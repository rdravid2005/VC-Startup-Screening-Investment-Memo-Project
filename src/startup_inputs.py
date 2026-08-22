"""Startup input collection, normalization, validation, and sample loading."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import pandas as pd

from src.utils import is_missing, optional_float, optional_int


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA_PATH = PROJECT_ROOT / "sample_data" / "sample_startups.csv"

TEXT_FIELDS = (
    "startup_name", "industry", "business_model", "problem_statement",
    "product_description", "target_customer", "geography", "stage",
    "revenue_model", "market_notes", "competitors", "differentiation",
    "founder_notes", "risk_notes",
)
FLOAT_FIELDS = (
    "estimated_market_size", "market_growth_rate", "current_arr",
    "revenue_growth_rate", "gross_margin", "monthly_burn_rate",
    "runway_months", "cac", "ltv", "retention_rate", "funding_raised",
    "valuation",
)
INTEGER_FIELDS = ("customer_count",)
PERCENTAGE_FIELDS = {
    "market_growth_rate": "Market growth rate",
    "revenue_growth_rate": "Revenue growth rate",
    "gross_margin": "Gross margin",
    "retention_rate": "Annual customer retention",
}
NON_NEGATIVE_FIELDS = {
    "estimated_market_size": "Estimated market size",
    "current_arr": "Current ARR / annual revenue",
    "monthly_burn_rate": "Monthly burn rate",
    "runway_months": "Runway", "cac": "Customer acquisition cost",
    "ltv": "Customer lifetime value", "funding_raised": "Funding raised",
    "valuation": "Valuation", "customer_count": "Customer count",
}

DEFAULT_STARTUP: Dict[str, Any] = {
    "startup_name": "", "industry": "Enterprise Software",
    "business_model": "B2B SaaS", "problem_statement": "",
    "product_description": "", "target_customer": "",
    "geography": "United States", "stage": "Seed",
    "revenue_model": "Subscription", "estimated_market_size": None,
    "market_growth_rate": None, "market_notes": "", "current_arr": None,
    "revenue_growth_rate": None, "gross_margin": None,
    "monthly_burn_rate": None, "runway_months": None,
    "customer_count": None, "cac": None, "ltv": None,
    "retention_rate": None, "funding_raised": None, "valuation": None,
    "competitors": "", "differentiation": "", "founder_notes": "",
    "risk_notes": "",
}


def blank_startup() -> Dict[str, Any]:
    """Return a fresh blank startup profile."""
    return deepcopy(DEFAULT_STARTUP)


def normalize_startup_data(raw: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalize a mapping into the application's canonical startup schema."""
    normalized = blank_startup()
    for field in TEXT_FIELDS:
        value = raw.get(field, normalized[field])
        normalized[field] = "" if is_missing(value) else str(value).strip()
    for field in FLOAT_FIELDS:
        normalized[field] = optional_float(raw.get(field))
    for field in INTEGER_FIELDS:
        normalized[field] = optional_int(raw.get(field))
    return normalized


def validate_startup_data(startup: Mapping[str, Any]) -> Tuple[List[str], List[str]]:
    """Return blocking errors and non-blocking diligence warnings."""
    errors: List[str] = []
    warnings: List[str] = []
    if is_missing(startup.get("startup_name")):
        errors.append("Startup name is required.")
    if is_missing(startup.get("product_description")):
        errors.append("Product description is required.")
    if is_missing(startup.get("target_customer")):
        errors.append("Target customer is required.")

    for field, label in NON_NEGATIVE_FIELDS.items():
        value = startup.get(field)
        if value is not None and value < 0:
            errors.append(f"{label} cannot be negative.")
    for field, label in PERCENTAGE_FIELDS.items():
        value = startup.get(field)
        if value is not None and not 0 <= value <= 100:
            errors.append(f"{label} must be between 0% and 100%.")

    valuation = startup.get("valuation")
    funding = startup.get("funding_raised")
    if valuation is not None and funding is not None and valuation < funding:
        warnings.append(
            "Valuation is below total funding raised; verify that both figures use a comparable basis."
        )

    evidence_checks = (
        ("estimated_market_size", "Market size was not provided."),
        ("current_arr", "ARR / revenue was not provided."),
        ("revenue_growth_rate", "Revenue growth was not provided."),
        ("gross_margin", "Gross margin was not provided."),
        ("runway_months", "Runway was not provided."),
        ("founder_notes", "Founder / team evidence was not provided."),
        ("differentiation", "Product differentiation was not described."),
    )
    for field, message in evidence_checks:
        if is_missing(startup.get(field)):
            warnings.append(message)
    return errors, warnings


