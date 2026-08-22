"""Tests for prompt construction, AI integration, and local memo fallback."""

from types import SimpleNamespace

from src.memo_generator import (
    MEMO_SECTIONS,
    build_fallback_memo,
    build_memo_payload,
    build_memo_prompt,
    generate_investment_memo,
    output_passes_guardrails,
)
from src.scoring_model import score_startup
from src.startup_inputs import load_sample_startups


def _profile_and_scorecard():
    profile = load_sample_startups()[0]
    return profile, score_startup(profile)


def test_payload_contains_only_structured_evidence():
    profile, scorecard = _profile_and_scorecard()
    payload = build_memo_payload(profile, scorecard)
    assert payload["startup"]["startup_name"] == "AtlasGrid"
    assert payload["screening"]["overall_score"] == scorecard["overall_score"]
    assert payload["required_sections"] == list(MEMO_SECTIONS)


def test_prompt_marks_json_as_evidence_and_forbids_external_knowledge():
    profile, scorecard = _profile_and_scorecard()
    prompt = build_memo_prompt(profile, scorecard)
    assert "<startup_evidence_json>" in prompt
    assert "do not use external knowledge" in prompt
    assert '"startup_name": "AtlasGrid"' in prompt


def test_fallback_contains_every_required_section():
    profile, scorecard = _profile_and_scorecard()
    memo = build_fallback_memo(profile, scorecard)
    for section in MEMO_SECTIONS:
        assert f"## {section}" in memo
    assert "not investment advice" in memo
    assert "Invest in this company" not in memo


def test_no_key_returns_complete_local_fallback(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    profile, scorecard = _profile_and_scorecard()
    result = generate_investment_memo(profile, scorecard, api_key="")
    assert result["source"] == "Local deterministic fallback"
    assert "## Executive Summary" in result["content"]
    assert result["warning"]


def test_injected_client_uses_responses_api():
    class FakeResponses:
        def __init__(self):
            self.arguments = None

        def create(self, **kwargs):
            self.arguments = kwargs
            return SimpleNamespace(output_text="# Memo\n\nThis case requires further diligence.")

    fake_responses = FakeResponses()
    fake_client = SimpleNamespace(responses=fake_responses)
    profile, scorecard = _profile_and_scorecard()
    result = generate_investment_memo(profile, scorecard, client=fake_client, model="test-model")
    assert result["source"] == "OpenAI Responses API"
    assert result["model"] == "test-model"
    assert fake_responses.arguments["store"] is False
    assert "startup_evidence_json" in fake_responses.arguments["input"]


def test_guardrail_failure_uses_fallback():
    bad_response = SimpleNamespace(output_text="Invest in this company. It is a guaranteed winner.")
    fake_client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: bad_response))
    profile, scorecard = _profile_and_scorecard()
    result = generate_investment_memo(profile, scorecard, client=fake_client)
    assert result["source"] == "Local deterministic fallback"
    assert "guardrails" in result["warning"]


def test_direct_recommendation_patterns_are_rejected():
    assert not output_passes_guardrails("Pass on this company.")
    assert not output_passes_guardrails("This startup will succeed.")
    assert output_passes_guardrails("The investment case depends on retention evidence.")
