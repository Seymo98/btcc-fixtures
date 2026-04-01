# Weekend Results Digest — WhatsApp Template
#
# This template is used by results_digest.py (Phase 1a) to format
# BTCC weekend results for posting to WhatsApp Communities.
#
# Variables are filled from the Play-Cricket Result Summary API.
# The script generates the text; a human copy-pastes to WhatsApp.

---

🏏 *BTCC Weekend Results*
_{date}_

*{team_name}*
{competition}
{home_team} vs {away_team}
{result_summary}

🏅 Batting: {top_batter} — {top_batter_runs} ({top_batter_balls} balls)
🎳 Bowling: {top_bowler} — {top_bowler_figures}

---

# Notes:
# - Emoji usage is deliberate — WhatsApp renders them well
# - Bold (*text*) and italic (_text_) use WhatsApp markdown
# - One block per team, repeated for each XI that played
# - Human reviews before posting — never auto-send
