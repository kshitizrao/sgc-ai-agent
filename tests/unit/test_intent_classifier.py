from sgc_agent.router.intent_classifier import classify_intent
from sgc_shared.constants import IntentType


def test_classify_parts_intent():
    assert classify_intent("Do you have brake pads for Swift?") == IntentType.PARTS


def test_classify_service_intent():
    assert classify_intent("What is the cost of standard service?") == IntentType.SERVICES_PRICING


def test_classify_rsa_intent():
    assert classify_intent("I'm stranded with a flat tyre emergency") == IntentType.RSA


def test_classify_claims_intent():
    assert classify_intent("Why is my insurance claim liability so high?") == IntentType.CLAIMS


def test_classify_garage_intent():
    assert classify_intent("Recommend a garage near me with pickup") == IntentType.GARAGE_MATCH


def test_classify_diagnostics_intent():
    assert classify_intent("My car is vibrating at high speed") == IntentType.DIAGNOSTICS
