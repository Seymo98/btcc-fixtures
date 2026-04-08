#!/usr/bin/env python3
"""
BTCC Weekend Results Digest — Phase 1a
=======================================
Fetches recent BTCC results from Play-Cricket and formats them for
copy-paste to WhatsApp Communities and social media.

Outputs:
    - Console: WhatsApp-formatted text (copy-paste ready)
    - File: outputs/digests/YYYY-MM-DD_digest.txt

Usage:
    python scripts/results_digest.py                    # Last 7 days
    python scripts/results_digest.py --days 3           # Last 3 days
    python scripts/results_digest.py --date 2025-09-06  # Specific date
    python scripts/results_digest.py --season 2025      # Use 2025 data

Ref: Play-Cricket API Strategy v2, Phase 1a
"""

import os
import sys
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")

API_KEY = os.environ.get("PLAY_CRICKET_API_KEY")
BTCC_SITE_ID = int(os.environ.get("BTCC_SITE_ID", 950))
BASE_URL = "https://www.play-cricket.com/api/v2"
OUTPUT_DIR = REPO_ROOT / "outputs" / "digests"

# Team IDs — same as ical_generator.py
SENIOR_TEAMS = {
    "35112":  "1st XI",
    "35113":  "2nd XI",
    "278687": "Sunday XI",
    "35120":  "Sunday Friendly XI",
    "35119":  "Midweek XI",
}

JUNIOR_TEAMS = {
    "35117":  "Under 11",
    "35116":  "Under 13",
    "262780": "Under 13 B",
    "35115":  "Under 15",
    "35114":  "Under 17",
    "183118": "Under 19",
}

ALL_TEAMS = {**SENIOR_TEAMS, **JUNIOR_TEAMS}

# Display order for the digest
TEAM_ORDER = [
    "35112", "35113", "278687", "35120", "35119",  # seniors
    "35117", "35116", "262780", "35115", "35114", "183118",  # juniors
]


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def fetch_results(season: int, from_date: str = None, to_date: str = None) -> list:
    """Fetch result summaries. Dates in DD/MM/YYYY format."""
    params = {
        "site_id": BTCC_SITE_ID,
        "season": season,
        "api_token": API_KEY,
    }
    if from_date:
        params["from_match_date"] = from_date
    if to_date:
        params["end_match_date"] = to_date

    resp = requests.get(f"{BASE_URL}/result_summary.json", params=params, timeout=30)
    if resp.status_code != 200:
        print(f"  ⚠ result_summary returned HTTP {resp.status_code}")
        return []
    data = resp.json()
    return data if isinstance(data, list) else data.get("result_summary", [])


def fetch_match_detail(match_id) -> dict:
    """Fetch full scorecard for a match."""
    resp = requests.get(f"{BASE_URL}/match_detail.json", params={
        "match_id": match_id,
        "api_token": API_KEY,
    }, timeout=30)
    if resp.status_code != 200:
        return {}
    data = resp.json()
    # match_details is a LIST containing one dict
    if isinstance(data, dict) and "match_details" in data:
        md = data["match_details"]
        if isinstance(md, list) and len(md) > 0:
            return md[0]
        elif isinstance(md, dict):
            return md
    return data


# ---------------------------------------------------------------------------
# Scorecard parsing
# ---------------------------------------------------------------------------

def find_btcc_team(result: dict) -> tuple:
    """Identify which BTCC team played. Returns (team_id, team_name, is_home)."""
    home_cid = str(result.get("home_club_id", ""))
    away_cid = str(result.get("away_club_id", ""))

    if home_cid == str(BTCC_SITE_ID):
        tid = str(result.get("home_team_id", ""))
        return tid, ALL_TEAMS.get(tid, "BTCC"), True
    elif away_cid == str(BTCC_SITE_ID):
        tid = str(result.get("away_team_id", ""))
        return tid, ALL_TEAMS.get(tid, "BTCC"), False
    return None, None, None


