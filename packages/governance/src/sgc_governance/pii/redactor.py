import re

PHONE_PATTERN = re.compile(r"\b(\+91[\s-]?)?[6-9]\d{9}\b")
AADHAAR_PATTERN = re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b")
POLICY_PATTERN = re.compile(r"\b(POL|POLICY)[\s-]?\d{6,12}\b", re.IGNORECASE)


def redact_pii(text: str) -> str:
    text = PHONE_PATTERN.sub("[PHONE_REDACTED]", text)
    text = AADHAAR_PATTERN.sub("[AADHAAR_REDACTED]", text)
    text = POLICY_PATTERN.sub("[POLICY_REDACTED]", text)
    return text
