from sqlalchemy import select

from sgc_db.models.diagnostics import PredictiveFailureMatrix, SymptomMapping, VehicleIssue
from sgc_shared.types import SourceRef, ToolResult
from sgc_tools.registry import BaseTool

CONFIDENCE_THRESHOLD = 0.33


class DiagnoseSymptomTool(BaseTool):
    name = "diagnose_symptom"
    description = "Match customer symptoms to likely vehicle issues"

    async def execute(
        self,
        session,
        symptom_text,
        vehicle_make=None,
        vehicle_model=None,
        fuel_type=None,
        mileage_km=None,
        **kwargs,
    ):
        sym_result = await session.execute(select(SymptomMapping))
        mappings = list(sym_result.scalars().all())

        matched_issues: list[dict] = []
        clarifying_question = None

        for mapping in mappings:
            keywords = mapping.customer_keywords or []
            score = sum(1 for kw in keywords if kw.lower() in symptom_text.lower())
            if score > 0:
                issue_result = await session.execute(
                    select(VehicleIssue).where(VehicleIssue.issue_id == mapping.issue_id)
                )
                issue = issue_result.scalar_one_or_none()
                if issue:
                    confidence = min(score / 3.0, 1.0)
                    if confidence < CONFIDENCE_THRESHOLD:
                        clarifying_question = mapping.ai_diagnostic_question
                        continue
                    matched_issues.append({
                        "issue_id": issue.issue_id,
                        "issue_name": issue.issue_name,
                        "severity_level": issue.severity_level,
                        "is_safety_risk": issue.is_safety_risk,
                        "resolution_service_id": issue.resolution_service_id,
                        "confidence": confidence,
                    })

        if mileage_km and vehicle_make and vehicle_model:
            pred_result = await session.execute(
                select(PredictiveFailureMatrix).where(
                    PredictiveFailureMatrix.vehicle_make.ilike(f"%{vehicle_make}%"),
                    PredictiveFailureMatrix.vehicle_model.ilike(f"%{vehicle_model}%"),
                )
            )
            for pred in pred_result.scalars().all():
                if fuel_type and pred.fuel_type and pred.fuel_type != fuel_type:
                    continue
                if pred.risk_start_km and pred.risk_end_km:
                    if pred.risk_start_km <= mileage_km <= pred.risk_end_km:
                        issue_result = await session.execute(
                            select(VehicleIssue).where(VehicleIssue.issue_id == pred.issue_id)
                        )
                        issue = issue_result.scalar_one_or_none()
                        if issue:
                            matched_issues.append({
                                "issue_id": issue.issue_id,
                                "issue_name": issue.issue_name,
                                "severity_level": issue.severity_level,
                                "probability_score": pred.probability_score,
                                "confidence": 0.8,
                            })

        matched_issues.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        if not matched_issues and clarifying_question:
            return ToolResult(
                tool_name=self.name,
                success=True,
                data={"issues": [], "clarifying_question": clarifying_question},
            )

        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"issues": matched_issues[:5], "clarifying_question": clarifying_question},
            source_refs=[SourceRef(table="diagnostics.vehicle_issues", record_id=i["issue_id"]) for i in matched_issues[:5]],
        )


class GetPredictiveMaintenanceTool(BaseTool):
    name = "get_predictive_maintenance"
    description = "Get proactive maintenance warnings based on vehicle age and mileage"

    async def execute(self, session, vehicle_make, vehicle_model, fuel_type, mileage_km, age_months=None, **kwargs):
        result = await session.execute(
            select(PredictiveFailureMatrix).where(
                PredictiveFailureMatrix.vehicle_make.ilike(f"%{vehicle_make}%"),
                PredictiveFailureMatrix.vehicle_model.ilike(f"%{vehicle_model}%"),
            )
        )
        warnings = []
        for pred in result.scalars().all():
            if pred.fuel_type and pred.fuel_type != fuel_type:
                continue
            km_match = pred.risk_start_km and pred.risk_end_km and pred.risk_start_km <= mileage_km <= pred.risk_end_km
            age_match = age_months and pred.risk_start_age_months and age_months >= pred.risk_start_age_months
            if km_match or age_match:
                issue_result = await session.execute(
                    select(VehicleIssue).where(VehicleIssue.issue_id == pred.issue_id)
                )
                issue = issue_result.scalar_one_or_none()
                if issue:
                    warnings.append({
                        "issue_id": issue.issue_id,
                        "issue_name": issue.issue_name,
                        "probability_score": pred.probability_score,
                        "severity_level": issue.severity_level,
                    })

        return ToolResult(
            tool_name=self.name,
            success=True,
            data=warnings,
            source_refs=[SourceRef(table="diagnostics.predictive_failure_matrix", record_id=w["issue_id"]) for w in warnings],
        )
