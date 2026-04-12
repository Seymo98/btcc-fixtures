#!/usr/bin/env python3
"""
BTCC iCal Fixture Feed Generator — Phase 1b
=============================================
Generates subscribable .ics calendar files per team from Play-Cricket API.

Members subscribe once in their phone/calendar app; fixtures auto-update
when this script re-runs. Post-match, events are updated with results.

Outputs to outputs/feeds/:
    btcc-all.ics        — all senior teams
    btcc-1stxi.ics      — 1st XI only
    btcc-2ndxi.ics      — 2nd XI only
    btcc-sunday.ics     — Sunday XI
    btcc-midweek.ics    — Midweek XI
    btcc-juniors.ics    — all junior teams

Usage:
    python scripts/ical_generator.py                  # 2026 season (default)
    python scripts/ical_generator.py --season 2025    # specific season

Designed to run daily via cron or GitHub Actions.

Ref: Play-Cricket API Strategy v2, Section 6
"""

import os
import sys
import argparse
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
OUTPUT_DIR = REPO_ROOT / "outputs" / "feeds"

# Team IDs confirmed from Phase 0 (stable across seasons)
SENIOR_TEAMS = {
    "35112":  {"name": "1st XI",              "feed": "btcc-1stxi",   "duration_hrs": 7.5},
    "35113":  {"name": "2nd XI",              "feed": "btcc-2ndxi",   "duration_hrs": 7.5},
    "278687": {"name": "Sunday XI",           "feed": "btcc-sunday",  "duration_hrs": 5.5},
    "35120":  {"name": "Sunday Friendly XI",  "feed": "btcc-sunday",  "duration_hrs": 5.5},
    "35119":  {"name": "Midweek XI",          "feed": "btcc-midweek", "duration_hrs": 3.0},
    }

JUNIOR_TEAMS = {
    "35117":  {"name": "Under 11"},
    "35116":  {"name": "Under 13"},
    "262780": {"name": "Under 13 B"},
    "35115":  {"name": "Under 15"},
    "35114":  {"name": "Under 17"},
    "183118": {"name": "Under 19"},
}

DEFAULT_DURATION_HRS = {
    "junior": 2.5,
    "fallback": 5.0,
}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def fetch_matches(season: int) -> list:
    """Fetch all BTCC matches for a season."""
    resp = requests.get(f"{BASE_URL}/matches.json", params={
        "site_id": BTCC_SITE_ID,
        "season": season,
        "api_token": API_KEY,
    }, timeout=30)
    if resp.status_code != 200:
        print(f"  ⚠ matches.json returned HTTP {resp.status_code}")
        return []
    data = resp.json()
    return data if isinstance(data, list) else data.get("matches", [])


def fetch_results(season: int) -> dict:
    """Fetch result summaries, keyed by match id string."""
    resp = requests.get(f"{BASE_URL}/result_summary.json", params={
        "site_id": BTCC_SITE_ID,
        "season": season,
        "api_token": API_KEY,
    }, timeout=30)
    if resp.status_code != 200:
        return {}
    data = resp.json()
    rlist = data if isinstance(data, list) else data.get("result_summary", [])
    return {str(r.get("id", r.get("match_id", ""))): r for r in rlist}


# ---------------------------------------------------------------------------
# Date/time parsing
# ---------------------------------------------------------------------------

def parse_pc_date(date_str: str):
    """Parse Play-Cricket DD/MM/YYYY date. Returns datetime or None."""
    if not date_str:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_pc_time(time_str: str) -> tuple:
    """Parse HH:MM. Returns (hour, minute). Default (12, 0)."""
    if not time_str or ":" not in time_str:
        return (12, 0)
    try:
        h, m = time_str.strip().split(":")[:2]
        return (int(h), int(m))
    except (ValueError, IndexError):
        return (12, 0)


# ---------------------------------------------------------------------------
# iCal generation (RFC 5545)
# ---------------------------------------------------------------------------

def escape_ical(text: str) -> str:
    """Escape special characters per RFC 5545."""
    if not text:
        return ""
    return (text
            .replace("\\", "\\\\")
            .replace(";", "\\;")
            .replace(",", "\\,")
            .replace("\n", "\\n"))


def is_btcc_home(match: dict) -> bool:
    return str(match.get("home_club_id", "")) == str(BTCC_SITE_ID)


