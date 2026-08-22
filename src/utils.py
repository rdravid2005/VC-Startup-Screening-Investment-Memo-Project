"""Shared formatting, parsing, and missing-value utilities."""

from __future__ import annotations

import math
from typing import Any, Optional


def is_missing(value: Any) -> bool:
    """Return whether a value should be treated as missing.

    Zero and ``False`` are valid values. Empty strings, common CSV null tokens,
    ``None``, and NaN-like values are missing.
    """
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "n/a", "na", "none", "null", "nan"}
    try:
        return bool(math.isnan(value))
    except (TypeError, ValueError):
        return False


def optional_float(value: Any) -> Optional[float]:
    """Convert a value to float, returning ``None`` when it is missing."""
    if is_missing(value):
        return None
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Expected a number, received {value!r}.") from exc


def optional_int(value: Any) -> Optional[int]:
    """Convert a value to a non-rounded integer, or return ``None``."""
    number = optional_float(value)
    if number is None:
        return None
    if not number.is_integer():
        raise ValueError(f"Expected a whole number, received {value!r}.")
    return int(number)


def clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    """Clamp a numeric value to an inclusive range."""
    return max(lower, min(upper, value))


def safe_divide(numerator: Any, denominator: Any) -> Optional[float]:
    """Divide two values safely, returning ``None`` for missing/zero inputs."""
    top = optional_float(numerator)
    bottom = optional_float(denominator)
    if top is None or bottom in (None, 0):
        return None
    return top / bottom


def format_currency(value: Any, compact: bool = True) -> str:
    """Format an optional dollar value for dashboard display."""
    number = optional_float(value)
    if number is None:
        return "Not provided"
    sign = "-" if number < 0 else ""
    absolute = abs(number)
    if compact and absolute >= 1_000_000_000:
        return f"{sign}${absolute / 1_000_000_000:.1f}B"
    if compact and absolute >= 1_000_000:
        return f"{sign}${absolute / 1_000_000:.1f}M"
    if compact and absolute >= 1_000:
        return f"{sign}${absolute / 1_000:.1f}K"
    return f"{sign}${absolute:,.0f}"


def format_percentage(value: Any, decimals: int = 0) -> str:
    """Format a percentage stored as percentage points (for example, 72)."""
    number = optional_float(value)
    return "Not provided" if number is None else f"{number:.{decimals}f}%"


def format_number(value: Any) -> str:
    """Format an optional count."""
    number = optional_float(value)
    return "Not provided" if number is None else f"{number:,.0f}"


def score_label(score: float) -> str:
    """Return the educational label associated with a 0–100 score."""
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Promising"
    if score >= 40:
        return "Needs diligence"
    if score >= 20:
        return "Weak / high risk"
    return "Critical concern"
