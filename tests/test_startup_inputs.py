"""Tests for startup profile normalization and CSV handling."""

from io import StringIO

import pytest

from src.startup_inputs import (
    blank_startup,
    load_sample_startups,
    load_startup_csv,
    normalize_startup_data,
    validate_startup_data,
)


def test_blank_startup_returns_independent_profiles():
    first = blank_startup()
    second = blank_startup()
    first["startup_name"] = "Changed"
    assert second["startup_name"] == ""


def test_normalization_preserves_missing_numbers_and_parses_formatting():
    profile = normalize_startup_data(
        {
            "startup_name": "  Demo Co  ",
            "product_description": "Product",
            "target_customer": "Teams",
            "current_arr": "$1,250,000",
            "gross_margin": "72%",
            "cac": "",
            "customer_count": "14",
        }
    )
    assert profile["startup_name"] == "Demo Co"
    assert profile["current_arr"] == 1_250_000
    assert profile["gross_margin"] == 72
    assert profile["cac"] is None
    assert profile["customer_count"] == 14


def test_validation_separates_errors_from_missing_evidence_warnings():
    profile = blank_startup()
    profile["gross_margin"] = 120
    errors, warnings = validate_startup_data(profile)
    assert "Startup name is required." in errors
    assert "Gross margin must be between 0% and 100%." in errors
    assert "ARR / revenue was not provided." in warnings


def test_bundled_samples_are_valid_and_fictional():
    profiles = load_sample_startups()
    assert len(profiles) == 4
    for profile in profiles:
        errors, _ = validate_startup_data(profile)
        assert errors == []
        assert profile["startup_name"]


def test_uploaded_csv_requires_core_columns():
    with pytest.raises(ValueError, match="target_customer"):
        load_startup_csv(StringIO("startup_name,product_description\nDemo,Product\n"))


def test_uploaded_csv_reports_invalid_rows():
    csv = StringIO(
        "startup_name,product_description,target_customer,gross_margin\n"
        "Demo,Product,Teams,150\n"
    )
    with pytest.raises(ValueError, match="Row 2"):
        load_startup_csv(csv)
