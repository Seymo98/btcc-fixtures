#!/usr/bin/env python3
"""
BTCC Play-Cricket API — Phase 0 Validation Tests
==================================================
Confirms API access, data model, cross-club capability, and competition IDs.

Usage:
    python scripts/phase0_tests.py

Reads API key from .env file in the repo root.
Saves raw JSON responses to data/phase0_results/ for inspection.

Ref: Play-Cricket API Strategy v2, Phase 0
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Find repo root (one level up from scripts/)
REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

API_KEY = os.environ.get("PLAY_CRICKET_API_KEY")
BTCC_SITE_ID = int(os.environ.get("BTCC_SITE_ID", 950))
BASE_URL = "https://www.play-cricket.com/api/v2"
OUTPUT_DIR = REPO_ROOT / "data" / "phase0_results"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def api_call(endpoint: str, params: dict) -> tuple[int, dict]:
    """Make a Play-Cricket API call. Returns (status_code, data)."""
    params["api_token"] = API_KEY
    url = f"{BASE_URL}/{endpoint}"

    # Log with key masked
    safe_params = {k: ("***" if k == "api_token" else v) for k, v in params.items()}
    print(f"  GET {endpoint}?{'&'.join(f'{k}={v}' for k, v in safe_params.items())}")

    try:
        resp = requests.get(url, params=params, timeout=30)
        try:
            data = resp.json()
        except requests.exceptions.JSONDecodeError:
            data = {"raw_text": resp.text[:500]}
        return resp.status_code, data
    except requests.exceptions.RequestException as e:
        return 0, {"error": str(e)}


def save_result(name: str, data):
    """Save raw JSON to data/phase0_results/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  → Saved: {path.relative_to(REPO_ROOT)}")


