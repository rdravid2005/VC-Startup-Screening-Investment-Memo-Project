"""Transparent, rule-based VC screening score calculations.

The model is intentionally heuristic. It organizes evidence for educational
screening; it is not trained on outcomes and does not predict investment returns.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple

from src.startup_inputs import normalize_startup_data
from src.utils import clamp, format_currency, format_number, format_percentage, is_missing, safe_divide, score_label


MODEL_VERSION = "1.0"
CATEGORY_WEIGHTS = OrderedDict(
    (
        ("Market Opportunity", 0.15),
        ("Product / Differentiation", 0.12),
        ("Traction", 0.18),
        ("Business Model Quality", 0.10),
        ("Unit Economics", 0.12),
        ("Founder / Team Strength", 0.10),
        ("Competitive Positioning", 0.08),
        ("Financial Health", 0.10),
        ("Risk Resilience", 0.05),
    )
)


def _band(value: float, bands: Sequence[Tuple[float, float]]) -> float:
    """Return the score for the first inclusive upper-bound band."""
    for upper_bound, score in bands:
        if value <= upper_bound:
            return score
    return bands[-1][1]


def _result(score: float, rationale: List[str], gaps: List[str]) -> Dict[str, Any]:
    rounded = round(clamp(score))
    return {
        "score": rounded,
        "label": score_label(rounded),
        "rationale": rationale,
        "evidence_gaps": gaps,
    }


def _component(
    value: Any,
    label: str,
    scorer: Callable[[float], float],
    formatter: Callable[[Any], str],
    rationale: List[str],
    gaps: List[str],
    missing_score: float = 40,
) -> float:
    """Score one optional numeric input without treating absence as zero."""
    if value is None:
        gaps.append(f"{label} was not provided.")
        rationale.append(f"{label}: missing evidence; a conservative neutral score was used.")
        return missing_score
    score = scorer(float(value))
    rationale.append(f"{label}: {formatter(value)} contributed {round(score)}/100.")
    return score


def score_market_opportunity(startup: Mapping[str, Any]) -> Dict[str, Any]:
    rationale: List[str] = []
    gaps: List[str] = []
    size_score = _component(
        startup.get("estimated_market_size"), "Addressable market",
        lambda value: _band(value, ((100_000_000, 25), (500_000_000, 45), (1_000_000_000, 60), (5_000_000_000, 75), (10_000_000_000, 85), (float("inf"), 95))),
        format_currency, rationale, gaps,
    )
    growth_score = _component(
        startup.get("market_growth_rate"), "Market growth",
        lambda value: _band(value, ((0, 20), (5, 35), (10, 55), (15, 70), (25, 85), (float("inf"), 95))),
        format_percentage, rationale, gaps,
    )
    evidence_score = 70 if len(startup.get("market_notes", "")) >= 60 else 50 if startup.get("market_notes") else 35
    rationale.append(
        "Market evidence: supporting context was provided." if startup.get("market_notes")
        else "Market evidence: no supporting context was provided."
    )
    if not startup.get("market_notes"):
        gaps.append("Bottom-up market evidence and source quality need validation.")
    return _result(0.50 * size_score + 0.30 * growth_score + 0.20 * evidence_score, rationale, gaps)


def score_product_differentiation(startup: Mapping[str, Any]) -> Dict[str, Any]:
    rationale: List[str] = []
    gaps: List[str] = []
    product = startup.get("product_description", "")
    problem = startup.get("problem_statement", "")
    differentiation = startup.get("differentiation", "")
    product_score = 75 if len(product) >= 90 else 60 if len(product) >= 40 else 40
    problem_score = 75 if len(problem) >= 70 else 55 if problem else 35
    differentiation_score = 80 if len(differentiation) >= 80 else 60 if differentiation else 30
    rationale.extend(
        (
            f"Product description provides {'substantive' if product_score >= 75 else 'basic'} screening detail.",
            f"Problem definition provides {'substantive' if problem_score >= 75 else 'limited'} screening detail.",
            "Differentiation is explicitly described." if differentiation else "Differentiation was not described.",
        )
    )
    if not problem:
        gaps.append("Customer problem severity and current alternative are not documented.")
    if not differentiation:
        gaps.append("No defensible product differentiation was supplied.")
    return _result(0.30 * product_score + 0.25 * problem_score + 0.45 * differentiation_score, rationale, gaps)


def score_traction(startup: Mapping[str, Any]) -> Dict[str, Any]:
    rationale: List[str] = []
    gaps: List[str] = []
    revenue_score = _component(
        startup.get("current_arr"), "ARR / annual revenue",
        lambda value: _band(value, ((0, 15), (100_000, 30), (500_000, 48), (1_000_000, 62), (3_000_000, 76), (10_000_000, 88), (float("inf"), 95))),
        format_currency, rationale, gaps,
    )
    growth_score = _component(
        startup.get("revenue_growth_rate"), "Annual revenue growth",
        lambda value: _band(value, ((0, 15), (20, 35), (40, 52), (70, 68), (100, 82), (float("inf"), 94))),
        format_percentage, rationale, gaps,
    )
    customer_score = _component(
        startup.get("customer_count"), "Customer count",
        lambda value: _band(value, ((0, 15), (5, 30), (20, 48), (50, 62), (200, 75), (1_000, 86), (float("inf"), 94))),
        format_number, rationale, gaps,
    )
    retention_score = _component(
        startup.get("retention_rate"), "Annual customer retention",
        lambda value: _band(value, ((60, 25), (75, 42), (85, 60), (92, 76), (97, 88), (float("inf"), 95))),
        format_percentage, rationale, gaps,
    )
    return _result(0.35 * revenue_score + 0.30 * growth_score + 0.15 * customer_score + 0.20 * retention_score, rationale, gaps)


def score_business_model(startup: Mapping[str, Any]) -> Dict[str, Any]:
    rationale: List[str] = []
    gaps: List[str] = []
    model = startup.get("business_model", "")
    revenue_model = startup.get("revenue_model", "")
    recurring = any(term in f"{model} {revenue_model}".lower() for term in ("saas", "subscription", "recurring"))
    model_score = 78 if recurring else 65 if model and model != "Other" else 45
    description_score = 75 if len(revenue_model) >= 18 else 55 if revenue_model else 30
    margin = startup.get("gross_margin")
    margin_score = _component(
        margin, "Gross margin support",
        lambda value: _band(value, ((30, 25), (50, 45), (65, 62), (80, 80), (float("inf"), 90))),
        format_percentage, rationale, gaps,
    )
    rationale.insert(0, f"Revenue structure: {'recurring characteristics identified' if recurring else 'recurrence requires validation'}.")
    if not revenue_model:
        gaps.append("Pricing mechanics and revenue model were not provided.")
    return _result(0.35 * model_score + 0.25 * description_score + 0.40 * margin_score, rationale, gaps)


def score_unit_economics(startup: Mapping[str, Any]) -> Dict[str, Any]:
    rationale: List[str] = []
    gaps: List[str] = []
    margin_score = _component(
        startup.get("gross_margin"), "Gross margin",
        lambda value: _band(value, ((30, 20), (50, 40), (65, 58), (75, 72), (85, 86), (float("inf"), 92))),
        format_percentage, rationale, gaps,
    )
    ltv_cac = safe_divide(startup.get("ltv"), startup.get("cac"))
    ratio_score = _component(
        ltv_cac, "LTV / CAC",
        lambda value: _band(value, ((1, 20), (2, 40), (3, 60), (5, 80), (float("inf"), 90))),
        lambda value: f"{value:.1f}x", rationale, gaps,
    )
    retention_score = _component(
        startup.get("retention_rate"), "Annual customer retention",
        lambda value: _band(value, ((60, 25), (75, 45), (85, 62), (92, 78), (97, 88), (float("inf"), 94))),
        format_percentage, rationale, gaps,
    )
    if ltv_cac is None:
        gaps.append("LTV and CAC are both needed to assess acquisition efficiency.")
    return _result(0.40 * margin_score + 0.35 * ratio_score + 0.25 * retention_score, rationale, gaps)


def score_team(startup: Mapping[str, Any]) -> Dict[str, Any]:
    notes = startup.get("founder_notes", "")
    rationale: List[str] = []
    gaps: List[str] = []
    if not notes:
        score = 35
        rationale.append("No founder / team evidence was supplied.")
        gaps.append("Founder-market fit, execution history, role coverage, and hiring plan need diligence.")
    else:
        score = 58
        lower = notes.lower()
        if len(notes) >= 100:
            score += 8
            rationale.append("Team notes provide substantive screening detail.")
        if any(term in lower for term in ("previously", "experience", "led", "managed", "built", "operated")):
            score += 10
            rationale.append("Relevant operating or functional experience is described.")
        if any(term in lower for term in ("incomplete", "no founder", "gap", "hiring")):
            score -= 8
            rationale.append("The supplied notes identify a team-coverage or hiring gap.")
        gaps.append("References, founder-market fit, ownership, and recruiting capacity remain unverified.")
    return _result(score, rationale, gaps)


def score_competitive_positioning(startup: Mapping[str, Any]) -> Dict[str, Any]:
    competitors = startup.get("competitors", "")
    differentiation = startup.get("differentiation", "")
    rationale: List[str] = []
    gaps: List[str] = []
    competitor_score = 65 if len(competitors) >= 35 else 50 if competitors else 30
    differentiation_score = 80 if len(differentiation) >= 80 else 60 if differentiation else 30
    rationale.append("Named alternatives or competitors were provided." if competitors else "No competitor set was provided.")
    rationale.append("A specific differentiation thesis was provided." if differentiation else "No differentiation thesis was provided.")
    if not competitors:
        gaps.append("Direct, indirect, and do-nothing alternatives need mapping.")
    if not differentiation:
        gaps.append("Durability and customer proof of differentiation need assessment.")
    else:
        gaps.append("Customer references should validate the claimed differentiation.")
    return _result(0.40 * competitor_score + 0.60 * differentiation_score, rationale, gaps)


def score_financial_health(startup: Mapping[str, Any]) -> Dict[str, Any]:
    rationale: List[str] = []
    gaps: List[str] = []
    runway_score = _component(
        startup.get("runway_months"), "Runway",
        lambda value: _band(value, ((6, 15), (9, 30), (12, 45), (18, 68), (24, 82), (float("inf"), 90))),
        lambda value: f"{value:.0f} months", rationale, gaps,
    )
    burn = startup.get("monthly_burn_rate")
    arr = startup.get("current_arr")
    burn_multiple = safe_divide(burn * 12 if burn is not None else None, arr)
    efficiency_score = _component(
        burn_multiple, "Annualized burn / ARR",
        lambda value: _band(value, ((0.5, 90), (1, 78), (2, 62), (4, 42), (float("inf"), 22))),
        lambda value: f"{value:.1f}x", rationale, gaps,
    )
    funding_score = _component(
        startup.get("funding_raised"), "Funding raised",
        lambda value: _band(value, ((0, 30), (1_000_000, 45), (5_000_000, 62), (15_000_000, 75), (float("inf"), 82))),
        format_currency, rationale, gaps,
    )
    if burn_multiple is None:
        gaps.append("ARR and monthly burn are needed for a simple burn-efficiency view.")
    return _result(0.50 * runway_score + 0.35 * efficiency_score + 0.15 * funding_score, rationale, gaps)


def generate_risk_flags(startup: Mapping[str, Any]) -> List[Dict[str, str]]:
    """Generate deterministic flags from supplied metrics and evidence gaps."""
    flags: List[Dict[str, str]] = []

    def add(severity: str, category: str, message: str) -> None:
        flags.append({"severity": severity, "category": category, "message": message})

    runway = startup.get("runway_months")
    if runway is None:
        add("Medium", "Financial", "Runway is unknown.")
    elif runway < 9:
        add("High", "Financial", f"Only {runway:.0f} months of runway were reported.")
    elif runway < 15:
        add("Medium", "Financial", f"Runway of {runway:.0f} months may constrain execution or fundraising timing.")

    margin = startup.get("gross_margin")
    if margin is None:
        add("Medium", "Unit economics", "Gross margin is unknown.")
    elif margin < 50:
        add("High", "Unit economics", f"Gross margin of {margin:.0f}% limits operating leverage.")
    elif margin < 65:
        add("Medium", "Unit economics", f"Gross margin of {margin:.0f}% is below mature software benchmarks.")

    ratio = safe_divide(startup.get("ltv"), startup.get("cac"))
    if ratio is None:
        add("Medium", "Unit economics", "LTV / CAC cannot be calculated from the supplied information.")
    elif ratio < 2:
        add("High", "Unit economics", f"LTV / CAC of {ratio:.1f}x suggests weak acquisition efficiency.")
    elif ratio < 3:
        add("Medium", "Unit economics", f"LTV / CAC of {ratio:.1f}x requires improvement or validation.")

    retention = startup.get("retention_rate")
    if retention is None:
        add("Medium", "Traction", "Customer retention is unknown.")
    elif retention < 75:
        add("High", "Traction", f"Annual retention of {retention:.0f}% indicates material churn risk.")
    elif retention < 85:
        add("Medium", "Traction", f"Annual retention of {retention:.0f}% may limit efficient growth.")

    if not startup.get("differentiation"):
        add("High", "Competition", "No product differentiation was provided.")
    if not startup.get("founder_notes"):
        add("Medium", "Team", "Founder / team evidence is missing.")
    if not startup.get("competitors"):
        add("Medium", "Competition", "The competitive set is not documented.")
    if startup.get("risk_notes"):
        add("Context", "Management-identified", startup["risk_notes"])

    order = {"High": 0, "Medium": 1, "Context": 2}
    return sorted(flags, key=lambda flag: order[flag["severity"]])


def score_risk_resilience(startup: Mapping[str, Any]) -> Dict[str, Any]:
    flags = generate_risk_flags(startup)
    high_count = sum(flag["severity"] == "High" for flag in flags)
    medium_count = sum(flag["severity"] == "Medium" for flag in flags)
    score = 88 - high_count * 18 - medium_count * 8
    rationale = [
        f"Rule checks identified {high_count} high-severity and {medium_count} medium-severity flags.",
        "A higher Risk Resilience score means fewer observed metric or evidence concerns.",
    ]
    gaps = [flag["message"] for flag in flags if flag["severity"] in {"High", "Medium"}]
    return _result(score, rationale, gaps)


def generate_diligence_questions(startup: Mapping[str, Any], flags: Sequence[Mapping[str, str]]) -> List[str]:
    """Create a concise set of company-specific follow-up questions."""
    questions: List[str] = []
    if startup.get("estimated_market_size") is None or not startup.get("market_notes"):
        questions.append("What bottom-up assumptions and independent sources support the addressable-market estimate?")
    if startup.get("revenue_growth_rate") is None:
        questions.append("What has monthly and annualized revenue growth been, and which cohorts or customers drive it?")
    if startup.get("retention_rate") is None or startup.get("retention_rate", 100) < 85:
        questions.append("What are gross and net retention by customer cohort, and what are the primary causes of churn?")
    if safe_divide(startup.get("ltv"), startup.get("cac")) is None:
        questions.append("How are CAC, CAC payback, contribution margin, and LTV calculated by acquisition channel?")
    if startup.get("runway_months") is None or startup.get("runway_months", 99) < 15:
        questions.append("What operating milestones can be reached before the next financing is required?")
    if not startup.get("differentiation") or any(flag["category"] == "Competition" for flag in flags):
        questions.append("Why do customers choose this product over direct competitors, internal tools, and doing nothing?")
    if not startup.get("founder_notes"):
        questions.append("How does the founding team's experience map to the market, product, and go-to-market risks?")
    else:
        questions.append("Which critical capabilities are missing from the current team, and what is the hiring plan?")
    questions.extend(
        (
            "Which customer references can validate ROI, implementation effort, and willingness to expand?",
            "What assumptions create the largest downside variance in the next 18-month operating plan?",
        )
    )
    return list(dict.fromkeys(questions))[:8]


def _risk_rating(flags: Sequence[Mapping[str, str]], overall_score: float) -> str:
    high_count = sum(flag["severity"] == "High" for flag in flags)
    medium_count = sum(flag["severity"] == "Medium" for flag in flags)
    if high_count >= 2 or overall_score < 40:
        return "High"
    if high_count == 1 or medium_count >= 3 or overall_score < 55:
        return "Elevated"
    if medium_count >= 1 or overall_score < 75:
        return "Moderate"
    return "Low"


def _data_completeness(startup: Mapping[str, Any]) -> int:
    fields = (
        "estimated_market_size", "market_growth_rate", "market_notes",
        "current_arr", "revenue_growth_rate", "gross_margin", "runway_months",
        "customer_count", "cac", "ltv", "retention_rate", "competitors",
        "differentiation", "founder_notes", "risk_notes",
    )
    supplied = sum(not is_missing(startup.get(field)) for field in fields)
    return round(100 * supplied / len(fields))


def score_startup(startup: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the complete explainable scorecard for one startup profile."""
    normalized = normalize_startup_data(startup)
    scorers = OrderedDict(
        (
            ("Market Opportunity", score_market_opportunity),
            ("Product / Differentiation", score_product_differentiation),
            ("Traction", score_traction),
            ("Business Model Quality", score_business_model),
            ("Unit Economics", score_unit_economics),
            ("Founder / Team Strength", score_team),
            ("Competitive Positioning", score_competitive_positioning),
            ("Financial Health", score_financial_health),
            ("Risk Resilience", score_risk_resilience),
        )
    )
    categories: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
    for category, scorer in scorers.items():
        result = scorer(normalized)
        result["weight"] = CATEGORY_WEIGHTS[category]
        categories[category] = result

    overall = round(sum(result["score"] * result["weight"] for result in categories.values()))
    flags = generate_risk_flags(normalized)
    return {
        "model_version": MODEL_VERSION,
        "categories": categories,
        "overall_score": overall,
        "overall_label": score_label(overall),
        "risk_rating": _risk_rating(flags, overall),
        "risk_flags": flags,
        "diligence_questions": generate_diligence_questions(normalized, flags),
        "data_completeness": _data_completeness(normalized),
        "disclaimer": "Educational screening heuristic—not a prediction or investment recommendation.",
    }
