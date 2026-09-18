"""LLM-based intent classifier with Hinglish / Hindi / English support.

The classifier uses gpt-4o-mini for accurate multilingual intent detection.
Falls back to keyword-based classification if the LLM call fails.
"""

from __future__ import annotations

import logging
import time

from sgc_shared.constants import IntentType

logger = logging.getLogger("agent.intent")

# ═══════════════════════════════════════════════════════════════════════════
# Keyword-based fallback (kept from original implementation)
# ═══════════════════════════════════════════════════════════════════════════

INTENT_KEYWORDS: dict[IntentType, list[str]] = {
    IntentType.SERVICE_BOOKING: [
        "book", "booking karna", "service book", "service karwani", "service chahiye",
        "appointment", "garage mein", "schedule karo", "book karo", "book a service",
        "appoint", "book car", "book bike", "service lena", "slot lena",
        "gaadi service", "gadi service",
    ],
    IntentType.PIKPART_QUERY: [
        "booking", "customer", "vehicle", "service", "brand", "price", "kitna",
        "status", "history", "gaadi", "gadi", "bike", "scooty", "centre",
        "pichli", "agla", "show", "dikhao", "batao", "check", "find",
        "phone", "number", "registration", "kab", "kaha", "kaun",
        "konsi", "list", "search", "meri", "mera",
    ],
    IntentType.PARTS: ["part", "spare", "brake pad", "filter", "oem", "stock", "available"],

    IntentType.CLAIMS: [
        "insurance", "claim", "surveyor", "liability", "deductible",
        "depreciation", "bima",
    ],
    IntentType.RSA: [
        "emergency", "breakdown", "stranded", "tow", "flat tyre", "puncture",
        "won't start", "kharab", "band", "ruk gayi",
    ],
    IntentType.GARAGE_MATCH: [
        "garage", "workshop", "near me", "recommend", "best garage",
        "paas", "nazdeek",
    ],
    IntentType.DIAGNOSTICS: [
        "vibrat", "noise", "smoke", "problem", "issue", "symptom",
        "diagnos", "sluggish", "awaaz", "dhuan",
    ],
    IntentType.VEHICLE_INFO: ["reg no", "registration", "details", "vehicle number"],
    IntentType.GENERAL_FAQ: [
        "hello", "hi", "namaste", "help", "thank", "shukriya", "dhanyavad",
        "kaise ho", "good morning", "bye",
    ],
}

# Valid intent names for parsing LLM output
_VALID_INTENTS = {intent.value: intent for intent in IntentType}


def classify_intent_keywords(message: str) -> IntentType:
    """Keyword-based intent classification (fallback)."""
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


async def classify_intent_llm(
    message: str,
    llm_router,
) -> IntentType:
    """LLM-based intent classification using gpt-4o-mini.

    Parameters
    ----------
    message:
        The customer's message (Hindi / Hinglish / English).
    llm_router:
        An instance of ``ModelRouter`` to make the LLM call.

    Returns
    -------
    IntentType
        The classified intent.
    """
    from sgc_agent.persona.system_prompts import INTENT_CLASSIFIER_PROMPT
    from sgc_shared.constants import TaskType

    start = time.perf_counter()

    messages = [
        {"role": "system", "content": INTENT_CLASSIFIER_PROMPT},
        {"role": "user", "content": message},
    ]

    try:
        response = await llm_router.complete(messages, task=TaskType.CLASSIFY)
        raw = response.content.strip().lower().replace('"', "").replace("'", "")

        # Parse the intent name
        intent = _VALID_INTENTS.get(raw)
        if intent is None:
            # Try partial match
            for key, val in _VALID_INTENTS.items():
                if key in raw:
                    intent = val
                    break

        elapsed = round((time.perf_counter() - start) * 1000, 2)

        if intent:
            logger.info(
                "LLM intent classified",
                extra={
                    "intent": intent.value,
                    "message_preview": message[:80],
                    "model": response.model,
                    "duration_ms": elapsed,
                },
            )
            return intent
        else:
            logger.warning(
                "LLM returned unparseable intent, falling back to keywords",
                extra={"raw_response": raw, "duration_ms": elapsed},
            )
            return classify_intent_keywords(message)

    except Exception as e:
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        logger.warning(
            "LLM intent classification failed, falling back to keywords",
            extra={"error": str(e), "duration_ms": elapsed},
        )
        return classify_intent_keywords(message)


def classify_intent(message: str) -> IntentType:
    """Synchronous keyword-based classifier (backward compatibility).

    For async LLM-based classification, use ``classify_intent_llm`` instead.
    """
    return classify_intent_keywords(message)