def header(num: int, title: str):
    print(f"\n{'='*60}")
    print(f"TEST {num}: {title}")
    print(f"{'='*60}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def main():
    if not API_KEY:
        print("ERROR: PLAY_CRICKET_API_KEY not found.")
        print("Copy .env.example to .env and add your key.")
        sys.exit(1)

    results = {}
    print(f"BTCC Phase 0 API Validation")
    print(f"Date: {datetime.now().strftime('%d %B %Y %H:%M')}")
    print(f"Site ID: {BTCC_SITE_ID}")
    print(f"Output: {OUTPUT_DIR.relative_to(REPO_ROOT)}/")

    # -- TEST 1: Basic access -----------------------------------------------
    header(1, "Basic access — BTCC 2025 fixtures")
    status, data = api_call("matches.json", {
        "site_id": BTCC_SITE_ID,
        "season": 2025
    })
    save_result("01_btcc_matches_2025", data)

    if status == 200:
        matches = data if isinstance(data, list) else data.get("matches", data)
        count = len(matches) if isinstance(matches, list) else "unknown structure"
        print(f"  ✓ PASS — {count} matches returned")
        results["1_basic_access"] = "PASS"
    else:
        print(f"  ✗ FAIL — HTTP {status}")
        results["1_basic_access"] = f"FAIL ({status})"

    time.sleep(1)

    # -- TEST 2: Teams (extracted from match data) ----------------------------
    header(2, "BTCC teams — extracted from match data")
    # teams.json returns 401 for club-level tokens, but every match record
    # contains home_team_name/home_team_id when BTCC is home, and
    # away_team_name/away_team_id when BTCC is away. Extract from Test 1.

    btcc_teams = {}  # {team_id: team_name}
    try:
        with open(OUTPUT_DIR / "01_btcc_matches_2025.json") as f:
            t1_data = json.load(f)
        mlist = t1_data if isinstance(t1_data, list) else t1_data.get("matches", [])
        for m in mlist:
            # When BTCC is home
            if str(m.get("home_club_id", "")) == str(BTCC_SITE_ID):
                tid = m.get("home_team_id", "")
                tname = m.get("home_team_name", "")
                if tid and tname:
                    btcc_teams[str(tid)] = tname
            # When BTCC is away
            if str(m.get("away_club_id", "")) == str(BTCC_SITE_ID):
                tid = m.get("away_team_id", "")
                tname = m.get("away_team_name", "")
                if tid and tname:
                    btcc_teams[str(tid)] = tname
    except Exception as e:
        print(f"  Could not read Test 1 data: {e}")

    if btcc_teams:
        print(f"  ✓ PASS — {len(btcc_teams)} BTCC teams found in match data:")
        for tid, tname in sorted(btcc_teams.items(), key=lambda x: x[1]):
            print(f"      {tname} (team_id: {tid})")
        save_result("02_btcc_teams", {
            "source": "Extracted from matches.json (teams.json returns 401)",
            "teams": [{"team_id": tid, "team_name": tname}
                      for tid, tname in sorted(btcc_teams.items(), key=lambda x: x[1])]
        })
        results["2_teams"] = f"PASS ({len(btcc_teams)} teams)"
    else:
        print(f"  ✗ FAIL — could not extract team IDs from match data")
        results["2_teams"] = "FAIL (no teams extracted)"

    # -- TEST 3: Result summary (check last_updated) ------------------------
    header(3, "Result summary — last_updated field")
    status, data = api_call("result_summary.json", {
        "site_id": BTCC_SITE_ID,
        "season": 2025
    })
    save_result("03_btcc_results_2025", data)

    match_id = None
    if status == 200:
        rlist = data if isinstance(data, list) else data.get("result_summary", [])
        if isinstance(rlist, list) and len(rlist) > 0:
            first = rlist[0]
            has_lu = "last_updated" in first
            match_id = first.get("id", first.get("match_id"))
            print(f"  ✓ PASS — {len(rlist)} results")
            print(f"    last_updated present: {'YES ✓' if has_lu else 'NO ✗'}")
            print(f"    Sample match_id for Test 4: {match_id}")
            results["3_result_summary"] = "PASS"
        else:
            print(f"  ✓ HTTP 200 but empty — may be off-season")
            results["3_result_summary"] = "PASS (empty)"
    else:
        print(f"  ✗ FAIL — HTTP {status}")
        results["3_result_summary"] = f"FAIL ({status})"

    time.sleep(1)

    # -- TEST 4: Match detail (full scorecard) ------------------------------
    header(4, "Match detail — full scorecard")
    if match_id:
        status, data = api_call("match_detail.json", {"match_id": match_id})
        save_result("04_match_detail", data)

        if status == 200:
            print(f"  ✓ PASS — scorecard retrieved for match {match_id}")
            # Inspect structure
            if isinstance(data, dict):
                top_keys = list(data.keys())
                print(f"    Top-level keys: {', '.join(top_keys[:10])}")
            results["4_match_detail"] = "PASS"
        else:
            print(f"  ✗ FAIL — HTTP {status}")
            results["4_match_detail"] = f"FAIL ({status})"
    else:
        print("  ⊘ SKIPPED — no match_id from Test 3")
        results["4_match_detail"] = "SKIPPED"

    time.sleep(1)

    # -- TEST 5: Players (try multiple URL patterns) -------------------------
    header(5, "Players — registration data")
    # players.json returned 404 — try documented variations
    players_attempts = [
        ("players.json", {"site_id": BTCC_SITE_ID}),
        ("players.json", {"site_id": BTCC_SITE_ID, "include_everyone": "yes"}),
        ("club_players.json", {"site_id": BTCC_SITE_ID}),
    ]

    players_found = False
    for endpoint, params in players_attempts:
        print(f"  Trying: {endpoint} with {params}")
        status, data = api_call(endpoint, params)

        if status == 200:
            players = data if isinstance(data, list) else data.get("players", [])
            if isinstance(players, list) and len(players) > 0:
                save_result("05_btcc_players", data)
                print(f"  ✓ PASS — {len(players)} players via {endpoint}")
                fields = list(players[0].keys()) if isinstance(players[0], dict) else []
                print(f"    Fields: {', '.join(fields[:15])}{'...' if len(fields) > 15 else ''}")
                sensitive = [f for f in fields if any(
                    s in f.lower() for s in
                    ["email", "phone", "address", "dob", "date_of_birth", "mobile"]
                )]
                if sensitive:
                    print(f"    ⚠ SENSITIVE: {', '.join(sensitive)}")
                    print(f"      → Restrict per data exposure policy")
                else:
                    print(f"    No obvious sensitive fields in top-level response")
                results["5_players"] = f"PASS via {endpoint}"
                players_found = True
                break
            elif status == 200:
                print(f"    200 but empty response")
        else:
            print(f"    HTTP {status}")
        time.sleep(1)

    if not players_found:
        # Not a blocker — players data only needed for Phase 3
        print(f"  ✗ No working players endpoint found")
        print(f"    Not a Phase 1 blocker — needed for junior tracking (Phase 3)")
        print(f"    May require ECB helpdesk query re: correct endpoint/params")
        save_result("05_players_attempts", {
            "note": "All players endpoint attempts failed",
            "attempts": [{"endpoint": e, "params": {k: v for k, v in p.items()}}
                         for e, p in players_attempts]
        })
        results["5_players"] = "DEFERRED (not needed until Phase 3)"

    time.sleep(1)

    # -- TEST 6: Cross-club access ------------------------------------------
    header(6, "Cross-club access")

    # Instead of searching clubs.json (which needs an unknown county_id),
    # find an opponent from BTCC's own 2025 matches — guaranteed real club
    print("  Finding an LRCL opponent from BTCC's 2025 fixtures...")
    other_site_id = None
    other_club_name = None

    try:
        with open(OUTPUT_DIR / "01_btcc_matches_2025.json") as f:
            t1_data = json.load(f)
        mlist = t1_data if isinstance(t1_data, list) else t1_data.get("matches", [])
        for m in mlist:
            # Find a league match where BTCC is home (opponent is away)
            if (m.get("competition_type") == "League"
                    and str(m.get("home_club_id", "")) == str(BTCC_SITE_ID)
                    and m.get("away_club_id")):
                other_site_id = m["away_club_id"]
                other_club_name = m.get("away_club_name", "Unknown")
                break
    except Exception as e:
        print(f"  Could not read match data: {e}")

    if not other_site_id:
        # Fallback to the API docs example
        other_site_id = 3540
        other_club_name = "Hunningham CC (API docs example)"
        print(f"  No league opponent found, falling back to {other_club_name}")

    print(f"  Testing: {other_club_name} (site_id: {other_site_id})")

    status, data = api_call("matches.json", {
        "site_id": other_site_id,
        "season": 2025
    })
    save_result("06b_crossclub_matches", data)

    if status == 200:
        matches = data if isinstance(data, list) else data.get("matches", [])
        count = len(matches) if isinstance(matches, list) else "?"
        print(f"  ✓ PASS — {count} matches for {other_club_name}")
        print(f"  ✓ CROSS-CLUB ACCESS CONFIRMED")
        results["6_crossclub"] = f"PASS ({other_club_name})"
    elif status in (401, 403):
        print(f"  ✗ BLOCKED — HTTP {status}")
        results["6_crossclub"] = f"BLOCKED ({status})"
    else:
        print(f"  ? UNEXPECTED — HTTP {status}")
        results["6_crossclub"] = f"UNEXPECTED ({status})"

    time.sleep(1)

    # -- TEST 7: Competition discovery and league tables ---------------------
    header(7, "Competitions, league tables, and season structure")
    try:
        with open(OUTPUT_DIR / "01_btcc_matches_2025.json") as f:
            matches_data = json.load(f)
    except Exception:
        matches_data = None

    # Extract competitions, categorised by type
    comps = {}  # keyed by competition_id
    friendlies = 0
    if matches_data:
        mlist = matches_data if isinstance(matches_data, list) else matches_data.get("matches", [])
        if isinstance(mlist, list):
            for m in mlist:
                comp_type = m.get("competition_type", "")
                comp_name = m.get("competition_name", "")
                comp_id = m.get("competition_id", "")
                league_name = m.get("league_name", "")
                league_id = m.get("league_id", "")
                match_type = m.get("match_type", "")

                if not comp_id:
                    friendlies += 1
                    continue

                if str(comp_id) not in comps:
                    comps[str(comp_id)] = {
                        "competition_name": comp_name,
                        "competition_id": comp_id,
                        "competition_type": comp_type,
                        "league_name": league_name,
                        "league_id": league_id,
                        "match_type": match_type,
                        "match_count": 0
                    }
                comps[str(comp_id)]["match_count"] += 1

    if comps:
        # Separate league comps from cups/other
        leagues = {k: v for k, v in comps.items() if v["competition_type"] == "League"}
        cups = {k: v for k, v in comps.items() if v["competition_type"] != "League"}

        print(f"  {len(comps)} competitions, {friendlies} friendlies\n")

        if leagues:
            print(f"  LEAGUE COMPETITIONS ({len(leagues)}):")
            for cid, c in sorted(leagues.items(), key=lambda x: x[1]["competition_name"]):
                print(f"    • {c['competition_name']} ({c['match_count']} matches)")
                print(f"      comp_id: {cid}, league: {c['league_name']} (id: {c['league_id']})")

        if cups:
            print(f"\n  CUPS & OTHER ({len(cups)}):")
            for cid, c in sorted(cups.items(), key=lambda x: x[1]["competition_name"]):
                print(f"    • {c['competition_name']} [{c['competition_type']}] ({c['match_count']} matches)")
                print(f"      comp_id: {cid}")

        save_result("07_competitions", {
            "leagues": leagues,
            "cups": cups,
            "friendlies_count": friendlies
        })

        # Try league table for each league competition using competition_id
        print(f"\n  Testing league table retrieval:")
        tables_found = 0
        for cid, c in leagues.items():
            time.sleep(1)
            print(f"    {c['competition_name']} (comp_id: {cid})...")

            # The league_table endpoint may accept competition_id or
            # league_id — try both
            for param_name, param_val in [
                ("competition_id", cid),
                ("division_id", cid),
                ("league_id", c["league_id"]),
            ]:
                if not param_val:
                    continue
                lt_status, lt_data = api_call("league_table.json", {
                    param_name: param_val
                })
                if lt_status == 200:
                    lt_content = lt_data if isinstance(lt_data, list) else lt_data.get("league_table", [])
                    if isinstance(lt_content, list) and len(lt_content) > 0:
                        save_result(f"07_league_table_{cid}", lt_data)
                        print(f"      ✓ Table retrieved via {param_name}={param_val} ({len(lt_content)} entries)")
                        tables_found += 1
                        break
                    else:
                        print(f"      200 but empty via {param_name}={param_val}")
                else:
                    print(f"      HTTP {lt_status} via {param_name}={param_val}")
                time.sleep(1)

        results["7_competitions"] = f"PASS ({len(leagues)} leagues, {len(cups)} cups, {tables_found} tables)"
    else:
        print("  Could not extract competition IDs from match data")
        results["7_competitions"] = "MANUAL CHECK NEEDED"

    # Save field inventory — prefer a league match as sample over a friendly
    if matches_data:
        mlist = matches_data if isinstance(matches_data, list) else matches_data.get("matches", [])
        if isinstance(mlist, list) and len(mlist) > 0:
            # Find a league match for a richer sample
            sample = mlist[0]
            for m in mlist:
                if m.get("competition_id"):
                    sample = m
                    break
            save_result("08_match_field_inventory", {
                "note": "Sample match record — league match preferred over friendly",
                "match_type": sample.get("competition_type", "unknown"),
                "fields": list(sample.keys()),
                "sample_record": sample
            })
            print(f"\n  Field inventory saved (sample: {sample.get('competition_name', 'friendly')},"
                  f" {sample.get('match_date', '?')})")

    # -----------------------------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("PHASE 0 SUMMARY")
    print(f"{'='*60}")
    all_pass = True
    for test, result in results.items():
        if "PASS" in result or "DEFERRED" in result:
            icon = "✓" if "PASS" in result else "○"
        elif "FAIL" in result or "BLOCKED" in result:
            icon = "✗"
        else:
            icon = "?"
        print(f"  {icon}  {test}: {result}")
        if "FAIL" in result or "BLOCKED" in result:
            all_pass = False

    print(f"\n  Raw JSON: {OUTPUT_DIR.relative_to(REPO_ROOT)}/")

    if all_pass:
        print(f"\n  ALL TESTS PASSED — Phase 0 complete.")
        print(f"  Proceed to Phase 1 builds.")
    else:
        print(f"\n  SOME ISSUES — review output above before proceeding.")

    # -----------------------------------------------------------------------
    # NEXT ACTIONS
    # -----------------------------------------------------------------------
    print(f"\n{'='*60}")
    print("NEXT ACTIONS")
    print(f"{'='*60}")
    print("  □ Store API key in committee Gmail vault (David + Bridgett)")
    print("  □ Agree data access rules with Emma (safeguarding)")
    print("  □ Record 2026 competition/division IDs when season fixtures published")
    print("  □ Export 2025 native Play-Cricket stats (website → CSV)")
    print("  □ Set up captain's form sheet from CSV exports")
    print("  □ Build Phase 1a: weekend results digest")
    print("  □ Build Phase 1b: iCal fixture feeds")

    # Save summary
    save_result("00_summary", {
        "run_date": datetime.now().isoformat(),
        "site_id": BTCC_SITE_ID,
        "results": results
    })


if __name__ == "__main__":
    main()
