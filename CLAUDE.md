# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtual environment (required before running anything)
source env/bin/activate

# Run the app
streamlit run app.py

# Install dependencies
pip install -r requirements.txt
```

There are no automated tests or linting commands — the `test_*.py` and `debug_*.py` files at the root are one-off scripts used during development, not a test suite.

## Architecture

This is a **Streamlit** single-page application for financial forecasting. The entry point is `app.py`, which instantiates `ForecastApp` and calls `.run()`.

### Data flow

```
Excel upload (C&N Funnel Report from Salesforce)
  → ExcelParser         (auto-detects header row, typically row 12)
  → DataProcessor       (cleans rows, fills missing Lead Times from ClientDatabase)
  → DataValidator       (validates required fields, BUs, dates, amounts)
  → ForecastCalculator  (applies billing rules per BU → list of BillingEvents)
  → Managers            (render AGGrid tables + Plotly charts via Streamlit)
```

### Manager pattern

`app.py` delegates all tab rendering to two managers:
- `ForecastMainManager` — main forecast (≥60% probability opportunities)
- `ForecastLowProbManager` — low-probability pipeline view

Both extend `BaseForecastManager` (`src/managers/base_forecast_manager.py`), which owns the shared `DataProcessor`, `DataValidator`, and `ForecastCalculator` instances, plus `merge_results_with_existing()` for `st.session_state`.

### Key modules in `src/`

| Module | Purpose |
|--------|---------|
| `models.py` | Core dataclasses: `Opportunity`, `BillingEvent`; enums: `BillingStage`, `BusinessUnit` |
| `forecast_calculator.py` | Billing rules by BU — the core business logic |
| `data_processor.py` | Reads/cleans Excel; uses `ClientDatabase` to infer missing Lead Times |
| `excel_parser.py` | Auto-detects header row in uploaded Excel files |
| `validators.py` | Row-level validation, returns `ValidationResult` objects |
| `kpi_processor.py` | KPI table processing (MX/SAPI entity) |
| `llc_kpi_processor.py` | KPI table processing (LLC/US entity) |
| `client_database.py` | SQLite at `data/client_history.db` — historical Lead Times and Payment Terms per client |
| `ui_components.py` | AGGrid wrappers, filter row, totals panel, export buttons |
| `consolidated_report_generator.py` | Multi-sheet Excel export combining all views |
| `chatbot.py` | OpenAI GPT-4o-mini assistant (optional; requires API key at runtime) |

### Configuration (`config/settings.py`)

All business rules are in frozen dataclasses — change here, nowhere else:
- `BUSINESS_RULES` — lead time minimums, billing percentages per stage, financial penalty factors
- `EXCEL_CONFIG` — header row index, required column names
- `APP_CONFIG` — valid BUs (`ICT`, `FCT`, `IAT`, `REP`, `SWD`), supported date formats

### Billing rules (implemented in `ForecastCalculator`)

- **ICT without PIA**: 1 payment (100%) after Lead Time
- **ICT with PIA**: 2 payments — PIA upfront + remainder after Lead Time
- **FCT / IAT / REP / SWD without PIA**: 4 stages — INICIO 30%, DR (+30d) 30%, FAT (DR + Lead Time) 30%, SAT (FAT +30d) 10%
- **FCT / IAT / REP / SWD with PIA**: PIA replaces INICIO; DR and FAT split 50/50; SAT keeps 10%
- **Billing type** (sidebar toggle): "Contable" vs "Financiera" — Financiera applies a 40% penalty factor (60% for exactly 60%-probability opportunities)

### Input file format

Excel exported from Salesforce C&N Funnel Report. Headers auto-detected (typically row 12, data from row 13). Required columns: `Opportunity Name`, `BU`, `Amount`, `Close Date`, `Lead Time`, `Payment Terms`, `Probability (%) ↑`, `Paid in Advance`. `Account Name` is optional but used when present.
