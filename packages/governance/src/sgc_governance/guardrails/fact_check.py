import re
from decimal import Decimal


def extract_numbers(text: str) -> set[str]:
    # Extract only currency amounts (e.g. ₹ 500, Rs. 500) to prevent false positives on IDs/vehicle numbers.
    return set(re.findall(r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{2})?)", text, re.IGNORECASE))


def normalize_amount(value: str) -> str:
    cleaned = value.replace("₹", "").replace(",", "").strip()
    try:
        return str(Decimal(cleaned).quantize(Decimal("0.01")))
    except Exception:
        return cleaned


def fact_check_response(
    response: str,
    tool_amounts: list[float | Decimal | str],
) -> tuple[bool, str | None]:
    """Verify numeric claims in response match tool output amounts."""
    if not tool_amounts:
        return True, None

    response_numbers = {normalize_amount(n) for n in extract_numbers(response)}
    allowed = {normalize_amount(str(a)) for a in tool_amounts}

    for num in response_numbers:
        if num and num not in allowed and num not in {"0", "0.00"}:
            if any(abs(float(num) - float(a)) < 1.0 for a in allowed if a.replace(".", "").isdigit()):
                continue
            return False, f"Response contains unverified amount: {num}"
    return True, None
