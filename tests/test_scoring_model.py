"""Tests for the transparent VC scoring model."""

from copy import deepcopy

import pytest

from src.scoring_model import CATEGORY_WEIGHTS, score_startup
from src.startup_inputs import load_sample_startups


@pytest.fixture
def complete_profile():
    return load_sample_startups()[0]


def test_category_weights_sum_to_one():
    assert sum(CATEGORY_WEIGHTS.values()) == pytest.approx(1.0)


def test_scorecard_has_expected_categories_and_bounds(complete_profile):
    scorecard = score_startup(complete_profile)
    assert list(scorecard["categories"]) == list(CATEGORY_WEIGHTS)
    assert 0 <= scorecard["overall_score"] <= 100
    assert 0 <= scorecard["data_completeness"] <= 100
    for result in scorecard["categories"].values():
        assert 0 <= result["score"] <= 100
        assert result["rationale"]


def test_overall_score_matches_documented_weighting(complete_profile):
    scorecard = score_startup(complete_profile)
    expected = round(
        sum(result["score"] * result["weight"] for result in scorecard["categories"].values())
    )
    assert scorecard["overall_score"] == expected


def test_missing_data_is_not_treated_as_zero(complete_profile):
    incomplete = deepcopy(complete_profile)
    incomplete["current_arr"] = None
    scorecard = score_startup(incomplete)
    traction = scorecard["categories"]["Traction"]
    assert any("missing evidence" in reason for reason in traction["rationale"])
    assert any("ARR" in gap for gap in traction["evidence_gaps"])


def test_stronger_traction_metrics_improve_traction_score(complete_profile):
    weak = deepcopy(complete_profile)
    weak.update(current_arr=50_000, revenue_growth_rate=5, customer_count=3, retention_rate=65)
    strong = deepcopy(complete_profile)
    strong.update(current_arr=12_000_000, revenue_growth_rate=120, customer_count=1_200, retention_rate=98)
    assert score_startup(strong)["categories"]["Traction"]["score"] > score_startup(weak)["categories"]["Traction"]["score"]


def test_low_runway_and_margin_create_high_risk_flags(complete_profile):
    risky = deepcopy(complete_profile)
    risky.update(runway_months=5, gross_margin=25, ltv=1_000, cac=1_500, retention_rate=60)
    scorecard = score_startup(risky)
    high_categories = {
        flag["category"] for flag in scorecard["risk_flags"] if flag["severity"] == "High"
    }
    assert {"Financial", "Unit economics", "Traction"}.issubset(high_categories)
    assert scorecard["risk_rating"] == "High"


def test_sample_profiles_score_without_errors():
    for profile in load_sample_startups():
        scorecard = score_startup(profile)
        assert scorecard["diligence_questions"]
        assert scorecard["disclaimer"]
