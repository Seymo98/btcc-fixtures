#!/usr/bin/env python3
"""
BTCC Data Layer Sync — Phase 2
================================
Incremental sync from Play-Cricket API to local SQLite database.

Architecture:
    Play-Cricket API → sync.py → data/btcc.db (SQLite)
                                    ├── matches
                                    ├── results
                                    ├── batting_innings
                                    ├── bowling_spells
                                    ├── players
                                    ├── league_tables
                                    └── data_quality_flags

Design principles:
    1. Raw/clean separation (staging → serving tables)
    2. Incremental sync via last_updated field
    3. Data quality checks on every sync
    4. Season-aware (competition IDs remapped annually)

Status: PLACEHOLDER — build during season (May–Sep 2026).

Usage:
    python scripts/sync.py                # Incremental sync
    python scripts/sync.py --full         # Full re-sync (season start)
    python scripts/sync.py --check-only   # Data quality report only
"""

# TODO: Implement during Phase 2
# Requires: Phase 0 complete, Phase 1 operational, season underway

raise NotImplementedError("Phase 2 — build during 2026 season")
