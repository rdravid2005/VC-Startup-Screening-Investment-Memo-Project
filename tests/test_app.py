"""End-to-end Streamlit application-flow tests."""

from streamlit.testing.v1 import AppTest


def _workspace(app: AppTest):
    return next(control for control in app.get("button_group") if control.label == "Workspace")


def _choose_group(app: AppTest, label: str, value: str) -> AppTest:
    # Streamlit's button-group test element expects the selected value as a list.
    for control in app.get("button_group"):
        control.set_value([value if control.label == label else control.value])
    return next(control for control in app.get("button_group") if control.label == label).run()


def _choose_workspace(app: AppTest, value: str) -> AppTest:
    return _choose_group(app, "Workspace", value)


def _button(app: AppTest, label: str):
    return next(control for control in app.button if control.label == label)


def _click(app: AppTest, label: str) -> AppTest:
    # Preserve single-select button-group state across unrelated button clicks.
    for control in app.get("button_group"):
        control.set_value([control.value])
    return _button(app, label).click().run()


def _loaded_atlasgrid_app() -> AppTest:
    app = AppTest.from_file("app.py", default_timeout=30).run()
    _choose_workspace(app, "Company Review")
    _click(app, "Load sample")
    startup_name = next(field for field in app.text_input if field.label == "Startup name *")
    assert startup_name.value == "AtlasGrid"
    _click(app, "Save profile and calculate score")
    assert not app.exception
    return app


def test_home_page_loads_without_runtime_errors():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception
    assert _workspace(app).value == "Briefing"
    assert any("A clearer way" in block.value for block in app.markdown)


def test_sample_profile_reaches_complete_scoring_dashboard():
    app = _loaded_atlasgrid_app()
    _choose_workspace(app, "IC Scorecard")
    assert not app.exception
    assert any("See the case" in block.value for block in app.markdown)
    assert len(app.get("plotly_chart")) == 3
    score_expanders = [item for item in app.expander if "/100" in item.label]
    assert len(score_expanders) == 9
    assert app.session_state["scorecard"]["data_completeness"] == 100


def test_local_memo_flow_renders_required_content():
    app = _loaded_atlasgrid_app()
    _choose_workspace(app, "Memo Builder")
    _click(app, "Generate local memo")
    assert not app.exception
    rendered_markdown = "\n".join(block.value for block in app.markdown)
    assert "Executive Summary" in rendered_markdown
    assert "Preliminary Investment View" in rendered_markdown
    assert "not investment advice" in rendered_markdown


def test_csv_upload_view_explains_the_contract_before_upload():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    _choose_workspace(app, "Company Review")
    _choose_group(app, "Starting point", "CSV upload")
    assert not app.exception
    assert len(app.get("file_uploader")) == 1
    assert any("Need the correct format" in block.value for block in app.markdown)
    assert any("accepted columns" in item.label.lower() for item in app.expander)


def test_invalid_optional_number_returns_a_helpful_form_error():
    app = AppTest.from_file("app.py", default_timeout=30).run()
    _choose_workspace(app, "Company Review")
    next(field for field in app.text_input if field.label == "Startup name *").set_value("Input Test Co")
    next(field for field in app.text_input if field.label == "Target customer *").set_value("Finance teams")
    next(field for field in app.text_area if field.label == "Product description *").set_value("Workflow software for finance teams.")
    next(field for field in app.text_input if field.label == "ARR / revenue · USD").set_value("not-a-number")
    _click(app, "Save profile and calculate score")
    assert not app.exception
    assert any("Check the numeric fields" in message.value for message in app.error)