def safe_int(val, default=0) -> int:
    """Convert string or int to int safely."""
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def parse_top_performers(detail: dict) -> dict:
    """Extract top batter and bowler from match detail scorecard.

    Structure confirmed from Phase 0:
        detail["innings"] = list of innings dicts
        Each innings has: team_batting_id, bat[], bowl[]
        bat[]: batsman_name, runs (str), balls (str), how_out, fours, sixes
        bowl[]: bowler_name, overs (str), maidens (str), runs (str), wickets (str)

    BTCC batted in innings where team_batting_id matches a BTCC team_id.
    BTCC bowled in innings where team_batting_id does NOT match (opposition batting).
    """
    performers = {"bat": None, "bowl": None}

    if not detail:
        return performers

    innings = detail.get("innings", [])
    if not innings:
        return performers

    btcc_team_ids = set(ALL_TEAMS.keys())
    best_runs = -1
    best_wickets = -1
    best_bowl_runs = 9999

    for inning in innings:
        batting_team = str(inning.get("team_batting_id", ""))
        bat_list = inning.get("bat", [])
        bowl_list = inning.get("bowl", [])

        if batting_team in btcc_team_ids:
            # BTCC batting innings — find top scorer
            for b in bat_list:
                runs = safe_int(b.get("runs"))
                if runs > best_runs:
                    best_runs = runs
                    name = b.get("batsman_name", "?")
                    balls = b.get("balls", "")
                    how_out = str(b.get("how_out", "")).lower().strip()
                    no = "*" if how_out in ("not out", "retired not out") else ""
                    balls_str = f" ({balls}b)" if balls else ""
                    performers["bat"] = f"{name} {runs}{no}{balls_str}"
        else:
            # Opposition batting — BTCC bowled. Find best BTCC bowler.
            for bw in bowl_list:
                wickets = safe_int(bw.get("wickets"))
                runs_conceded = safe_int(bw.get("runs"))
                if (wickets > best_wickets or
                        (wickets == best_wickets and runs_conceded < best_bowl_runs)):
                    best_wickets = wickets
                    best_bowl_runs = runs_conceded
                    overs = bw.get("overs", "")
                    name = bw.get("bowler_name", "?")
                    performers["bowl"] = f"{name} {wickets}-{runs_conceded} ({overs} ov)"

    return performers


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_date_display(date_str: str) -> str:
    """Convert DD/MM/YYYY to readable format."""
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%A %d %B %Y")
    except ValueError:
        return date_str


def format_result_block(result: dict, detail: dict) -> str:
    """Format a single result for WhatsApp."""
    team_id, team_name, is_home = find_btcc_team(result)
    if not team_id:
        return None

    # Opponent
    if is_home:
        opponent = result.get("away_club_name", "") or result.get("away_team_name", "?")
        ha = "Home"
    else:
        opponent = result.get("home_club_name", "") or result.get("home_team_name", "?")
        ha = "Away"

    # Competition
    comp = result.get("competition_name", "")
    if not comp:
        comp = result.get("competition_type", "")

    # Build scores from scorecard detail if available
    scores = ""
    if detail:
        innings = detail.get("innings", [])
        score_parts = []
        for inn in innings:
            team_name_inn = inn.get("team_batting_name", "?")
            runs = inn.get("runs", "")
            wickets = inn.get("wickets", "")
            overs = inn.get("overs", "")
            declared = inn.get("declared", False)
            dec = " dec" if declared else ""
            if runs:
                wkt_str = f"-{wickets}" if wickets and str(wickets) != "10" else ""
                if str(wickets) == "10":
                    wkt_str = " ao"
                ov_str = f" ({overs} ov)" if overs else ""
                score_parts.append(f"{team_name_inn} {runs}{wkt_str}{dec}{ov_str}")
        scores = " | ".join(score_parts)

    # Clean result description — make it BTCC-centric
    result_desc = result.get("result_description", result.get("result", ""))
    # result_applied_to is in detail, not result_summary
    result_applied = str(detail.get("result_applied_to", "")) if detail else ""
    btcc_team_id = str(result.get("home_team_id" if is_home else "away_team_id", ""))
    result_code = detail.get("result", result.get("result", "")) if detail else result.get("result", "")
    if result_code == "W":
        if result_applied == btcc_team_id:
            result_text = "✅ *Won*"
        else:
            result_text = "❌ Lost"
    elif result_code == "T":
        result_text = "🤝 Tied"
    elif result_code == "D":
        result_text = "🤝 Draw"
    elif result_code == "A":
        result_text = "🚫 Abandoned"
    elif result_code == "C":
        result_text = "🚫 Cancelled"
    else:
        result_text = result_desc if result_desc else ""

    # Top performers from detail
    performers = parse_top_performers(detail)

    # Build the block using WhatsApp markdown
    lines = []
    lines.append(f"*{team_name}* vs {opponent} ({ha})")
    if comp:
        lines.append(f"_{comp}_")
    if scores:
        lines.append(scores)
    if result_text:
        lines.append(result_text)
    if performers["bat"]:
        lines.append(f"🏏 {performers['bat']}")
    if performers["bowl"]:
        lines.append(f"🎳 {performers['bowl']}")

    return "\n".join(lines)


