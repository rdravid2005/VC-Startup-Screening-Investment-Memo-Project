"""Shared formatting and missing-value utilities."""


def is_missing(value):
    """Return whether a value should be treated as missing."""
    return value is None or value == ""

