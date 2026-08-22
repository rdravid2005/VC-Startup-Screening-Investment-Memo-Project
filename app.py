"""Streamlit entry point for the AI Venture Capital Investment Screener."""

from __future__ import annotations

from html import escape
from typing import Any, Mapping, Optional

import streamlit as st

from src.scoring_model import CATEGORY_WEIGHTS, score_startup
from src.startup_inputs import (
    load_sample_startups,
    load_startup_csv,
    profile_options,
    render_startup_input_form,
)
from src.utils import format_currency, format_number, format_percentage, safe_divide
from src.visualizations import build_risk_summary_chart, build_score_bar_chart, build_score_radar_chart


st.set_page_config(
    page_title="AI VC Investment Screener",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


GLOBAL_CSS = """
<style>
    :root {
        --ink: #e8eef6;
        --muted: #91a3b7;
        --teal: #34d3b5;
        --panel: rgba(13, 27, 42, 0.78);
        --border: rgba(145, 163, 183, 0.18);
    }
    .stApp {
        background:
            radial-gradient(circle at 85% 0%, rgba(52, 211, 181, 0.10), transparent 30rem),
            radial-gradient(circle at 20% 35%, rgba(91, 143, 249, 0.08), transparent 28rem),
            #07111f;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: rgba(7, 17, 31, 0.94);
        border-right: 1px solid var(--border);
    }
    .block-container { max-width: 1320px; padding-top: 2.2rem; padding-bottom: 4rem; }
    h1, h2, h3 { letter-spacing: -0.025em; }
    p, label { color: var(--ink); }
    .eyebrow {
        color: var(--teal); text-transform: uppercase; letter-spacing: .16em;
        font-size: .76rem; font-weight: 700; margin-bottom: .65rem;
    }
    .hero-title {
        font-size: clamp(2.8rem, 6vw, 5.6rem); line-height: .98; max-width: 940px;
        font-weight: 740; letter-spacing: -.055em; margin: 0 0 1.2rem;
        background: linear-gradient(110deg, #f4f8fc 15%, #a9c3df 65%, #34d3b5 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hero-copy { color: var(--muted); max-width: 760px; font-size: 1.2rem; line-height: 1.65; }
    .panel, .feature-card, .overview-card {
        background: var(--panel); border: 1px solid var(--border); border-radius: 16px;
        padding: 1.35rem 1.4rem; box-shadow: 0 16px 44px rgba(0,0,0,.18);
    }
    .feature-card { min-height: 195px; }
    .feature-number { color: var(--teal); font: 700 .76rem/1 ui-monospace, monospace; letter-spacing: .14em; }
    .feature-card h3 { font-size: 1.2rem; margin: 1.5rem 0 .55rem; }
    .feature-card p, .overview-card p { color: var(--muted); line-height: 1.55; margin-bottom: 0; }
    .company-name { font-size: 1.65rem; font-weight: 700; margin-bottom: .3rem; }
    .company-meta { color: var(--teal); font-size: .85rem; letter-spacing: .04em; }
    [data-testid="stMetric"] {
        background: var(--panel); border: 1px solid var(--border); border-radius: 14px;
        padding: 1rem 1.1rem;
    }
    [data-testid="stMetricLabel"] { color: var(--muted); }
    div[data-testid="stPlotlyChart"] { border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }
    .score-orb {
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        width: 146px; height: 146px; border-radius: 50%; margin: .2rem auto 1rem;
        background: radial-gradient(circle, rgba(52,211,181,.15), rgba(52,211,181,.03));
        border: 2px solid #34d3b5; box-shadow: 0 0 42px rgba(52,211,181,.14);
    }
    .score-orb strong { font-size: 3rem; line-height: 1; }
    .score-orb span { color: var(--muted); font-size: .74rem; text-transform: uppercase; letter-spacing: .1em; }
    .risk-high, .risk-elevated, .risk-moderate, .risk-low, .risk-context {
        display: inline-block; border-radius: 999px; padding: .3rem .65rem;
        font-size: .76rem; font-weight: 700; letter-spacing: .03em;
    }
    .risk-high, .risk-elevated { color: #ffabab; background: rgba(240,106,106,.14); }
    .risk-moderate { color: #ffd88d; background: rgba(245,184,75,.14); }
    .risk-low { color: #79ebd4; background: rgba(52,211,181,.14); }
    .risk-context { color: #a9c5ff; background: rgba(91,143,249,.14); }
    .small-muted { color: var(--muted); font-size: .86rem; }
    hr { border-color: var(--border) !important; }
</style>
"""


def apply_global_styles() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def navigate(page: str) -> None:
    st.session_state["requested_page"] = page


def get_profile() -> Optional[Mapping[str, Any]]:
    return st.session_state.get("startup_profile")


def get_scorecard(profile: Mapping[str, Any]) -> Mapping[str, Any]:
    cached = st.session_state.get("scorecard")
    if cached is None:
        cached = score_startup(profile)
        st.session_state["scorecard"] = cached
    return cached


def render_home() -> None:
    """Render the project landing page."""
    st.markdown('<div class="eyebrow">Evidence before conviction</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Turn startup data into an investment thesis.</div>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-copy">A structured first-pass VC workspace for assessing market opportunity, traction, unit economics, competitive position, financial health, and the questions that deserve deeper diligence.</p>',
        unsafe_allow_html=True,
    )
    action, note = st.columns((1, 3), vertical_alignment="center")
    with action:
        if st.button("Start a screening →", type="primary", use_container_width=True):
            navigate("Startup Screener")
            st.rerun()
    with note:
        st.caption("Built for educational analysis · No investment recommendations")

    st.write("")
    st.write("")
    columns = st.columns(3)
    features = (
        ("01 / STRUCTURE", "Startup Screening", "Capture qualitative context and operating metrics in one consistent company profile."),
        ("02 / EXPLAIN", "VC Scorecard", "See transparent category scores, explicit weights, evidence gaps, and risk flags."),
        ("03 / SYNTHESIZE", "Investment Memo", "Convert only the supplied evidence into a careful VC-style memo with next-step questions."),
    )
    for column, (number, title, description) in zip(columns, features):
        with column:
            st.markdown(
                f'<div class="feature-card"><span class="feature-number">{number}</span><h3>{title}</h3><p>{description}</p></div>',
                unsafe_allow_html=True,
            )

    st.write("")
    st.markdown("### A disciplined screening workflow")
    workflow = st.columns(4)
    for column, title, detail in zip(
        workflow,
        ("Frame", "Measure", "Challenge", "Synthesize"),
        ("Define the company and customer", "Review traction and economics", "Surface risks and missing proof", "Create a diligence-ready memo"),
    ):
        with column:
            st.caption(title.upper())
            st.write(detail)
    st.info("This application is an educational screening tool. Its outputs are not investment advice and do not replace independent diligence.")


def render_profile_header(profile: Mapping[str, Any]) -> None:
    st.markdown(
        f'<div class="overview-card"><div class="company-name">{escape(str(profile["startup_name"]))}</div>'
        f'<div class="company-meta">{escape(str(profile["industry"])).upper()} · {escape(str(profile["stage"])).upper()} · {escape(str(profile["geography"])).upper()}</div>'
        f'<p>{escape(str(profile["product_description"]))}</p></div>',
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


def render_company_details(profile: Mapping[str, Any]) -> None:
    left, right = st.columns(2)
    with left:
        st.markdown("#### Business and market")
        st.markdown(f"**Problem**  \n{profile.get('problem_statement') or 'Not provided'}")
        st.markdown(f"**Target customer**  \n{profile.get('target_customer') or 'Not provided'}")
        st.markdown(f"**Business model**  \n{profile.get('business_model')} · {profile.get('revenue_model') or 'Revenue model not provided'}")
        st.markdown(f"**Market context**  \n{profile.get('market_notes') or 'Not provided'}")
    with right:
        st.markdown("#### Positioning and team")
        st.markdown(f"**Differentiation**  \n{profile.get('differentiation') or 'Not provided'}")
        st.markdown(f"**Competitive set**  \n{profile.get('competitors') or 'Not provided'}")
        st.markdown(f"**Founder / team**  \n{profile.get('founder_notes') or 'Not provided'}")
        st.markdown(f"**Known risks**  \n{profile.get('risk_notes') or 'Not provided'}")


def render_unit_economics(profile: Mapping[str, Any]) -> None:
    st.markdown("### Unit economics and capitalization")
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


def render_startup_screener() -> None:
    """Render sample selection, CSV upload, the form, and profile snapshot."""
    st.markdown('<div class="eyebrow">01 / Company evidence</div>', unsafe_allow_html=True)
    st.title("Startup Screener")
    st.write("Load a fictional company, upload compatible CSV data, or enter a startup manually.")

    source_tab, upload_tab = st.tabs(("Fictional samples", "Upload CSV"))
    selected_profile = st.session_state.get("startup_profile")
    with source_tab:
        samples = profile_options(load_sample_startups())
        sample_name = st.selectbox("Sample startup", tuple(samples))
        if st.button("Load sample", use_container_width=True):
            selected_profile = samples[sample_name]
            st.session_state["startup_form_seed"] = selected_profile
            st.success(f"Loaded {sample_name}. Review the profile and select Analyze startup.")
    with upload_tab:
        upload = st.file_uploader("Startup profiles CSV", type=("csv",))
        st.caption("Use the column names in sample_data/sample_startups.csv. Unknown columns are ignored.")
        if upload is not None:
            try:
                uploaded_profiles = profile_options(load_startup_csv(upload))
                upload_name = st.selectbox("Uploaded startup", tuple(uploaded_profiles))
                if st.button("Use uploaded profile", use_container_width=True):
                    selected_profile = uploaded_profiles[upload_name]
                    st.session_state["startup_form_seed"] = selected_profile
                    st.success(f"Loaded {upload_name}.")
            except ValueError as exc:
                st.error(str(exc))

    st.divider()
    seed = st.session_state.get("startup_form_seed", selected_profile)
    profile = render_startup_input_form(seed)
    if profile is not None:
        st.session_state["startup_profile"] = profile
        st.session_state.pop("scorecard", None)
        selected_profile = profile
        st.success("Profile saved and ready for scoring.")

    active_profile = st.session_state.get("startup_profile")
    if active_profile:
        st.divider()
        st.markdown('<div class="eyebrow">Screening snapshot</div>', unsafe_allow_html=True)
        render_profile_header(active_profile)
        st.write("")
        render_metric_snapshot(active_profile)
        render_company_details(active_profile)
        render_unit_economics(active_profile)
        if st.button("Open scoring dashboard →", type="primary"):
            navigate("Scoring Dashboard")
            st.rerun()


def render_empty_state(destination: str) -> None:
    st.warning("No startup has been analyzed yet. Load a fictional profile or enter a company first.")
    if st.button("Go to Startup Screener", type="primary"):
        navigate("Startup Screener")
        st.rerun()


def risk_badge(rating: str) -> str:
    css_class = f"risk-{rating.lower()}"
    return f'<span class="{css_class}">{rating} risk</span>'


def render_risk_flags(scorecard: Mapping[str, Any]) -> None:
    flags = scorecard["risk_flags"]
    st.markdown("### Risk register")
    if not flags:
        st.success("No rule-based risk flags were triggered. This does not eliminate unobserved risks.")
        return
    for flag in flags:
        label = flag["severity"]
        css_class = "risk-context" if label == "Context" else f"risk-{label.lower()}"
        st.markdown(
            f'<div class="panel"><span class="{css_class}">{label}</span> '
            f'<span class="small-muted">{escape(str(flag["category"]))}</span><br><br>{escape(str(flag["message"]))}</div>',
            unsafe_allow_html=True,
        )
        st.write("")


def render_scoring_dashboard() -> None:
    """Render overall, category, risk, and diligence analysis."""
    st.markdown('<div class="eyebrow">02 / Explainable assessment</div>', unsafe_allow_html=True)
    st.title("VC Scoring Dashboard")
    profile = get_profile()
    if profile is None:
        render_empty_state("Scoring Dashboard")
        return
    scorecard = get_scorecard(profile)
    render_profile_header(profile)
    st.write("")

    score_column, context_column = st.columns((1, 2))
    with score_column:
        st.markdown(
            f'<div class="panel"><div class="score-orb"><strong>{scorecard["overall_score"]}</strong><span>overall / 100</span></div>'
            f'<div style="text-align:center"><strong>{scorecard["overall_label"]}</strong><br><br>{risk_badge(scorecard["risk_rating"])}</div></div>',
            unsafe_allow_html=True,
        )
    with context_column:
        metric_columns = st.columns(2)
        with metric_columns[0]:
            st.metric("Data completeness", f'{scorecard["data_completeness"]}%')
        with metric_columns[1]:
            st.metric("Model version", scorecard["model_version"])
        st.markdown("#### How to read this result")
        st.write(
            "The overall score is the weighted sum of nine rule-based categories. "
            "Risk is displayed separately so a promising company can still carry material diligence concerns."
        )
        st.caption(scorecard["disclaimer"])

    st.markdown("### Category profile")
    radar_column, bar_column = st.columns(2)
    with radar_column:
        st.plotly_chart(build_score_radar_chart(scorecard["categories"]), use_container_width=True, config={"displayModeBar": False})
    with bar_column:
        st.plotly_chart(build_score_bar_chart(scorecard["categories"]), use_container_width=True, config={"displayModeBar": False})

    st.markdown("### Score rationale")
    for category, result in scorecard["categories"].items():
        with st.expander(f'{category} · {result["score"]}/100 · {result["label"]}'):
            st.caption(f'Weight in overall score: {result["weight"]:.0%}')
            st.markdown("**Observed rationale**")
            for item in result["rationale"]:
                st.markdown(f"- {item}")
            if result["evidence_gaps"]:
                st.markdown("**Evidence gaps**")
                for gap in result["evidence_gaps"]:
                    st.markdown(f"- {gap}")

    risk_column, chart_column = st.columns((3, 2))
    with risk_column:
        render_risk_flags(scorecard)
    with chart_column:
        st.markdown("### Flag mix")
        st.plotly_chart(build_risk_summary_chart(scorecard["risk_flags"]), use_container_width=True, config={"displayModeBar": False})

    st.markdown("### Priority diligence questions")
    for number, question in enumerate(scorecard["diligence_questions"], start=1):
        st.markdown(f"**{number:02d}** &nbsp; {question}")
    st.divider()
    st.markdown("#### Methodology")
    weight_text = " · ".join(f"{category} {weight:.0%}" for category, weight in CATEGORY_WEIGHTS.items())
    st.caption(weight_text)
    st.caption("Thresholds are documented in src/scoring_model.py. They are illustrative screening heuristics, not statistically validated predictors.")


def render_memo_placeholder() -> None:
    st.markdown('<div class="eyebrow">03 / Structured synthesis</div>', unsafe_allow_html=True)
    st.title("AI Investment Memo")
    if get_profile() is None:
        render_empty_state("AI Investment Memo")
        return
    st.info("Memo generation is the next implementation phase. Your active profile and scorecard are ready.")


def main() -> None:
    """Run the application and sidebar navigation."""
    apply_global_styles()
    st.sidebar.markdown("## ◆ VentureLens")
    st.sidebar.caption("AI VC Investment Screener")
    pages = ("Home", "Startup Screener", "Scoring Dashboard", "AI Investment Memo")
    requested_page = st.session_state.pop("requested_page", None)
    if requested_page in pages:
        st.session_state["nav_page"] = requested_page
    if st.session_state.get("nav_page") not in pages:
        st.session_state["nav_page"] = "Home"
    page = st.sidebar.radio("Workspace", pages, key="nav_page")
    st.sidebar.divider()
    active = get_profile()
    if active:
        st.sidebar.caption("ACTIVE COMPANY")
        st.sidebar.markdown(f'**{active["startup_name"]}**')
        st.sidebar.caption(f'{active["stage"]} · {active["industry"]}')
    else:
        st.sidebar.caption("No active company")
    st.sidebar.divider()
    st.sidebar.caption("Educational screening only. Not investment advice.")

    if page == "Home":
        render_home()
    elif page == "Startup Screener":
        render_startup_screener()
    elif page == "Scoring Dashboard":
        render_scoring_dashboard()
    else:
        render_memo_placeholder()


if __name__ == "__main__":
    main()
