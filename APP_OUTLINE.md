# Application Outline

## Product statement

The AI Venture Capital Investment Screener converts raw startup information into a structured, first-pass VC analysis. It helps a user answer: **Is this company worth deeper diligence, and what evidence matters next?**

## Audience

Finance students, student investment funds, VC interns, startup analysts, early-stage founders, and people learning venture analysis.

## Version 1 modules — implemented

1. **Startup Screener** — capture company, market, traction, unit-economics, financial, team, competition, and risk inputs.
2. **VC Scoring Model** — provide transparent 0–100 category scores, supporting rationale, risk flags, and diligence questions.
3. **Investment Memo** — generate a structured VC-style memo from supplied facts and calculated scores.

## Memo sections

Executive Summary; Company Overview; Problem; Product / Solution; Market Opportunity; Business Model; Traction; Unit Economics; Competitive Landscape; Founder / Team; Key Strengths; Key Risks; Diligence Questions; Preliminary Investment View; and Final Risk Rating.

## Guardrails

- Missing information is identified rather than invented.
- Scores are educational heuristics, not predictive models.
- Language describes an investment case and diligence needs; it does not direct the user to invest or pass.
- Real-time databases, scraping, authentication, portfolio management, and cap-table modeling are out of scope for Version 1.
- All bundled company profiles are fictional.

## Future roadmap

Potential later versions may add pitch-deck extraction, collaborative diligence workflows, scenario analysis, richer market research, portfolio tracking, and controlled data integrations.

## Version 1 completion status

- [x] Manual startup input form
- [x] Validated CSV and fictional sample loader
- [x] Explainable weighted scoring model
- [x] KPI, score, and risk dashboards
- [x] Adaptive risk flags and diligence questions
- [x] Complete no-key investment memo
- [x] Optional guarded OpenAI memo generation
- [x] Markdown preview and download
- [x] Automated data, scoring, memo, and application-flow tests
- [x] Public setup, methodology, privacy, and limitation documentation
