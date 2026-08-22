"""Streamlit entry point for the AI Venture Capital Investment Screener."""

import streamlit as st

from src.startup_inputs import (
    load_sample_startups,
    load_startup_csv,
    profile_options,
    render_startup_input_form,
)


st.set_page_config(
    page_title="AI VC Investment Screener",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_home() -> None:
    """Render the project landing page."""
    st.title("AI Venture Capital Investment Screener")
    st.subheader(
        "Analyze startups across market, traction, unit economics, "
        "competition, and risk."
    )
    st.markdown(
        "Turn messy startup information into a structured, first-pass "
        "venture capital screening analysis."
    )

    columns = st.columns(3)
    features = (
        ("01", "Startup Screening Dashboard", "Organize company, market, traction, financial, and team inputs."),
        ("02", "Transparent VC Scoring", "Compare strengths and diligence gaps using explainable rules."),
        ("03", "AI Investment Memo", "Convert structured evidence into a guarded VC-style memo."),
    )
    for column, (number, title, description) in zip(columns, features):
        with column:
            st.caption(number)
            st.markdown(f"### {title}")
            st.write(description)

    st.info(
        "Educational screening tool only. Outputs are not investment advice "
        "and should not replace independent diligence."
    )


def render_placeholder(title: str, description: str) -> None:
    """Render a friendly placeholder while a module is being built."""
    st.title(title)
    st.info(description)


def render_startup_screener() -> None:
    """Render sample selection, CSV upload, and the startup form."""
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
        st.success("Profile saved. Continue to the Scoring Dashboard when ready.")


def main() -> None:
    """Run the application shell and sidebar navigation."""
    st.sidebar.markdown("## VentureLens")
    st.sidebar.caption("Structured startup screening")
    page = st.sidebar.radio(
        "Workspace",
        ("Home", "Startup Screener", "Scoring Dashboard", "AI Investment Memo"),
    )
    st.sidebar.divider()
    st.sidebar.caption("Built for educational analysis—not investment advice.")

    if page == "Home":
        render_home()
    elif page == "Startup Screener":
        render_startup_screener()
    elif page == "Scoring Dashboard":
        render_placeholder(
            "Scoring Dashboard",
            "Transparent category scoring and supporting rationale will appear here.",
        )
    else:
        render_placeholder(
            "AI Investment Memo",
            "Structured memo generation will be enabled after the data and scoring layers.",
        )


if __name__ == "__main__":
    main()
