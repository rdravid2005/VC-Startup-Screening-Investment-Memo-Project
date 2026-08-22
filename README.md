# AI Venture Capital Investment Screener

An educational Streamlit application that turns structured startup information into a transparent first-pass VC screening analysis and investment memo.

## Why this project exists

Startup pitches often mix qualitative claims with incomplete operating metrics. This project organizes those inputs into a consistent view of market opportunity, differentiation, traction, business-model quality, unit economics, team, competition, financial health, and risk.

## Planned MVP

- Manual startup input and fictional sample profiles
- Explainable 0–100 category scores
- Interactive screening and scoring dashboards
- Risk flags and suggested diligence questions
- Guarded AI memo generation with a no-key local fallback
- Markdown memo download

## Technology

Python, Streamlit, pandas, NumPy, Plotly, the OpenAI Python SDK, and python-dotenv.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

An OpenAI API key is optional. If it is omitted, the completed app will create a deterministic local memo instead.

## Status

The repository currently contains the application shell. Data collection, scoring, dashboards, and memo generation are being implemented in staged commits.

## Disclaimer

This project is for educational and portfolio demonstration purposes. It does not provide investment advice, predict startup outcomes, or replace legal, financial, commercial, or technical diligence.