def dataframe_to_profiles(dataframe: pd.DataFrame) -> List[Dict[str, Any]]:
    """Normalize all records from an uploaded or bundled CSV."""
    required = {"startup_name", "product_description", "target_customer"}
    missing_columns = sorted(required.difference(dataframe.columns))
    if missing_columns:
        raise ValueError("CSV is missing required columns: " + ", ".join(missing_columns))

    profiles: List[Dict[str, Any]] = []
    row_errors: List[str] = []
    for index, record in enumerate(dataframe.to_dict(orient="records"), start=2):
        try:
            profile = normalize_startup_data(record)
            errors, _ = validate_startup_data(profile)
            if errors:
                row_errors.append(f"Row {index}: {' '.join(errors)}")
            else:
                profiles.append(profile)
        except ValueError as exc:
            row_errors.append(f"Row {index}: {exc}")
    if row_errors:
        raise ValueError("\n".join(row_errors))
    if not profiles:
        raise ValueError("CSV does not contain any startup profiles.")
    return profiles


def load_startup_csv(source: Any) -> List[Dict[str, Any]]:
    """Load and normalize profiles from a file path or file-like object."""
    try:
        dataframe = pd.read_csv(source)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        raise ValueError(f"Could not read the CSV: {exc}") from exc
    return dataframe_to_profiles(dataframe)


