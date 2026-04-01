# btcc-data

Play-Cricket API tools for Barrow Town Cricket Club.

**Club:** Barrow Town CC (site_id: 950)
**League:** Leicestershire & Rutland Cricket League, Premier Division (from 2026)
**Maintainer:** David Seymour (Treasurer)
**Backup:** Bridgett Shipman (Secretary)

## What this does

Scripts that pull BTCC's data from the ECB Play-Cricket API and turn it into
useful things: fixture calendar feeds, results digests, stats dashboards,
and committee reporting tools.

See `docs/api_strategy_v2.md` for the full strategy and phasing.

## Quick start

```bash
# 1. Clone and set up
cd btcc-data
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env and add your API key

# 3. Run Phase 0 validation
python scripts/phase0_tests.py
```

## Folder structure

```
scripts/          Python scripts (the things that run)
data/             Local data — SQLite DB, raw JSON, CSV exports (gitignored)
outputs/          Generated files — iCal feeds, formatted digests
docs/             Strategy documents and specs
templates/        Prompt and report templates
```

## API key security

- The API key lives in `.env` (gitignored — never committed)
- Backup copy in committee Gmail vault
- Key is not club-specific (can query any site_id) — see strategy doc
- ECB agreement signed 1 April 2026

## Phases

| Phase | What | Status |
|-------|------|--------|
| 0 | Validate access, test data model | **Active** |
| 1 | iCal feeds, results digest, captain's form sheet | Blocked on Phase 0 |
| 2 | SQLite data layer, match fee reconciliation | Not started |
| 3 | AI-powered tools (Claude/MCP), committee packs | Not started |
| 4 | Opposition analysis, coaching analytics, benchmarking | Not started |

## Dependencies

- Python 3.10+
- `python-dotenv` — reads `.env` file
- `requests` — HTTP calls to Play-Cricket API
- No cloud infrastructure required (runs locally or via GitHub Actions)
