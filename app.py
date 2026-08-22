"""Streamlit entry point for the AI Venture Capital Investment Screener."""

import streamlit as st


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
        render_placeholder(
            "Startup Screener",
            "The manual input form and fictional sample loader are the next build step.",
        )
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

