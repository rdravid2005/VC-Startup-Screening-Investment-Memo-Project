# Development Notes

## Architecture decisions

- Keep `app.py` focused on navigation and composition.
- Keep validation and normalization independent from Streamlit where practical.
- Represent absent metrics as `None`, never as fabricated zeros.
- Return score rationales with every category result.
- Maintain a deterministic local memo so the project remains demonstrable without paid API access.
- Store the active startup and scorecard in Streamlit session state.

## Delivery checkpoints

1. Repository scaffold and application shell
2. Startup schema, form, and sample data
3. Transparent scoring engine
4. Screening and scoring dashboards
5. Guarded memo generation
6. Documentation and final QA

