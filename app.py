"""Streamlit entry point for the AI Venture Capital Investment Screener."""

from __future__ import annotations

from html import escape
from pathlib import Path
import re
from typing import Any, Mapping, Optional

import pandas as pd
import streamlit as st

from src.memo_generator import build_fallback_memo, build_memo_payload, generate_investment_memo, has_api_key
from src.scoring_model import CATEGORY_WEIGHTS, score_startup
from src.startup_inputs import (
    CSV_FIELD_DEFINITIONS,
    CSV_TEMPLATE_PATH,
    blank_startup,
    load_sample_startups,
    load_startup_csv,
    profile_options,
    render_startup_input_form,
    startup_widget_state,
)
from src.utils import format_currency, format_number, format_percentage, safe_divide
from src.visualizations import build_risk_summary_chart, build_score_profile_chart, build_weighted_contribution_chart


PROJECT_ROOT = Path(__file__).resolve().parent
LOGO_PATH = PROJECT_ROOT / "assets" / "venturelens-mark.svg"
PAGES = ("Briefing", "Company Review", "IC Scorecard", "Memo Builder")

st.set_page_config(
    page_title="VentureLens · Investment Screening Desk",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)


GLOBAL_CSS = """
<style>
    :root {
        --paper: #f3f0e7;
        --surface: #fbfaf6;
        --ink: #17201b;
        --muted: #6d746e;
        --line: #d8d4c9;
        --rust: #b94732;
        --green: #236b53;
        --teal: #16796f;
        --teal-soft: rgba(22, 121, 111, .08);
    }
    .stApp {
        background-color: var(--paper);
        background-image:
            linear-gradient(rgba(23, 32, 27, .024) 1px, transparent 1px),
            linear-gradient(90deg, rgba(23, 32, 27, .024) 1px, transparent 1px);
        background-size: 32px 32px;
        color: var(--ink);
    }
    ::selection { background: rgba(22, 121, 111, .18); color: var(--ink); }
    [data-testid="stHeader"] { height: 0; background: transparent; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
    .block-container { max-width: 1210px; padding: 1.15rem 2rem 5rem; }
    h1, h2, h3 { color: var(--ink); letter-spacing: -.025em; }
    h1 { font-family: Georgia, 'Times New Roman', serif; font-weight: 500; }
    p, label, [data-testid="stCaptionContainer"] { color: var(--ink); }
    a { color: var(--ink); }
    hr { border-color: var(--line) !important; }
    .brand-copy { padding-top: .1rem; }
    .brand-name { font: 700 1.04rem/1 Arial, sans-serif; letter-spacing: -.02em; }
    .brand-sub { margin-top: .35rem; color: var(--muted); font: 600 .63rem/1 Arial, sans-serif; letter-spacing: .13em; text-transform: uppercase; }
    .system-status {
        display: flex; justify-content: space-between; gap: 1rem; align-items: center;
        border-top: 1px solid var(--ink); border-bottom: 1px solid var(--line);
        margin: .7rem 0 2.8rem; padding: .42rem 0;
        color: var(--muted); font: 650 .62rem/1.3 ui-monospace, SFMono-Regular, monospace;
        letter-spacing: .06em; text-transform: uppercase;
    }
    .system-status strong { color: var(--ink); font-weight: 750; }
    .status-dot { display: inline-block; width: 6px; height: 6px; margin-right: .45rem; border-radius: 50%; background: var(--teal); box-shadow: 0 0 0 3px var(--teal-soft); }
    .kicker { color: var(--rust); font: 700 .68rem/1 Arial, sans-serif; letter-spacing: .14em; text-transform: uppercase; margin-bottom: .9rem; }
    .kicker::before { content: ""; display: inline-block; width: 14px; height: 2px; background: var(--teal); margin: 0 .55rem .2rem 0; }
    .page-title { font: 500 clamp(2.5rem, 5vw, 4.8rem)/.98 Georgia, serif; letter-spacing: -.045em; max-width: 880px; margin-bottom: 1.05rem; }
    .page-copy { max-width: 750px; color: var(--muted); font-size: 1.03rem; line-height: 1.65; margin-bottom: 2.4rem; }
    .hero-title { font: 500 clamp(3.4rem, 7vw, 6.5rem)/.92 Georgia, serif; letter-spacing: -.055em; margin: .3rem 0 1.35rem; max-width: 900px; }
    .hero-copy { color: var(--muted); font-size: 1.12rem; line-height: 1.65; max-width: 710px; }
    .docket { border-top: 3px solid var(--ink); border-bottom: 1px solid var(--line); padding: 1.1rem .85rem 1.3rem; background: rgba(251,250,246,.58); box-shadow: inset 3px 0 0 var(--teal); }
    .docket-label { color: var(--muted); font: 700 .65rem/1 Arial, sans-serif; letter-spacing: .13em; text-transform: uppercase; }
    .docket-value { font: 500 1.65rem/1.2 Georgia, serif; margin: .8rem 0 .35rem; }
    .docket-meta { color: var(--muted); font-size: .8rem; }
    .section-rule { display: grid; grid-template-columns: 72px 1fr; gap: 1rem; border-top: 1px solid var(--line); padding: 1.15rem .65rem; transition: background .16s ease, transform .16s ease; }
    .section-rule:hover { background: rgba(251,250,246,.7); transform: translateX(3px); }
    .section-rule .num { color: var(--rust); font: 700 .68rem/1.3 ui-monospace, monospace; }
    .section-rule h3 { font: 500 1.32rem/1.2 Georgia, serif; margin: 0 0 .3rem; }
    .section-rule p { color: var(--muted); line-height: 1.5; margin: 0; }
    .process-line { display: grid; grid-template-columns: repeat(3, 1fr); border-top: 1px solid var(--ink); border-bottom: 1px solid var(--line); }
    .process-step { padding: 1.2rem 1.2rem 1.3rem 0; min-height: 140px; border-right: 1px solid var(--line); transition: background .16s ease; }
    .process-step:hover { background: var(--teal-soft); }
    .process-step + .process-step { padding-left: 1.2rem; }
    .process-step:last-child { border-right: 0; }
    .process-step span { color: var(--rust); font: 700 .65rem/1 ui-monospace, monospace; }
    .process-step strong { display: block; margin: 1rem 0 .45rem; font-family: Georgia, serif; font-size: 1.2rem; font-weight: 500; }
    .process-step p { color: var(--muted); font-size: .86rem; line-height: 1.45; }
    .form-section-title { border-top: 1px solid var(--ink); padding: 1.1rem 0 .75rem; margin-top: 2.2rem; font: 500 1.35rem/1 Georgia, serif; position: relative; }
    .form-section-title::after { content: ""; position: absolute; top: -1px; right: 0; width: 42px; height: 3px; background: var(--teal); }
    .form-section-title span { display: inline-block; min-width: 52px; color: var(--rust); font: 700 .68rem/1 ui-monospace, monospace; }
    .company-strip { border-top: 3px solid var(--ink); border-bottom: 1px solid var(--line); padding: 1rem 1rem 1.1rem; background: linear-gradient(90deg, rgba(22,121,111,.075), rgba(251,250,246,.5) 46%, transparent); }
    .company-name { font: 500 1.8rem/1.15 Georgia, serif; }
    .company-meta { color: var(--rust); font-size: .69rem; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; margin: .5rem 0 .7rem; }
    .company-desc { color: var(--muted); line-height: 1.55; max-width: 850px; }
    .score-hero { border-top: 3px solid var(--ink); border-bottom: 1px solid var(--line); padding: 1.25rem .75rem 1.45rem; background: rgba(251,250,246,.42); min-height: 142px; }
    .score-number { font: 500 5.3rem/.85 Georgia, serif; letter-spacing: -.065em; }
    .score-denominator { color: var(--muted); font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; }
    .score-call { font: 500 1.45rem/1.2 Georgia, serif; margin: .55rem 0; }
    .risk-chip { display: inline-block; padding: .28rem .52rem; border: 1px solid currentColor; border-radius: 2px; font-size: .68rem; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; }
    .risk-high, .risk-elevated { color: #a33f32; }
    .risk-moderate { color: #966314; }
    .risk-low { color: #236b53; }
    .risk-context { color: #536a76; }
    .risk-row { display: grid; grid-template-columns: 90px 140px 1fr; gap: 1rem; align-items: start; border-top: 1px solid var(--line); padding: .9rem 0; }
    .risk-row:last-child { border-bottom: 1px solid var(--line); }
    .risk-category { color: var(--muted); font-size: .75rem; padding-top: .25rem; }
    .risk-message { line-height: 1.48; }
    .question-row { display: grid; grid-template-columns: 54px 1fr; border-top: 1px solid var(--line); padding: .95rem 0; }
    .question-row:last-child { border-bottom: 1px solid var(--line); }
    .question-row span { color: var(--rust); font: 700 .7rem/1.5 ui-monospace, monospace; }
    .detail-label { color: var(--rust); font: 700 .64rem/1 Arial, sans-serif; letter-spacing: .11em; text-transform: uppercase; margin-bottom: .45rem; }
    .detail-copy { color: var(--ink); line-height: 1.55; margin-bottom: 1.35rem; }
    .source-panel { border: 1px solid var(--line); background: rgba(251,250,246,.72); padding: 1.1rem 1.2rem; box-shadow: inset 3px 0 0 var(--teal); }
    .fine-print { color: var(--muted); font-size: .76rem; line-height: 1.5; }
    .footer { border-top: 1px solid var(--line); margin-top: 4rem; padding-top: 1rem; color: var(--muted); font-size: .72rem; display: flex; justify-content: space-between; }
    [data-testid="stForm"] { border: 0; padding: 0; background: transparent; }
    [data-testid="stMetric"] { background: rgba(251,250,246,.36); border-top: 1px solid var(--line); padding: .8rem .55rem .5rem; transition: border-color .16s ease, background .16s ease; }
    [data-testid="stMetric"]:hover { border-color: var(--teal); background: rgba(251,250,246,.78); }
    [data-testid="stMetricLabel"] { color: var(--muted); font-size: .72rem; }
    [data-testid="stMetricValue"] { color: var(--ink); font-family: Georgia, serif; letter-spacing: -.02em; }
    [data-testid="stVerticalBlockBorderWrapper"] { border-color: var(--line); border-radius: 2px; background: rgba(251,250,246,.55); }
    div[data-testid="stPlotlyChart"] { border-top: 1px solid var(--line); }
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
        background: var(--surface); border-color: #c7c3b8; border-radius: 2px;
    }
    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
        border-radius: 2px; box-shadow: none; font-weight: 700; letter-spacing: .01em;
        transition: background .15s ease, border-color .15s ease, color .15s ease, transform .15s ease;
    }
    [data-testid="stBaseButton-primary"] { background: var(--rust) !important; border-color: var(--rust) !important; color: #fff !important; }
    [data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-primary"] span { color: #fff !important; }
    [data-testid="stBaseButton-primary"]:hover { background: var(--ink) !important; border-color: var(--ink) !important; color: #fff !important; transform: translateY(-1px); }
    [data-testid="stBaseButton-primary"]:hover p, [data-testid="stBaseButton-primary"]:hover span { color: #fff !important; }
    [data-testid="stBaseButton-secondary"] { background: var(--surface) !important; border-color: #9d998e !important; color: var(--ink) !important; }
    [data-testid="stBaseButton-secondary"] p, [data-testid="stBaseButton-secondary"] span { color: var(--ink) !important; }
    [data-testid="stBaseButton-secondary"]:hover { background: var(--teal-soft) !important; border-color: var(--teal) !important; color: var(--ink) !important; }
    [data-testid="stFormSubmitButton"] button { background: var(--rust) !important; border-color: var(--rust) !important; color: #fff !important; }
    [data-testid="stFormSubmitButton"] button p, [data-testid="stFormSubmitButton"] button span { color: #fff !important; }
    button:focus-visible { outline: 3px solid rgba(22,121,111,.28) !important; outline-offset: 2px; }
    [data-testid="stSegmentedControl"] { background: transparent; }
    [data-testid="stSegmentedControl"] button { border-radius: 2px !important; font-size: .78rem; font-weight: 650; }
    [data-testid="stSegmentedControl"] button[aria-pressed="true"] { background: var(--ink) !important; border-color: var(--ink) !important; }
    [data-testid="stSegmentedControl"] button[aria-pressed="true"] p { color: #fff !important; }
    [data-testid="stExpander"] { border-color: var(--line); border-radius: 2px; background: rgba(251,250,246,.5); }
    [data-testid="stFileUploaderDropzone"] { background: var(--surface); border: 1px dashed #aaa69b; border-radius: 2px; }
    @media (max-width: 760px) {
        .block-container { padding: .8rem 1rem 3rem; }
        .process-line { grid-template-columns: 1fr; }
        .process-step { border-right: 0; border-bottom: 1px solid var(--line); padding-left: 0 !important; }
        .risk-row { grid-template-columns: 80px 1fr; }
        .risk-message { grid-column: 1 / -1; }
        .hero-title { font-size: 3.5rem; }
        .system-status span:nth-child(2) { display: none; }
    }
    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after { transition: none !important; animation: none !important; }
    }
</style>
"""


