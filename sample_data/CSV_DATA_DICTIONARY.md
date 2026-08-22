# CSV Upload Data Dictionary

Use [`upload_template.csv`](upload_template.csv) as the starting point for a bulk startup upload. Keep the header row unchanged and place one startup on each following row.

## Required columns

| Column | Type | Description | Example |
|---|---|---|---|
| `startup_name` | Text | Company name used throughout the analysis | `ExampleCo` |
| `product_description` | Text | Plain-language description of the product or service | `Workflow software for finance teams` |
| `target_customer` | Text | Primary buyer, user, or customer segment | `Mid-market CFO teams` |

Rows missing any required value are rejected with the CSV row number and a corrective message.

## Optional company and market columns

| Column | Type | Description | Example |
|---|---|---|---|
| `industry` | Text | Company sector | `Fintech` |
| `business_model` | Text | Primary commercial model | `B2B SaaS` |
| `problem_statement` | Text | Customer problem and current pain | `Teams reconcile data manually` |
| `geography` | Text | Primary operating market | `United States` |
| `stage` | Text | Financing or company stage | `Seed` |
| `revenue_model` | Text | How the company charges | `Annual subscription` |
| `estimated_market_size` | Number, USD | Estimated addressable market; do not include `$` or commas | `5000000000` |
| `market_growth_rate` | Number, % | Estimated annual market growth as percentage points | `12` |
| `market_notes` | Text | Source, calculation, or context for market claims | `Bottom-up estimate based on 20,000 buyers` |

## Optional traction and economics columns

| Column | Type | Description | Example |
|---|---|---|---|
| `current_arr` | Number, USD | Current ARR or annualized revenue | `750000` |
| `revenue_growth_rate` | Number, % | Annual revenue growth as percentage points | `65` |
| `gross_margin` | Number, % | Gross margin as percentage points | `78` |
| `monthly_burn_rate` | Number, USD | Current monthly net cash burn | `150000` |
| `runway_months` | Number | Months of cash runway | `16` |
| `customer_count` | Whole number | Current paying customers | `30` |
| `cac` | Number, USD | Customer acquisition cost | `12000` |
| `ltv` | Number, USD | Customer lifetime value | `48000` |
| `retention_rate` | Number, % | Annual customer retention as percentage points | `90` |
| `funding_raised` | Number, USD | Total funding raised | `2500000` |
| `valuation` | Number, USD | Latest company valuation | `12000000` |

## Optional qualitative columns

| Column | Type | Description | Example |
|---|---|---|---|
| `competitors` | Text | Direct, indirect, and do-nothing alternatives | `Competitor A; spreadsheets; internal tools` |
| `differentiation` | Text | Claimed reason customers choose the company | `Deploys in one day without an integration team` |
| `founder_notes` | Text | Relevant experience, role coverage, and team gaps | `CEO previously led procurement operations` |
| `risk_notes` | Text | Known commercial, product, regulatory, team, or financing risks | `Customer concentration; 12 months of runway` |

## Formatting rules

- Save the file as UTF-8 CSV.
- Keep numeric fields numeric. Do not add currency symbols, percent symbols, `x`, or commas.
- Use percentage points: enter `78` for 78%, not `0.78`.
- Leave unknown optional fields blank. Do not enter zero unless the true reported value is zero.
- Wrap text containing commas in double quotes. Spreadsheet applications normally do this automatically.
- Do not rename headers. Unknown extra columns are ignored.
- The template's `ExampleCo` row is fictional and should be replaced before analyzing real user-provided information.
