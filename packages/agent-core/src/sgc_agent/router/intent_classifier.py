from sgc_shared.constants import IntentType

INTENT_KEYWORDS: dict[IntentType, list[str]] = {
    IntentType.PARTS: ["part", "spare", "brake pad", "filter", "oem", "stock", "available"],
    IntentType.SERVICES_PRICING: ["service", "cost", "price", "basic", "standard", "comprehensive", "package"],
    IntentType.QUICK_SERVICE: ["express", "quick", "15 minute", "wash", "wiper", "top-up", "top up"],
    IntentType.CLAIMS: ["insurance", "claim", "surveyor", "liability", "deductible", "depreciation"],
    IntentType.RSA: ["emergency", "breakdown", "stranded", "tow", "flat tyre", "puncture", "won't start"],
    IntentType.GARAGE_MATCH: ["garage", "workshop", "near me", "recommend", "pickup", "best garage"],
    IntentType.DIAGNOSTICS: ["vibrat", "noise", "smoke", "problem", "issue", "symptom", "diagnos", "sluggish"],
    IntentType.GENERAL_FAQ: ["hello", "hi", "help", "thank"],
    IntentType.VEHICLE_INFO: ["car", "vehicle", "reg no", "registration", "details"],
}


def classify_intent(message: str) -> IntentType:
    lowered = message.lower()
    scores: dict[IntentType, int] = {intent: 0 for intent in IntentType}

    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in lowered:
                scores[intent] += 1

    best = max(scores, key=lambda k: scores[k])
    if scores[best] == 0:
        return IntentType.GENERAL_FAQ
    return best