def load_sample_startups(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load the bundled fictional startup profiles."""
    return load_startup_csv(path or SAMPLE_DATA_PATH)


def profile_options(profiles: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Index profiles by display name for a Streamlit select box."""
    return {str(profile["startup_name"]): dict(profile) for profile in profiles}


def _number_value(startup: Mapping[str, Any], field: str) -> float:
    value = startup.get(field)
    return 0.0 if value is None else float(value)


def _optional_widget_number(value: float, supplied: bool) -> Optional[float]:
    return float(value) if supplied else None


def _select_index(options: Tuple[str, ...], value: str, fallback: int) -> int:
    return options.index(value) if value in options else fallback


def render_startup_input_form(initial: Optional[Mapping[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Render the complete Streamlit input form and return valid submitted data."""
    import streamlit as st

    startup = normalize_startup_data(initial or DEFAULT_STARTUP)
    with st.form("startup_profile_form"):
        st.markdown("### Company and product")
        company_left, company_right = st.columns(2)
        with company_left:
            startup_name = st.text_input("Startup name *", value=startup["startup_name"])
            industries = ("Enterprise Software", "Fintech", "Healthcare", "Climate Tech", "Consumer", "Marketplace", "Developer Tools", "Other")
            industry = st.selectbox("Industry / sector", industries, index=_select_index(industries, startup["industry"], 7))
            stages = ("Pre-seed", "Seed", "Series A", "Series B", "Growth")
            stage = st.selectbox("Stage", stages, index=_select_index(stages, startup["stage"], 1))
            geography = st.text_input("Primary geography", value=startup["geography"])
        with company_right:
            models = ("B2B SaaS", "B2C Subscription", "Marketplace", "Usage-based", "Transaction fee", "Hardware + software", "Other")
            business_model = st.selectbox("Business model", models, index=_select_index(models, startup["business_model"], 6))
            revenue_model = st.text_input("Revenue model", value=startup["revenue_model"])
            target_customer = st.text_input("Target customer *", value=startup["target_customer"])
        problem_statement = st.text_area("Problem being solved", value=startup["problem_statement"])
        product_description = st.text_area("Product description *", value=startup["product_description"])

        st.markdown("### Market and positioning")
        market_left, market_right = st.columns(2)
        with market_left:
            estimated_market_size = st.number_input("Estimated addressable market ($)", min_value=0.0, value=_number_value(startup, "estimated_market_size"), step=1_000_000.0, key="input_estimated_market_size")
            market_size_supplied = st.checkbox("Use market-size value", value=startup["estimated_market_size"] is not None, key="supplied_estimated_market_size")
            market_growth_rate = st.number_input("Estimated annual market growth (%)", min_value=0.0, max_value=100.0, value=_number_value(startup, "market_growth_rate"), step=1.0, key="input_market_growth_rate")
            market_growth_supplied = st.checkbox("Use market-growth value", value=startup["market_growth_rate"] is not None, key="supplied_market_growth_rate")
        with market_right:
            market_notes = st.text_area("Market evidence / notes", value=startup["market_notes"])
            differentiation = st.text_area("Product differentiation", value=startup["differentiation"])
        competitors = st.text_area("Key competitors", value=startup["competitors"])

        st.markdown("### Traction and unit economics")
        traction_columns = st.columns(3)
        numeric_widgets: Dict[str, Tuple[float, bool]] = {}
        traction_fields = (
            ("current_arr", "Current ARR / annual revenue ($)", 10_000.0),
            ("revenue_growth_rate", "Annual revenue growth (%)", 1.0),
            ("customer_count", "Customer count", 1.0),
            ("gross_margin", "Gross margin (%)", 1.0),
            ("cac", "Customer acquisition cost ($)", 100.0),
            ("ltv", "Customer lifetime value ($)", 100.0),
            ("retention_rate", "Annual customer retention (%)", 1.0),
        )
        for position, (field, label, step) in enumerate(traction_fields):
            with traction_columns[position % 3]:
                value = st.number_input(label, min_value=0.0, max_value=100.0 if field in PERCENTAGE_FIELDS else None, value=_number_value(startup, field), step=step, key=f"input_{field}")
                supplied = st.checkbox(f"Use {label.lower()}", value=startup[field] is not None, key=f"supplied_{field}")
                numeric_widgets[field] = (value, supplied)

        st.markdown("### Financial position")
        finance_columns = st.columns(3)
        finance_fields = (
            ("monthly_burn_rate", "Monthly burn rate ($)", 10_000.0),
            ("runway_months", "Runway (months)", 1.0),
            ("funding_raised", "Funding raised ($)", 100_000.0),
            ("valuation", "Latest valuation ($)", 1_000_000.0),
        )
        for position, (field, label, step) in enumerate(finance_fields):
            with finance_columns[position % 3]:
                value = st.number_input(label, min_value=0.0, value=_number_value(startup, field), step=step, key=f"input_{field}")
                supplied = st.checkbox(f"Use {label.lower()}", value=startup[field] is not None, key=f"supplied_{field}")
                numeric_widgets[field] = (value, supplied)

        st.markdown("### Team and risks")
        founder_notes = st.text_area("Founder / team notes", value=startup["founder_notes"])
        risk_notes = st.text_area("Known risks", value=startup["risk_notes"])
        submitted = st.form_submit_button("Analyze startup", type="primary", use_container_width=True)
    if not submitted:
        return None

    raw: Dict[str, Any] = {
        "startup_name": startup_name, "industry": industry,
        "business_model": business_model, "problem_statement": problem_statement,
        "product_description": product_description, "target_customer": target_customer,
        "geography": geography, "stage": stage, "revenue_model": revenue_model,
        "estimated_market_size": _optional_widget_number(estimated_market_size, market_size_supplied),
        "market_growth_rate": _optional_widget_number(market_growth_rate, market_growth_supplied),
        "market_notes": market_notes, "competitors": competitors,
        "differentiation": differentiation, "founder_notes": founder_notes,
        "risk_notes": risk_notes,
    }
    raw.update({field: _optional_widget_number(value, supplied) for field, (value, supplied) in numeric_widgets.items()})
    profile = normalize_startup_data(raw)
    errors, warnings = validate_startup_data(profile)
    if errors:
        for error in errors:
            st.error(error)
        return None
    for warning in warnings:
        st.warning(warning)
    return profile
