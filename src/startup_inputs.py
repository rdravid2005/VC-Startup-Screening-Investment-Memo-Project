"""Startup input collection, normalization, validation, and sample loading."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

import pandas as pd

from src.utils import is_missing, optional_float, optional_int


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DATA_PATH = PROJECT_ROOT / "sample_data" / "sample_startups.csv"
CSV_TEMPLATE_PATH = PROJECT_ROOT / "sample_data" / "upload_template.csv"
CSV_DICTIONARY_PATH = PROJECT_ROOT / "sample_data" / "CSV_DATA_DICTIONARY.md"

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

CSV_FIELD_DEFINITIONS = (
    ("startup_name", "Required", "Text", "Company name"),
    ("product_description", "Required", "Text", "What the product does"),
    ("target_customer", "Required", "Text", "Primary buyer or user"),
    ("industry", "Optional", "Text", "Sector or industry"),
    ("business_model", "Optional", "Text", "Commercial model"),
    ("problem_statement", "Optional", "Text", "Customer problem and current pain"),
    ("geography", "Optional", "Text", "Primary operating market"),
    ("stage", "Optional", "Text", "Pre-seed through Growth"),
    ("revenue_model", "Optional", "Text", "How the company charges"),
    ("estimated_market_size", "Optional", "USD number", "Addressable market without $ or commas"),
    ("market_growth_rate", "Optional", "Percentage", "Enter 12 for 12%"),
    ("market_notes", "Optional", "Text", "Source or calculation context"),
    ("current_arr", "Optional", "USD number", "ARR or annualized revenue"),
    ("revenue_growth_rate", "Optional", "Percentage", "Enter 65 for 65%"),
    ("gross_margin", "Optional", "Percentage", "Enter 78 for 78%"),
    ("monthly_burn_rate", "Optional", "USD number", "Monthly net cash burn"),
    ("runway_months", "Optional", "Number", "Months of cash runway"),
    ("customer_count", "Optional", "Whole number", "Paying customers"),
    ("cac", "Optional", "USD number", "Customer acquisition cost"),
    ("ltv", "Optional", "USD number", "Customer lifetime value"),
    ("retention_rate", "Optional", "Percentage", "Annual customer retention"),
    ("funding_raised", "Optional", "USD number", "Total capital raised"),
    ("valuation", "Optional", "USD number", "Latest valuation"),
    ("competitors", "Optional", "Text", "Direct and indirect alternatives"),
    ("differentiation", "Optional", "Text", "Why customers choose the company"),
    ("founder_notes", "Optional", "Text", "Relevant experience and team gaps"),
    ("risk_notes", "Optional", "Text", "Known material risks"),
)


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


def _number_text(value: Any) -> str:
    """Format an optional number for an editable text input."""
    if value is None:
        return ""
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def startup_widget_state(profile: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the keyed Streamlit widget state for a normalized profile."""
    startup = normalize_startup_data(profile)
    state = {f"profile_{field}": startup[field] for field in TEXT_FIELDS}
    state.update({f"profile_{field}": _number_text(startup[field]) for field in FLOAT_FIELDS + INTEGER_FIELDS})
    return state


def _select_index(options: Tuple[str, ...], value: str, fallback: int) -> int:
    return options.index(value) if value in options else fallback


def _options_with_value(options: Tuple[str, ...], value: str) -> Tuple[str, ...]:
    return options if value in options else options + (value,)


