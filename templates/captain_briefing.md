# Captain's Form Briefing — Template
#
# Used by Claude (Phase 3) to generate plain-English form summaries.
# Fed into a prompt with recent innings/bowling data per player.
#
# Design principle: DESCRIBE, don't RANK. This is decision support
# for captains, not an automated selection tool.

---

## {team_name} — Form Summary
### Week ending {date}

**Recent form across the squad:**

{player_narratives}

**Key numbers:**
- Matches played this season: {matches_played}
- Current league position: {league_position}
- Next fixture: {next_opponent} ({home_or_away}), {next_date}

---

# Instructions for Claude prompt:
# - Describe each player's recent form in 1-2 sentences
# - Always show sample size ("in 4 innings this season")
# - Never say "should be selected" or "should be dropped"
# - Flag workload concerns (e.g., bowlers with high overs)
# - Note players who haven't been available recently
# - Tone: factual, supportive, captain-to-captain
