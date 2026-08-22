"""End-to-end Streamlit application-flow tests."""

from streamlit.testing.v1 import AppTest


def _radio(app: AppTest, label: str):
    return next(control for control in app.radio if control.label == label)


def _button(app: AppTest, label: str):
    return next(control for control in app.button if control.label == label)


def _loaded_atlasgrid_app() -> AppTest:
    app = AppTest.from_file("app.py", default_timeout=30).run()
    _radio(app, "Workspace").set_value("Startup Screener").run()
    _button(app, "Load sample").click().run()
    assert app.text_input[0].value == "AtlasGrid"
    _button(app, "Analyze startup").click().run()
    assert not app.exception
    return app


def test_home_page_loads_without_runtime_errors():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception
    assert _radio(app, "Workspace").value == "Home"
    assert any("Turn startup data" in block.value for block in app.markdown)


def test_sample_profile_reaches_complete_scoring_dashboard():
    app = _loaded_atlasgrid_app()
    _radio(app, "Workspace").set_value("Scoring Dashboard").run()
    assert not app.exception
    assert app.title[0].value == "VC Scoring Dashboard"
    assert len(app.get("plotly_chart")) == 3
    assert len(app.expander) == 9
    assert any(metric.label == "Data completeness" and metric.value == "100%" for metric in app.metric)


def test_local_memo_flow_renders_required_content():
    app = _loaded_atlasgrid_app()
    _radio(app, "Workspace").set_value("AI Investment Memo").run()
    _button(app, "Generate local memo").click().run()
    assert not app.exception
    rendered_markdown = "\n".join(block.value for block in app.markdown)
    assert "Executive Summary" in rendered_markdown
    assert "Preliminary Investment View" in rendered_markdown
    assert "not investment advice" in rendered_markdown