def render_startup_input_form(initial: Optional[Mapping[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Render a grouped, blank-friendly form and return valid submitted data."""
    import streamlit as st

    startup = normalize_startup_data(initial or DEFAULT_STARTUP)
    with st.form("startup_profile_form"):
        st.caption("Required fields are marked with *. Leave unknown metrics blank—missing evidence is handled explicitly in the scorecard.")
        st.markdown('<div class="form-section-title"><span>01</span> Company thesis</div>', unsafe_allow_html=True)
        company_left, company_right = st.columns(2)
        with company_left:
            startup_name = st.text_input("Startup name *", value=startup["startup_name"], placeholder="e.g. AtlasGrid", key="profile_startup_name")
            industries = _options_with_value(("Enterprise Software", "Fintech", "Healthcare", "Climate Tech", "Consumer", "Marketplace", "Developer Tools", "Other"), startup["industry"])
            industry = st.selectbox("Industry / sector", industries, index=_select_index(industries, startup["industry"], 0), key="profile_industry")
            stages = _options_with_value(("Pre-seed", "Seed", "Series A", "Series B", "Growth"), startup["stage"])
            stage = st.selectbox("Stage", stages, index=_select_index(stages, startup["stage"], 1), key="profile_stage")
            geography = st.text_input("Primary geography", value=startup["geography"], placeholder="e.g. United States", key="profile_geography")
        with company_right:
            models = _options_with_value(("B2B SaaS", "B2C Subscription", "Marketplace", "Usage-based", "Transaction fee", "Hardware + software", "Other"), startup["business_model"])
            business_model = st.selectbox("Business model", models, index=_select_index(models, startup["business_model"], 0), key="profile_business_model")
            revenue_model = st.text_input("Revenue model", value=startup["revenue_model"], placeholder="e.g. Annual subscription", key="profile_revenue_model")
            target_customer = st.text_input("Target customer *", value=startup["target_customer"], placeholder="e.g. Multi-site industrial operators", key="profile_target_customer")
        problem_statement = st.text_area("Problem being solved", value=startup["problem_statement"], placeholder="What is painful, expensive, or inefficient today?", key="profile_problem_statement")
        product_description = st.text_area("Product description *", value=startup["product_description"], placeholder="Describe the product in plain language.", key="profile_product_description")

        st.markdown('<div class="form-section-title"><span>02</span> Market and positioning</div>', unsafe_allow_html=True)
        market_left, market_right = st.columns(2)
        with market_left:
            estimated_market_size = st.text_input("Addressable market · USD", value=_number_text(startup["estimated_market_size"]), placeholder="e.g. 5000000000", help="Digits only; leave blank if unknown.", key="profile_estimated_market_size")
            market_growth_rate = st.text_input("Annual market growth · %", value=_number_text(startup["market_growth_rate"]), placeholder="e.g. 12", help="Enter 12 for 12%; leave blank if unknown.", key="profile_market_growth_rate")
            market_notes = st.text_area("Market evidence", value=startup["market_notes"], placeholder="Record the source, bottom-up calculation, or key assumptions.", key="profile_market_notes")
        with market_right:
            competitors = st.text_area("Competitive set", value=startup["competitors"], placeholder="Direct competitors; internal tools; doing nothing", key="profile_competitors")
            differentiation = st.text_area("Differentiation thesis", value=startup["differentiation"], placeholder="Why do customers choose this company?", key="profile_differentiation")

        st.markdown('<div class="form-section-title"><span>03</span> Traction and unit economics</div>', unsafe_allow_html=True)
        traction_columns = st.columns(4)
        traction_fields = (
            ("current_arr", "ARR / revenue · USD", "e.g. 750000"),
            ("revenue_growth_rate", "Annual growth · %", "e.g. 65"),
            ("customer_count", "Paying customers", "e.g. 30"),
            ("gross_margin", "Gross margin · %", "e.g. 78"),
            ("cac", "CAC · USD", "e.g. 12000"),
            ("ltv", "LTV · USD", "e.g. 48000"),
            ("retention_rate", "Annual retention · %", "e.g. 90"),
        )
        numeric_widgets: Dict[str, str] = {}
        for position, (field, label, placeholder) in enumerate(traction_fields):
            with traction_columns[position % 4]:
                numeric_widgets[field] = st.text_input(label, value=_number_text(startup[field]), placeholder=placeholder, key=f"profile_{field}")

        st.markdown('<div class="form-section-title"><span>04</span> Financial position</div>', unsafe_allow_html=True)
        finance_columns = st.columns(4)
        finance_fields = (
            ("monthly_burn_rate", "Monthly burn · USD", "e.g. 150000"),
            ("runway_months", "Runway · months", "e.g. 16"),
            ("funding_raised", "Funding raised · USD", "e.g. 2500000"),
            ("valuation", "Latest valuation · USD", "e.g. 12000000"),
        )
        for position, (field, label, placeholder) in enumerate(finance_fields):
            with finance_columns[position]:
                numeric_widgets[field] = st.text_input(label, value=_number_text(startup[field]), placeholder=placeholder, key=f"profile_{field}")

        st.markdown('<div class="form-section-title"><span>05</span> Team and known risks</div>', unsafe_allow_html=True)
        team_left, team_right = st.columns(2)
        with team_left:
            founder_notes = st.text_area("Founder / team evidence", value=startup["founder_notes"], placeholder="Relevant operating history, role coverage, and hiring gaps", key="profile_founder_notes")
        with team_right:
            risk_notes = st.text_area("Known risks", value=startup["risk_notes"], placeholder="Commercial, technical, regulatory, team, or financing concerns", key="profile_risk_notes")
        submitted = st.form_submit_button("Save profile and calculate score", type="primary", width="stretch")
    if not submitted:
        return None

    raw: Dict[str, Any] = {
        "startup_name": startup_name, "industry": industry,
        "business_model": business_model, "problem_statement": problem_statement,
        "product_description": product_description, "target_customer": target_customer,
        "geography": geography, "stage": stage, "revenue_model": revenue_model,
        "estimated_market_size": estimated_market_size,
        "market_growth_rate": market_growth_rate,
        "market_notes": market_notes, "competitors": competitors,
        "differentiation": differentiation, "founder_notes": founder_notes,
        "risk_notes": risk_notes,
    }
    raw.update(numeric_widgets)
    try:
        profile = normalize_startup_data(raw)
    except ValueError as exc:
        st.error(f"Check the numeric fields: {exc}")
        return None
    errors, warnings = validate_startup_data(profile)
    if errors:
        for error in errors:
            st.error(error)
        return None
    for warning in warnings:
        st.warning(warning)
    return profile