def format_digest(results: list, details: dict, date_label: str) -> str:
    """Format the full digest for all results."""
    lines = []
    lines.append(f"🏏 *BTCC Results*")
    lines.append(f"_{date_label}_")
    lines.append("")

    # Group by team in display order
    by_team = {}
    for r in results:
        team_id, _, _ = find_btcc_team(r)
        if team_id:
            by_team.setdefault(team_id, []).append(r)

    blocks_written = 0
    for tid in TEAM_ORDER:
        if tid not in by_team:
            continue
        for r in by_team[tid]:
            mid = str(r.get("id", r.get("match_id", "")))
            detail = details.get(mid, {})
            block = format_result_block(r, detail)
            if block:
                if blocks_written > 0:
                    lines.append("—")
                lines.append(block)
                blocks_written += 1

    if blocks_written == 0:
        lines.append("No BTCC results found for this period.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not API_KEY:
        print("ERROR: PLAY_CRICKET_API_KEY not found in .env")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Generate BTCC results digest")
    parser.add_argument("--season", type=int, default=2026,
                        help="Season year (default: 2026)")
    parser.add_argument("--days", type=int, default=7,
                        help="Look back N days (default: 7)")
    parser.add_argument("--date", type=str, default=None,
                        help="Specific date YYYY-MM-DD (overrides --days)")
    parser.add_argument("--no-detail", action="store_true",
                        help="Skip scorecard fetching (faster, no top performers)")
    parser.add_argument("--limit", type=int, default=20,
                        help="Max scorecards to fetch (default: 20)")
    args = parser.parse_args()

    # Determine date range
    if args.date:
        try:
            target = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print(f"ERROR: Invalid date format '{args.date}' — use YYYY-MM-DD")
            sys.exit(1)
        from_dt = target
        to_dt = target
        date_label = format_date_display(target.strftime("%d/%m/%Y"))
    else:
        to_dt = datetime.now()
        from_dt = to_dt - timedelta(days=args.days)
        if args.days <= 3:
            date_label = f"Weekend {to_dt.strftime('%d %B %Y')}"
        else:
            date_label = f"{from_dt.strftime('%d %b')} — {to_dt.strftime('%d %b %Y')}"

    from_str = from_dt.strftime("%d/%m/%Y")
    to_str = to_dt.strftime("%d/%m/%Y")

    print(f"BTCC Results Digest")
    print(f"Season: {args.season}")
    print(f"Period: {from_str} to {to_str}\n")

    # Fetch results
    print("Fetching results...")
    results = fetch_results(args.season, from_str, to_str)
    print(f"  {len(results)} results found")

    if not results:
        print("\nNo results in this period. Try --days 14 or --season 2025")
        return

    # Fetch match details for top performers (unless --no-detail)
    details = {}
    if args.no_detail:
        print("Skipping scorecards (--no-detail)")
    else:
        to_fetch = results[:args.limit]
        if len(results) > args.limit:
            print(f"Fetching scorecards for first {args.limit} of {len(results)} results (use --limit to change)...")
        else:
            print(f"Fetching {len(to_fetch)} scorecards...")

        import time
        for i, r in enumerate(to_fetch):
            mid = str(r.get("id", r.get("match_id", "")))
            if mid:
                detail = fetch_match_detail(mid)
                if detail:
                    details[mid] = detail
                # Progress indicator
                print(f"  {i+1}/{len(to_fetch)}", end="\r")
                time.sleep(0.5)
        print(f"  {len(details)} scorecards retrieved      \n")

    # Format digest
    digest = format_digest(results, details, date_label)

    # Output to console
    print("=" * 50)
    print("COPY BELOW FOR WHATSAPP:")
    print("=" * 50)
    print()
    print(digest)
    print()
    print("=" * 50)

    # Save to file
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{to_dt.strftime('%Y-%m-%d')}_digest.txt"
    filepath = OUTPUT_DIR / filename
    with open(filepath, "w") as f:
        f.write(digest)
    print(f"\nSaved: {filepath.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
