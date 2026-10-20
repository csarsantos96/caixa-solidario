"""Read explicit mass labels; volume (ml/l) is never converted to mass."""
import re
from decimal import Decimal


def weight_from_name(name: str) -> int | None:
    match = re.search(r'(?<![\w.,])(\d+(?:[.,]\d+)?)\s*(kg|g)\b', name, re.IGNORECASE)
    if not match:
        return None
    grams = Decimal(match[1].replace(',', '.')) * (1000 if match[2].lower() == 'kg' else 1)
    return int(grams) if grams == grams.to_integral_value() and grams > 0 else None