def apply_global_styles() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def navigate(page: str) -> None:
    st.session_state["requested_page"] = page


def get_profile() -> Optional[Mapping[str, Any]]:
    return st.session_state.get("startup_profile")


def get_scorecard(profile: Mapping[str, Any]) -> Mapping[str, Any]:
    scorecard = st.session_state.get("scorecard")
    if scorecard is None:
        scorecard = score_startup(profile)
        st.session_state["scorecard"] = scorecard
    return scorecard


def seed_form(profile: Mapping[str, Any]) -> None:
    """Load every normalized field into its keyed form widget."""
    st.session_state.update(startup_widget_state(profile))
    st.session_state["startup_form_seed"] = dict(profile)


def render_top_navigation() -> str:
    """Render the brand and workspace navigation at the top of every page."""
    requested = st.session_state.pop("requested_page", None)
    if requested in PAGES:
        st.session_state["nav_page"] = requested
    if st.session_state.get("nav_page") not in PAGES:
        st.session_state["nav_page"] = "Briefing"

    mark, brand, navigation = st.columns((0.07, 0.25, 0.68), vertical_alignment="center")
    with mark:
        st.image(str(LOGO_PATH), width=44)
    with brand:
        st.markdown('<div class="brand-copy"><div class="brand-name">VentureLens</div><div class="brand-sub">Investment screening desk</div></div>', unsafe_allow_html=True)
    with navigation:
        page = st.segmented_control("Workspace", PAGES, key="nav_page", label_visibility="collapsed", width="stretch")
    active = get_profile()
    active_label = (
        f'<strong>{escape(str(active["startup_name"]))}</strong> · {escape(str(active["stage"]))}'
        if active else "No active review"
    )
    st.markdown(
        f'<div class="system-status"><span><i class="status-dot"></i>Screening engine ready</span>'
        f'<span>Model 1.0 / local-first / explainable</span><span>{active_label}</span></div>',
        unsafe_allow_html=True,
    )
    return page or "Briefing"


