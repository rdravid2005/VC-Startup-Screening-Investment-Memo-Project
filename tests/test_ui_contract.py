"""Static checks for important visual-system contracts."""

import ast
from pathlib import Path


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def _global_css() -> str:
    tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "GLOBAL_CSS"
            for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError("GLOBAL_CSS was not found in app.py")


def test_primary_button_labels_have_explicit_visible_colors():
    css = _global_css()
    assert '[data-testid="stBaseButton-primary"] p' in css
    assert "color: #fff !important" in css
    assert '[data-testid="stFormSubmitButton"] button p' in css


def test_interface_contract_keeps_top_navigation_and_no_sidebar():
    source = APP_PATH.read_text(encoding="utf-8")
    css = _global_css()
    assert 'st.segmented_control("Workspace"' in source
    assert '[data-testid="stSidebar"]' in css
    assert "display: none" in css
