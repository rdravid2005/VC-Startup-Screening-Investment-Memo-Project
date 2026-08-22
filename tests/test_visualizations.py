"""Tests for the purpose-led Plotly screening figures."""

import pytest

from src.scoring_model import score_startup
from src.startup_inputs import load_sample_startups
from src.visualizations import build_risk_summary_chart, build_score_profile_chart, build_weighted_contribution_chart


@pytest.fixture
def scorecard():
    return score_startup(load_sample_startups()[0])


def test_score_profile_has_one_marker_per_category(scorecard):
    figure = build_score_profile_chart(scorecard["categories"])
    assert len(figure.data) == len(scorecard["categories"])
    assert all(trace.mode == "markers+text" for trace in figure.data)
    assert figure.layout.xaxis.range == (0, 108)


def test_weighted_contributions_reconcile_to_overall_score(scorecard):
    figure = build_weighted_contribution_chart(scorecard["categories"])
    contributions = list(figure.data[0].x)
    assert sum(contributions) == pytest.approx(scorecard["overall_score"], abs=0.5)


def test_risk_summary_uses_three_explicit_severity_traces(scorecard):
    figure = build_risk_summary_chart(scorecard["risk_flags"])
    assert [trace.name for trace in figure.data] == ["High", "Medium", "Context"]
    assert figure.layout.barmode == "stack"
