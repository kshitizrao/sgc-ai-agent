from dataclasses import dataclass


@dataclass
class TriageResult:
    symptom_id: str | None
    severity_level: str
    required_action: str
    safety_prompt: str
    confidence: float
    requires_human_review: bool
    clarifying_question: str | None = None


class TriageEngine:
    """Rule-based emergency triage — fast, deterministic dispatch decisions."""

    HIGH_SEVERITY_KEYWORDS = {"smoke", "fire", "accident", "crashed", "brakes failed", "highway"}
    TOW_KEYWORDS = {"accident", "crashed", "radiator", "transmission", "won't start", "engine seized", "hit", "divider"}
    MECHANIC_KEYWORDS = {"puncture", "flat tyre", "battery dead", "jump start", "wiper"}

    def triage(self, reported_issue: str, rules: list[dict]) -> TriageResult:
        issue_lower = reported_issue.lower()
        best_match: dict | None = None
        best_score = 0.0

        for rule in rules:
            tags = rule.get("symptom_tags", [])
            score = sum(1 for tag in tags if tag.lower() in issue_lower)
            if score > best_score:
                best_score = score
                best_match = rule

        confidence = min(best_score / 3.0, 1.0) if best_match else 0.0

        if any(kw in issue_lower for kw in self.HIGH_SEVERITY_KEYWORDS):
            severity = "High"
            requires_review = True
        elif best_match:
            severity = best_match.get("severity_level", "Medium")
            requires_review = severity == "High"
        else:
            severity = "Medium"
            requires_review = False

        if best_match and confidence >= 0.33:
            return TriageResult(
                symptom_id=best_match.get("symptom_id"),
                severity_level=severity,
                required_action=best_match.get("required_action", "Phone_Support"),
                safety_prompt=best_match.get("safety_prompt", "Please stay safe and pull over if needed."),
                confidence=confidence,
                requires_human_review=requires_review,
            )

        if any(kw in issue_lower for kw in self.TOW_KEYWORDS):
            return TriageResult(
                symptom_id=None,
                severity_level=severity,
                required_action="Tow_Truck",
                safety_prompt="Please turn on hazard lights and move to a safe location.",
                confidence=0.5,
                requires_human_review=True,
            )

        if any(kw in issue_lower for kw in self.MECHANIC_KEYWORDS):
            return TriageResult(
                symptom_id=None,
                severity_level=severity,
                required_action="Mobile_Mechanic",
                safety_prompt="Stay with your vehicle in a safe spot.",
                confidence=0.5,
                requires_human_review=False,
            )

        return TriageResult(
            symptom_id=None,
            severity_level=severity,
            required_action="Phone_Support",
            safety_prompt="Please describe your issue in more detail.",
            confidence=0.0,
            requires_human_review=requires_review,
            clarifying_question="Can you tell me more about what happened? Is the car in a safe location?",
        )