def render_page_title(kicker: str, title: str, copy: str) -> None:
    st.markdown(f'<div class="kicker">{escape(kicker)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-title">{escape(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-copy">{escape(copy)}</div>', unsafe_allow_html=True)


def render_home() -> None:
    """Render an editorial product briefing instead of a generic landing page."""
    left, right = st.columns((2.15, 0.85), gap="large", vertical_alignment="bottom")
    with left:
        st.markdown('<div class="kicker">First-pass venture underwriting</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-title">A clearer way to decide what deserves diligence.</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-copy">VentureLens turns a startup profile into an explainable scorecard, risk register, diligence agenda, and preliminary memo—without pretending incomplete evidence is certainty.</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("Open a company review", type="primary"):
            navigate("Company Review")
            st.rerun()
    with right:
        active = get_profile()
        if active:
            scorecard = get_scorecard(active)
            st.markdown(
                f'<div class="docket"><div class="docket-label">Current docket</div><div class="docket-value">{escape(str(active["startup_name"]))}</div>'
                f'<div class="docket-meta">{scorecard["overall_score"]}/100 · {escape(scorecard["overall_label"])} · {escape(scorecard["risk_rating"])} risk</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="docket"><div class="docket-label">Current docket</div><div class="docket-value">No active review</div><div class="docket-meta">Load a fictional company, upload a CSV, or start from a blank profile.</div></div>', unsafe_allow_html=True)

    st.write("")
    st.write("")
    st.markdown("## The screen is organized around four questions")
    sections = (
        ("01", "Can this become venture-scale?", "Market structure, growth, business model, and the path to an outcome large enough for venture economics."),
        ("02", "Is there evidence of pull?", "Revenue, growth, customers, retention, and the quality—not just the quantity—of early traction."),
        ("03", "Do the economics improve with scale?", "Gross margin, acquisition efficiency, retention, burn, and runway viewed as one operating system."),
        ("04", "What could break the case?", "Competitive response, team gaps, financing constraints, missing evidence, and the claims that need independent proof."),
    )
    for number, title, body in sections:
        st.markdown(f'<div class="section-rule"><div class="num">{number}</div><div><h3>{title}</h3><p>{body}</p></div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("## From raw input to an IC-ready brief")
    st.markdown(
        '<div class="process-line">'
        '<div class="process-step"><span>STEP 01</span><strong>Structure the evidence</strong><p>Normalize the company, market, traction, economics, team, and risk inputs.</p></div>'
        '<div class="process-step"><span>STEP 02</span><strong>Pressure-test the case</strong><p>Trace every score to a rule, surface gaps, and separate attractiveness from risk.</p></div>'
        '<div class="process-step"><span>STEP 03</span><strong>Write the first memo</strong><p>Generate a careful synthesis locally or through the optional guarded API path.</p></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.info("Educational screening only. VentureLens organizes supplied evidence; it does not verify claims, predict outcomes, or provide investment advice.")


def render_profile_header(profile: Mapping[str, Any]) -> None:
    st.markdown(
        f'<div class="company-strip"><div class="company-name">{escape(str(profile["startup_name"]))}</div>'
        f'<div class="company-meta">{escape(str(profile["industry"]))} · {escape(str(profile["stage"]))} · {escape(str(profile["geography"]))}</div>'
        f'<div class="company-desc">{escape(str(profile["product_description"]))}</div></div>',
        unsafe_allow_html=True,
    )


def render_metric_snapshot(profile: Mapping[str, Any]) -> None:
    columns = st.columns(5)
    metrics = (
        ("ARR / revenue", format_currency(profile.get("current_arr"))),
        ("Annual growth", format_percentage(profile.get("revenue_growth_rate"))),
        ("Gross margin", format_percentage(profile.get("gross_margin"))),
        ("Runway", f'{profile["runway_months"]:.0f} months' if profile.get("runway_months") is not None else "Not provided"),
        ("Customers", format_number(profile.get("customer_count"))),
    )
    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label, value)


def render_detail_pair(label: str, value: Any) -> None:
    st.markdown(f'<div class="detail-label">{escape(label)}</div><div class="detail-copy">{escape(str(value or "Not provided"))}</div>', unsafe_allow_html=True)


def render_company_details(profile: Mapping[str, Any]) -> None:
    left, right = st.columns(2, gap="large")
    with left:
        render_detail_pair("Problem", profile.get("problem_statement"))
        render_detail_pair("Target customer", profile.get("target_customer"))
        render_detail_pair("Business model", f'{profile.get("business_model")} · {profile.get("revenue_model") or "Revenue model not provided"}')
        render_detail_pair("Market evidence", profile.get("market_notes"))
    with right:
        render_detail_pair("Differentiation", profile.get("differentiation"))
        render_detail_pair("Competitive set", profile.get("competitors"))
        render_detail_pair("Founder / team", profile.get("founder_notes"))
        render_detail_pair("Known risks", profile.get("risk_notes"))


def render_unit_economics(profile: Mapping[str, Any]) -> None:
    ratio = safe_divide(profile.get("ltv"), profile.get("cac"))
    columns = st.columns(5)
    metrics = (
        ("CAC", format_currency(profile.get("cac"))),
        ("LTV", format_currency(profile.get("ltv"))),
        ("LTV / CAC", f"{ratio:.1f}x" if ratio is not None else "Not available"),
        ("Funding raised", format_currency(profile.get("funding_raised"))),
        ("Valuation", format_currency(profile.get("valuation"))),
    )
    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label, value)


def render_csv_source() -> None:
    """Render upload guidance, downloads, schema, and profile selection."""
    upload_column, guide_column = st.columns((1.35, 0.65), gap="large")
    with upload_column:
        st.markdown("#### Upload a startup CSV")
        st.caption("UTF-8 `.csv` · one startup per row · required columns are checked before loading")
        upload = st.file_uploader("Choose CSV file", type=("csv",), label_visibility="collapsed")
        if upload is not None:
            try:
                uploaded_profiles = profile_options(load_startup_csv(upload))
                upload_name = st.selectbox("Company to review", tuple(uploaded_profiles), key="uploaded_company")
                if st.button("Load uploaded profile", type="primary", width="stretch"):
                    selected = uploaded_profiles[upload_name]
                    seed_form(selected)
                    st.success(f"Loaded {upload_name}. Review the populated fields below.")
            except ValueError as exc:
                st.error(str(exc))
    with guide_column:
        st.markdown('<div class="source-panel"><div class="detail-label">Need the correct format?</div><p>Download the repository template, replace the fictional example row, and keep the header names unchanged.</p></div>', unsafe_allow_html=True)
        st.download_button(
            "Download CSV template",
            data=CSV_TEMPLATE_PATH.read_bytes(),
            file_name="venturelens-upload-template.csv",
            mime="text/csv",
            width="stretch",
        )
    with st.expander("View accepted columns and formatting rules"):
        st.markdown("**Three required columns:** `startup_name`, `product_description`, and `target_customer`. All others are optional.")
        guide = pd.DataFrame(CSV_FIELD_DEFINITIONS, columns=("Column", "Requirement", "Type", "What to enter"))
        st.dataframe(guide, hide_index=True, width="stretch")
        st.caption("Enter 78 for 78%. Keep unknown optional values blank. Numeric currency fields should not contain symbols or commas.")


def render_startup_screener() -> None:
    """Render evidence sourcing, the grouped form, and the active profile brief."""
    render_page_title(
        "Workspace 01 · Evidence intake",
        "Build the company record.",
        "Start with a fictional example, import a properly formatted CSV, or create a blank review. Then inspect and save the normalized evidence before scoring.",
    )
    source = st.segmented_control(
        "Starting point",
        ("Fictional sample", "CSV upload", "Blank review"),
        default="Fictional sample",
        key="review_source",
    )
    st.write("")
    if source == "Fictional sample":
        samples = profile_options(load_sample_startups())
        picker, action = st.columns((3, 1), vertical_alignment="bottom")
        with picker:
            sample_name = st.selectbox("Fictional company", tuple(samples), key="sample_company")
        with action:
            if st.button("Load sample", type="primary", width="stretch"):
                seed_form(samples[sample_name])
                st.success(f"Loaded {sample_name}. Review the populated fields below.")
    elif source == "CSV upload":
        render_csv_source()
    else:
        st.markdown('<div class="source-panel"><div class="detail-label">Blank review</div><p>Start with an empty profile. Unknown metrics can remain blank and will become explicit evidence gaps.</p></div>', unsafe_allow_html=True)
        if st.button("Start a clean review"):
            clean = blank_startup()
            seed_form(clean)
            for key in ("startup_profile", "scorecard", "memo_result"):
                st.session_state.pop(key, None)
            st.rerun()

    st.write("")
    form_seed = st.session_state.get("startup_form_seed", get_profile())
    profile = render_startup_input_form(form_seed)
    if profile is not None:
        st.session_state["startup_profile"] = profile
        st.session_state.pop("scorecard", None)
        st.session_state.pop("memo_result", None)
        st.success("Company record saved. The scorecard has been recalculated from this evidence.")

    active = get_profile()
    if active:
        st.write("")
        st.write("")
        st.markdown("## Current company brief")
        render_profile_header(active)
        render_metric_snapshot(active)
        st.write("")
        render_company_details(active)
        st.markdown("### Unit economics and capitalization")
        render_unit_economics(active)
        if st.button("Continue to IC scorecard", type="primary"):
            navigate("IC Scorecard")
            st.rerun()


def render_empty_state() -> None:
    st.warning("There is no active company record. Load a sample, upload a CSV, or save a blank review first.")
    if st.button("Open Company Review", type="primary"):
        navigate("Company Review")
        st.rerun()


def risk_badge(rating: str) -> str:
    return f'<span class="risk-chip risk-{rating.lower()}">{escape(rating)} risk</span>'


def render_risk_register(scorecard: Mapping[str, Any]) -> None:
    flags = scorecard["risk_flags"]
    if not flags:
        st.success("No rule-based flags were triggered. This does not eliminate unobserved risk.")
        return
    for flag in flags:
        severity = flag["severity"]
        css_class = "risk-context" if severity == "Context" else f"risk-{severity.lower()}"
        st.markdown(
            f'<div class="risk-row"><div><span class="risk-chip {css_class}">{escape(severity)}</span></div>'
            f'<div class="risk-category">{escape(str(flag["category"]))}</div><div class="risk-message">{escape(str(flag["message"]))}</div></div>',
            unsafe_allow_html=True,
        )


def render_scoring_dashboard() -> None:
    """Render the investment screen as an IC-style analytical brief."""
    render_page_title(
        "Workspace 02 · Explainable screen",
        "See the case—and what could break it.",
        "The overall score is a weighted screen, not a recommendation. Risk remains separate so an attractive opportunity can still carry material diligence concerns.",
    )
    profile = get_profile()
    if profile is None:
        render_empty_state()
        return
    scorecard = get_scorecard(profile)
    render_profile_header(profile)
    st.write("")

    score, view, evidence = st.columns((0.8, 1.35, 0.85), vertical_alignment="center")
    with score:
        st.markdown(f'<div class="score-hero"><div class="score-number">{scorecard["overall_score"]}</div><div class="score-denominator">Overall score / 100</div></div>', unsafe_allow_html=True)
    with view:
        st.markdown(f'<div class="score-hero"><div class="score-call">{escape(scorecard["overall_label"])}</div>{risk_badge(scorecard["risk_rating"])}<p class="fine-print">Attractiveness and risk are intentionally presented as separate decisions.</p></div>', unsafe_allow_html=True)
    with evidence:
        st.markdown(f'<div class="score-hero"><div class="score-call">{scorecard["data_completeness"]}%</div><div class="score-denominator">Evidence completeness</div><p class="fine-print">Model version {escape(scorecard["model_version"])}</p></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("## Category analysis")
    profile_chart, contribution_chart = st.columns(2, gap="large")
    with profile_chart:
        st.caption("CATEGORY SCORE · HIGHER IS STRONGER")
        st.plotly_chart(build_score_profile_chart(scorecard["categories"]), width="stretch", config={"displayModeBar": False})
    with contribution_chart:
        st.caption("WEIGHTED POINT CONTRIBUTION · OVERALL SCORE")
        st.plotly_chart(build_weighted_contribution_chart(scorecard["categories"]), width="stretch", config={"displayModeBar": False})

    st.markdown("## Read the score")
    for category, result in scorecard["categories"].items():
        with st.expander(f'{category} · {result["score"]}/100 · {result["label"]}'):
            st.caption(f'WEIGHT {result["weight"]:.0%}')
            left, right = st.columns(2, gap="large")
            with left:
                st.markdown("**Observed rationale**")
                for item in result["rationale"]:
                    st.markdown(f"- {item}")
            with right:
                st.markdown("**Evidence gaps**")
                if result["evidence_gaps"]:
                    for gap in result["evidence_gaps"]:
                        st.markdown(f"- {gap}")
                else:
                    st.write("No category-specific gaps were generated.")

    st.write("")
    risk_left, risk_right = st.columns((1.65, 0.75), gap="large")
    with risk_left:
        st.markdown("## Risk register")
        render_risk_register(scorecard)
    with risk_right:
        st.markdown("## Flag mix")
        st.plotly_chart(build_risk_summary_chart(scorecard["risk_flags"]), width="stretch", config={"displayModeBar": False})

    st.write("")
    st.markdown("## Priority diligence questions")
    for number, question in enumerate(scorecard["diligence_questions"], start=1):
        st.markdown(f'<div class="question-row"><span>{number:02d}</span><div>{escape(question)}</div></div>', unsafe_allow_html=True)

    with st.expander("Scoring methodology and weights"):
        for category, weight in CATEGORY_WEIGHTS.items():
            st.markdown(f"- **{category}:** {weight:.0%}")
        st.caption("Thresholds are readable in src/scoring_model.py. They are educational heuristics, not statistically validated predictors.")
    if st.button("Continue to memo builder", type="primary"):
        navigate("Memo Builder")
        st.rerun()


def render_memo_page() -> None:
    """Render memo controls, evidence preview, final memo, and export."""
    render_page_title(
        "Workspace 03 · Structured synthesis",
        "Turn the screen into a memo.",
        "Use the deterministic local engine or the optional OpenAI-assisted path. Both start from the same normalized evidence and calculated scorecard.",
    )
    profile = get_profile()
    if profile is None:
        render_empty_state()
        return
    scorecard = get_scorecard(profile)
    render_profile_header(profile)
    render_metric_snapshot(profile)
    st.write("")

    controls, boundary = st.columns((0.8, 1.2), gap="large")
    with controls:
        st.markdown("### Memo engine")
        mode = st.radio(
            "Generation method",
            ("Local deterministic memo", "OpenAI-assisted memo"),
            label_visibility="collapsed",
            help="Local mode makes no network request. AI mode sends the structured evidence payload to the configured OpenAI API account.",
        )
        if mode == "OpenAI-assisted memo":
            if has_api_key():
                st.success("API key detected. The secret is never displayed in the application or memo.")
            else:
                st.warning("No API key detected. Generation will use the complete local fallback.")
    with boundary:
        st.markdown("### Evidence boundary")
        st.write("The memo receives the normalized profile, score rationales, evidence gaps, risk flags, and diligence questions. It is instructed not to introduce outside facts.")
        st.caption("AI-assisted mode sends this displayed evidence to the configured OpenAI API account. The request sets store=False.")

    with st.expander("Inspect the structured memo payload"):
        st.json(build_memo_payload(profile, scorecard))

    label = "Generate AI-assisted memo" if mode == "OpenAI-assisted memo" else "Generate local memo"
    if st.button(label, type="primary", width="stretch"):
        with st.spinner("Preparing the preliminary memo…"):
            if mode == "OpenAI-assisted memo":
                result = generate_investment_memo(profile, scorecard)
            else:
                result = {
                    "content": build_fallback_memo(profile, scorecard),
                    "source": "Local deterministic fallback",
                    "model": None,
                    "warning": None,
                }
            st.session_state["memo_result"] = result

    result = st.session_state.get("memo_result")
    if result:
        st.write("")
        st.markdown("## Preliminary investment memo")
        source = result["source"] + (f' · {result["model"]}' if result.get("model") else "")
        st.caption(f"SOURCE · {source}")
        if result.get("warning"):
            st.warning(result["warning"])
        with st.container(border=True):
            st.markdown(result["content"])
        safe_name = re.sub(r"[^a-z0-9]+", "-", profile["startup_name"].lower()).strip("-") or "startup"
        st.download_button(
            "Download memo as Markdown",
            data=result["content"],
            file_name=f"{safe_name}-investment-memo.md",
            mime="text/markdown",
            width="stretch",
        )
        st.caption("Educational analysis only—not investment advice or a substitute for independent diligence.")


def render_footer() -> None:
    st.markdown('<div class="footer"><span>VentureLens · Version 1.0</span><span>Educational screening · Not investment advice</span></div>', unsafe_allow_html=True)


def main() -> None:
    """Run the application with a top-level workspace model."""
    apply_global_styles()
    page = render_top_navigation()
    if page == "Briefing":
        render_home()
    elif page == "Company Review":
        render_startup_screener()
    elif page == "IC Scorecard":
        render_scoring_dashboard()
    else:
        render_memo_page()
    render_footer()


if __name__ == "__main__":
    main()
