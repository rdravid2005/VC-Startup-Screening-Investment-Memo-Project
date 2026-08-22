# Development Notes

## Architecture decisions

- Keep `app.py` focused on navigation and composition.
- Keep validation and normalization independent from Streamlit where practical.
- Represent absent metrics as `None`, never as fabricated zeros.
- Return score rationales with every category result.
- Maintain a deterministic local memo so the project remains demonstrable without paid API access.
- Store the active startup and scorecard in Streamlit session state.

## Key implementation choices

### Interface system

The original dark, gradient-heavy sidebar interface was replaced after reviewing current product and public-sector design guidance. Version 1 now uses a top workspace switcher, original VentureLens mark, warm editorial palette, square controls, flat hierarchy, and purpose-led comparison charts. Navigation recedes while the current company and decision evidence dominate. The form follows one vertical reading order with numbered evidence groups and uses blank numeric text fields so optional information no longer requires a second “use this value” control.

### CSV onboarding

CSV import is treated as a user workflow, not just a file picker. The Company Review workspace states the accepted type before upload, exposes a downloadable production-compatible template, renders the supported schema, and returns row-specific validation messages. The same template and a detailed data dictionary are committed under `sample_data/` so GitHub users can prepare an upload without first running the app.

### Missing data

Missing numeric values remain `None`; they are never changed to zero. Each scoring function assigns a visible conservative-neutral component when evidence is absent and records the missing item as an evidence gap. This avoids accidentally treating an undisclosed metric as genuine zero performance.

### Overall score and risk

The overall score is a weighted sum of nine categories. Risk Resilience is positively oriented—a higher value means fewer observed concerns—so every category comparison points in the same favorable direction. The final risk rating is calculated separately from the overall score and severity mix. This allows a high-opportunity startup to remain visibly high-risk.

### Qualitative evidence

Version 1 cannot verify qualitative claims. Text-based rules therefore assess whether screening detail exists, not whether the claim is true. The resulting rationale and memo repeatedly call for customer references and independent validation.

### Memo generation

The local memo uses exactly the same profile and scorecard as the dashboard. AI-assisted mode sends a JSON evidence boundary through the Responses API. The request does not enable search or other tools. Direct recommendation phrases trigger replacement with the local memo, as do missing keys, API errors, and empty responses.

### State management

The normalized profile, scorecard, and memo live in Streamlit session state. Saving a changed profile invalidates both downstream artifacts, and recomputing the scorecard occurs only when needed.

## Verification completed

- Static Python compilation on Python 3.9
- Unit tests for normalization, CSV validation, scoring, risk, prompts, fallback, and guardrails
- Streamlit application tests for the home page and the complete sample → scorecard → memo path
- Runtime server startup and local health request
- Git whitespace and ignored-secret checks

## Interview walkthrough

1. Start with the product problem: startup inputs are inconsistent and difficult to compare.
2. Load AtlasGrid to demonstrate a complete profile, then contrast it with ParcelMint's higher risk rating.
3. Open a category expander to show that each score has a weight, rationale, and evidence gaps.
4. Explain why the overall score and risk rating are separate.
5. Generate the local memo to prove the app works without paid infrastructure.
6. Preview the AI evidence payload and explain prompt-injection boundaries and fallback behavior.
7. Close with limitations: the model organizes claims but does not verify them or predict outcomes.

## Delivery checkpoints

1. `cc51d41` — repository scaffold and application shell
2. `aa00aaf` — startup schema, form, validation, and fictional data
3. `3d599e5` — transparent scoring and risk engine
4. `ecc3cb9` — screening and scoring dashboards
5. `71fab36` — guarded memo generation
6. Final documentation and QA commit