def get_duration_hrs(team_id: str, match: dict) -> float:
    """Determine match duration in hours."""
    match_type = match.get("match_type", "")
    if "T20" in match_type or "Twenty" in match_type:
        return 3.0
    if team_id in SENIOR_TEAMS:
        return SENIOR_TEAMS[team_id]["duration_hrs"]
    if team_id in JUNIOR_TEAMS:
        return DEFAULT_DURATION_HRS["junior"]
    return DEFAULT_DURATION_HRS["fallback"]


def build_summary(match: dict, team_name: str, result: dict = None) -> str:
    """Event title: BTCC 1st XI vs Opponent Club (H) — Result."""
    if is_btcc_home(match):
        # Use club name for opponent — team_name is just "1st XI" etc.
        opp = match.get("away_club_name", "") or match.get("away_team_name", "TBC")
        ha = "(H)"
    else:
        opp = match.get("home_club_name", "") or match.get("home_team_name", "TBC")
        ha = "(A)"

    summary = f"BTCC {team_name} vs {opp} {ha}"

    if result:
        rdesc = result.get("result_description", result.get("result", ""))
        if rdesc:
            summary += f" — {rdesc}"

    return summary


def build_description(match: dict, result: dict = None) -> str:
    """Event description: competition, ground, result details.
    Uses real newlines — escape_ical converts them to iCal \\n sequences."""
    parts = []
    comp = match.get("competition_name", "")
    if comp:
        parts.append(comp)
    elif match.get("competition_type", ""):
        parts.append(match["competition_type"])

    ground = match.get("ground_name", "")
    if ground:
        parts.append(ground)

    if result:
        rdesc = result.get("result_description", result.get("result", ""))
        if rdesc:
            parts.append(f"Result: {rdesc}")

    return "\n".join(parts)


def match_to_vevent(match: dict, team_id: str, team_name: str,
                    result: dict = None) -> str:
    """Convert a Play-Cricket match to an RFC 5545 VEVENT block."""
    match_id = match.get("id", "")
    if not match_id:
        return None

    dt = parse_pc_date(match.get("match_date", ""))
    if not dt:
        return None

    match_time = match.get("match_time", "")
    h, m = parse_pc_time(match_time)

    # If no time specified, use sensible defaults by team/day
    if not match_time:
        if team_id in JUNIOR_TEAMS:
            if dt.weekday() == 6:  # Sunday
                h, m = 10, 0
            else:  # Weekday
                h, m = 18, 0
        elif dt.weekday() < 5:  # Weekday senior = evening T20/midweek
            h, m = 18, 0

    dt_start = dt.replace(hour=h, minute=m)
    dt_end = dt_start + timedelta(hours=get_duration_hrs(team_id, match))

    ts_fmt = "%Y%m%dT%H%M%S"
    lu = parse_pc_date(match.get("last_updated", ""))
    dtstamp = (lu or datetime.now()).strftime(ts_fmt)

    # Sequence increments when result is added — forces calendar refresh
    sequence = 1 if result else 0

    # Status
    raw_status = match.get("status", "").lower()
    ical_status = "CANCELLED" if raw_status in ("cancelled", "canceled") else "CONFIRMED"

    summary = escape_ical(build_summary(match, team_name, result))
    description = escape_ical(build_description(match, result))
    location = escape_ical(match.get("ground_name", ""))
    lat = match.get("ground_latitude", "")
    lon = match.get("ground_longitude", "")

    lines = [
        "BEGIN:VEVENT",
        f"UID:playcricket-{match_id}@btcc.org.uk",
        f"DTSTAMP;TZID=Europe/London:{dtstamp}",
        f"DTSTART;TZID=Europe/London:{dt_start.strftime(ts_fmt)}",
        f"DTEND;TZID=Europe/London:{dt_end.strftime(ts_fmt)}",
        f"SUMMARY:{summary}",
    ]
    if description:
        lines.append(f"DESCRIPTION:{description}")
    if location:
        lines.append(f"LOCATION:{location}")
    if lat and lon:
        lines.append(f"GEO:{lat};{lon}")
    lines.append(f"STATUS:{ical_status}")
    lines.append(f"SEQUENCE:{sequence}")
    lines.append("END:VEVENT")

    return "\r\n".join(lines)


