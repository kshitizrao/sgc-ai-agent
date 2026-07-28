from decimal import Decimal

from sqlalchemy import select

from sgc_db.models.operations import Claim, ClaimLineItem, PolicyRule
from sgc_domain.claim_liability_engine import ClaimLiabilityEngine
from sgc_shared.types import SourceRef, ToolResult
from sgc_tools.registry import BaseTool


class GetClaimStatusTool(BaseTool):
    name = "get_claim_status"
    description = "Get insurance claim workflow status"

    async def execute(self, session, claim_id=None, vehicle_reg_no=None, **kwargs):
        stmt = select(Claim)
        if claim_id:
            stmt = stmt.where(Claim.claim_id == claim_id)
        elif vehicle_reg_no:
            stmt = stmt.where(Claim.vehicle_reg_no == vehicle_reg_no)
        result = await session.execute(stmt)
        claim = result.scalar_one_or_none()
        if not claim:
            return ToolResult(tool_name=self.name, success=False, error="Claim not found")

        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "claim_id": claim.claim_id,
                "vehicle_reg_no": claim.vehicle_reg_no,
                "insurance_provider": claim.insurance_provider,
                "claim_type": claim.claim_type,
                "claim_status": claim.claim_status,
                "surveyor_name": claim.surveyor_name,
            },
            source_refs=[SourceRef(table="operations.claims", record_id=claim.claim_id)],
        )


class ExplainClaimLiabilityTool(BaseTool):
    name = "explain_claim_liability"
    description = "Calculate and explain customer out-of-pocket insurance liability"

    async def execute(self, session, claim_id, **kwargs):
        claim_result = await session.execute(select(Claim).where(Claim.claim_id == claim_id))
        claim = claim_result.scalar_one_or_none()
        if not claim:
            return ToolResult(tool_name=self.name, success=False, error="Claim not found")

        policy_result = await session.execute(
            select(PolicyRule).where(PolicyRule.vehicle_reg_no == claim.vehicle_reg_no)
        )
        policy = policy_result.scalar_one_or_none()
        if not policy:
            return ToolResult(tool_name=self.name, success=False, error="Policy not found")

        lines_result = await session.execute(
            select(ClaimLineItem).where(ClaimLineItem.claim_id == claim_id)
        )
        line_items = [
            {
                "part_id": li.part_id,
                "part_material": li.part_material,
                "garage_est_amount": float(li.garage_est_amount or 0),
                "surveyor_apprv_amount": float(li.surveyor_apprv_amount or 0),
                "surveyor_action": li.surveyor_action,
                "customer_liability": float(li.customer_liability or 0),
            }
            for li in lines_result.scalars().all()
        ]

        engine = ClaimLiabilityEngine()
        breakdown = engine.calculate(
            policy_type=policy.policy_type or "Comprehensive",
            compulsory_deductible=Decimal(str(policy.compulsory_deductible or 1000)),
            consumables_cover=bool(policy.consumables_cover_addon),
            line_items=line_items,
        )

        return ToolResult(
            tool_name=self.name,
            success=True,
            data={
                "claim_id": claim_id,
                "policy_type": policy.policy_type,
                "total_liability": float(breakdown.total_liability),
                "deductible": float(breakdown.deductible),
                "depreciation_deductions": float(breakdown.depreciation_deductions),
                "consumables_out_of_pocket": float(breakdown.consumables_out_of_pocket),
                "explanation": breakdown.explanation_parts,
                "line_items": breakdown.line_items,
            },
            source_refs=[
                SourceRef(table="operations.claims", record_id=claim_id),
                SourceRef(table="operations.policy_rules", record_id=policy.policy_id),
            ],
        )
