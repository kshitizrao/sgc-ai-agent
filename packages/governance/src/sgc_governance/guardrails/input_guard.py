import re

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"you\s+are\s+now\s+",
    r"system\s+prompt",
    r"jailbreak",
    r"<\s*script",
]

PROFANITY_PATTERNS = [
    r"\b(damn|hell)\b",
]


def check_input(text: str) -> tuple[bool, str | None]:
    lowered = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lowered):
            return False, "Potential prompt injection detected"
    return True, None


def check_output_tone(text: str, blocklist: list[str]) -> tuple[bool, str | None]:
    lowered = text.lower()
    for word in blocklist:
        if word in lowered:
            return False, f"Blocked tone violation: {word}"
    return True, None