def build_vcalendar(events: list, cal_name: str) -> str:
    """Wrap VEVENT blocks in a VCALENDAR with VTIMEZONE."""
    header = "\r\n".join([
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//BTCC//Fixture Feed//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{escape_ical(cal_name)}",
        "X-WR-TIMEZONE:Europe/London",
        "BEGIN:VTIMEZONE",
        "TZID:Europe/London",
        "BEGIN:DAYLIGHT",
        "TZOFFSETFROM:+0000",
        "TZOFFSETTO:+0100",
        "TZNAME:BST",
        "DTSTART:19700329T010000",
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
        "END:DAYLIGHT",
        "BEGIN:STANDARD",
        "TZOFFSETFROM:+0100",
        "TZOFFSETTO:+0000",
        "TZNAME:GMT",
        "DTSTART:19701025T020000",
        "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
        "END:STANDARD",
        "END:VTIMEZONE",
    ])

    return header + "\r\n" + "\r\n".join(events) + "\r\n" + "END:VCALENDAR"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate_feeds(season: int):
    """Fetch data and write all .ics feeds."""
    print(f"BTCC iCal Feed Generator")
    print(f"Season: {season}")
    print(f"Output: {OUTPUT_DIR.relative_to(REPO_ROOT)}/\n")

    print("Fetching matches...")
    matches = fetch_matches(season)
    print(f"  {len(matches)} matches")

    print("Fetching results...")
    results = fetch_results(season)
    print(f"  {len(results)} results\n")

    # Group matches by BTCC team_id
    by_team = {}
    for m in matches:
        if str(m.get("home_club_id", "")) == str(BTCC_SITE_ID):
            tid = str(m.get("home_team_id", ""))
        elif str(m.get("away_club_id", "")) == str(BTCC_SITE_ID):
            tid = str(m.get("away_team_id", ""))
        else:
            continue
        by_team.setdefault(tid, []).append(m)

    # Print breakdown
    all_teams = {**SENIOR_TEAMS, **{k: v for k, v in JUNIOR_TEAMS.items()}}
    print("Matches by team:")
    for tid in sorted(by_team, key=lambda t: all_teams.get(t, {}).get("name", t)):
        name = all_teams.get(tid, {}).get("name", f"Unknown ({tid})")
        print(f"  {name}: {len(by_team[tid])}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = []

    def write_feed(filename: str, cal_name: str, team_ids: list):
        """Generate events for given teams and write .ics file."""
        events = []
        for tid in team_ids:
            tname = all_teams.get(tid, {}).get("name", tid)
            for m in by_team.get(tid, []):
                mid = str(m.get("id", ""))
                vevent = match_to_vevent(m, tid, tname, results.get(mid))
                if vevent:
                    events.append(vevent)
        if events:
            path = OUTPUT_DIR / filename
            with open(path, "w", newline="") as f:
                f.write(build_vcalendar(events, cal_name))
            written.append(filename)
            print(f"  ✓ {filename}: {len(events)} events")
        else:
            print(f"  ○ {filename}: no events — skipped")

    print(f"\nGenerating feeds:")

    # Individual senior feeds — group teams that share a feed filename
    feeds = {}
    for tid, cfg in SENIOR_TEAMS.items():
        feed_name = cfg["feed"]
        if feed_name not in feeds:
            feeds[feed_name] = {"name": cfg["name"], "team_ids": []}
        feeds[feed_name]["team_ids"].append(tid)

    for feed_name, feed_cfg in feeds.items():
        write_feed(f"{feed_name}.ics",
                   f"BTCC {feed_cfg['name']} {season}",
                   feed_cfg["team_ids"])

    # Combined seniors
    write_feed("btcc-seniors.ics", f"BTCC Senior Fixtures {season}",
               list(SENIOR_TEAMS.keys()))

    # Combined juniors
    write_feed("btcc-juniors.ics", f"BTCC Junior Fixtures {season}",
               list(JUNIOR_TEAMS.keys()))

    # Summary
    print(f"\n{'='*50}")
    print(f"{len(written)} feeds written to {OUTPUT_DIR.relative_to(REPO_ROOT)}/")
    print(f"\nNext steps:")
    print(f"  1. Open a .ics file to test in your calendar app")
    print(f"  2. For subscribable feeds, host on GitHub Pages")
    print(f"  3. Re-run daily to pick up results and changes")
    print(f"{'='*50}")


def main():
    if not API_KEY:
        print("ERROR: PLAY_CRICKET_API_KEY not found in .env")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Generate BTCC iCal fixture feeds")
    parser.add_argument("--season", type=int, default=2026,
                        help="Season year (default: 2026)")
    args = parser.parse_args()

    generate_feeds(args.season)


if __name__ == "__main__":
    main()
