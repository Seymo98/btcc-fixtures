# Play-Cricket API Strategy v2 — Addendum
## Additions Following Cross-Review (Gemini, ChatGPT, v2 reconciliation)

**Date:** 29 March 2026  
**Status:** For incorporation into v2 strategy document  
**Author:** David Seymour, Treasurer, BTCC

---

## A1. Third-Party Platform Context (New Footnote — Section 1)

BTCC does not currently use Spond or Pitchero. However, for completeness and future reference, the following integration characteristics have been documented from the Gemini cross-review:

| Platform | Play-Cricket Integration | Key Limitation | BTCC Relevance |
|----------|------------------------|----------------|----------------|
| **Pitchero** | Daily sync of league fixtures, results, scorecards, league tables. Official ECB partnership. | Does not populate individual player stats into Pitchero player profiles — manual scorecard re-entry required. Cup matches and friendlies excluded from sync. | If Option C (Pitchero + custom data layer) is implemented, the API gives BTCC direct access to the same data with more flexibility and no subscription cost for the data itself. Pitchero handles public display; the API handles everything else. |
| **Spond** | One-time fixture import into Season Planner from Play-Cricket. | Not a live sync — rescheduled, delayed, or cancelled fixtures do not auto-update. Requires manual correction by a volunteer. | Reinforces that the subscribable iCal feed remains a priority build. Even if BTCC adopted Spond for availability management, the iCal feed would still be needed for ongoing fixture updates. |

*Sources: Pitchero Help Centre — [3rd Party Competitions](https://help.pitchero.com/knowledge/3rd-party-powered-competitions), [Scorecards](https://help.pitchero.com/knowledge/scorecards). Spond — [Play-Cricket Import](https://help.spond.com/app/en/articles/158926-how-to-import-match-data-from-play-cricket). All accessed 29 Mar 2026.*

---

## A2. Phase 4 Horizon Items (Additions to Section 5, Phase 4 table)

Two additional use cases identified from the Gemini cross-review, both appropriate for Phase 4 (off-season 2026–27 and beyond):

### A2.1 Pitch Usage Ledger

| Aspect | Detail |
|--------|--------|
| **What** | Digital log of which grass strip was prepared for which fixture, correlated with match scores from the API |
| **Value** | Empirical data on pitch deterioration, average scores per strip, bounce consistency across the season. Evidence base for groundsman decisions on strip rotation and renovation priorities. |
| **Prerequisites** | Clean match data in the data layer (Phase 2); a simple logging mechanism for strip allocation (could be as basic as a column in the groundsman's existing records) |
| **Link to other workstreams** | Connects directly to groundsman app development. If a BTCC grounds management tool is built, pitch usage tracking would be a natural module. |
| **Risk** | Low complexity, low risk. Main constraint is establishing the habit of logging strip allocation — a volunteer adoption challenge, not a technical one. |

### A2.2 Ball-by-Ball Data and Phase Analysis

| Aspect | Detail |
|--------|--------|
| **What** | When matches are scored electronically via PCS Pro or Play-Cricket Scorer, the API may provide access to ball-by-ball data through the Match Detail endpoint. This enables partnership analysis, phase-of-play run rates, dot-ball frequencies, boundary percentages, and powerplay performance. |
| **Value** | Coaching-grade analytics previously only available at county level. Allows targeted training session design based on identified scoring weaknesses (e.g., middle-overs run rate, death-bowling economy). Particularly valuable for a newly promoted Premier Division side facing unfamiliar opposition bowling attacks. |
| **Prerequisites** | Consistent use of electronic scoring across BTCC matches (iPad-based scoring is already in place for 1st XI and 2nd XI). API access confirmed. Phase 2 data layer operational. |
| **Feasibility for Premier Division** | High. Premier Division matches are more likely to be electronically scored than lower divisions. If BTCC's scorers are consistently using Play-Cricket Scorer on the iPads (10th gen and Air 5th gen already available), ball-by-ball data should be available for most home matches and potentially away matches too. |
| **Risk** | Data availability depends on opposition scorers also using electronic scoring for away matches. Home matches under BTCC's control are more reliable. Sample size caveats apply — a few matches' worth of phase analysis is indicative, not definitive. |
| **Backlog position** | Phase 4. Worth prototyping once the data layer is stable and one season's worth of electronically scored matches is available. |

*Source: Gemini deep research output, cross-referenced with Play-Cricket Match Detail API documentation — [Match Detail API](https://play-cricket.ecb.co.uk/hc/en-us/articles/360000141669-Match-Detail-API). Accessed 29 Mar 2026. Ball-by-ball availability within the Match Detail response is [inference] based on the endpoint's documented capability to return detailed innings data when electronic scoring is used; exact payload structure to be confirmed on API token receipt.*

---

## A3. Use Case Prioritisation Matrix (New Section)

This matrix evaluates each proposed use case against four dimensions, using a consistent rating scale. It consolidates and recalibrates the prioritisation work from both the v2 strategy and the Gemini cross-review.

**Rating scale:**
- **Value:** How much pain it removes, revenue it protects, or engagement it drives
- **Complexity:** Technical effort to build and maintain (Simple / Moderate / Complex / Very Complex)
- **Data availability:** Whether the API provides what's needed natively, or external data merging is required
- **Volunteer effort impact:** Whether the tool reduces, is neutral to, or increases volunteer workload

| Use Case | Value | Complexity | Data Availability | Volunteer Effort Impact | Recommended Phase |
|----------|-------|------------|-------------------|------------------------|-------------------|
| **iCal fixture feeds** (per-team, subscribable, auto-updating) | Extremely High | Simple | High — native via Match Summary API | Massive reduction (set-and-forget) | **Phase 1** |
| **Weekend results digest** (WhatsApp/social media formatted) | High | Simple | High — native via Result Summary + Match Detail API | High reduction (eliminates manual compilation) | **Phase 1** |
| **Captain's form sheet** (Google Sheet from native exports) | High | Simple | High — native Play-Cricket stats export, no API needed | High reduction (replaces manual lookup) | **Phase 1** (can do now) |
| **Fixture reminders** (WhatsApp-ready weekly messages) | Medium | Simple | High — native via Match Summary API | Moderate reduction | **Phase 1** |
| **Match fee reconciliation** (played vs paid cross-reference) | Very High | Moderate | Medium — requires Zettle CSV + Match Detail API | Massive reduction (automates treasurer reconciliation) | **Phase 2** |
| **Captain's stats dashboard** (rolling averages, form trends) | High | Moderate | High — computed from Match Detail API | High reduction (replaces manual analysis) | **Phase 2** |
| **Season stats dashboard** (interactive batting/bowling) | High | Moderate | High — computed from Match Detail API | High reduction | **Phase 2** |
| **Auto-drafted match reports** (AI narrative from scorecard) | High | Moderate | High — Match Detail API → Claude | High reduction (generates first draft) | **Phase 3** |
| **Monthly committee data pack** (automated cricket section) | High | Moderate | High — multiple endpoints, computed | High reduction (eliminates manual report assembly) | **Phase 3** |
| **AGM report generator** (season statistics automation) | Medium | Simple | High — native via API | High reduction (eliminates end-of-season crunch) | **Phase 3** |
| **Junior progression tracker** (junior → senior transition) | Medium–High | Moderate | High — Players API + Match Detail cross-reference | Neutral (new capability, not replacing existing process) | **Phase 3** |
| **MCP server integration** (conversational Claude querying) | High | Moderate | High — full API surface via c-m-hunt package | Neutral (new capability) | **Phase 3** |
| **Data quality reviewer** (scorecard reconciliation, duplicate flags) | High | Moderate | High — computed from Match Detail + Players API | Moderate reduction (catches errors before publication) | **Phase 2–3** |
| **Match fee automation** (participation → payment link → tracking) | Very High | Moderate–Complex | Medium — requires API + payment infrastructure + messaging | Massive reduction (end-to-end automation) | **Phase 2–3** (see separate workstream) |
| **Opposition analysis** (pre-match briefings on opponents) | Medium–High | Complex | Low–Medium — cross-club access unconfirmed | Slight increase (requires human review/context layer) | **Phase 4** |
| **League benchmarking dashboard** (BTCC vs Premier peers) | Medium | Moderate | Medium — league site_id + division_ids needed | Neutral | **Phase 4** |
| **Sponsor value reporting** (home match footfall proxies) | Medium | Complex | Low — requires bar data + match data + social metrics | Neutral | **Phase 4** |
| **Pitch usage ledger** (strip allocation vs match scores) | Low–Medium | Simple | Medium — requires manual strip logging + Match Detail | Neutral | **Phase 4** |
| **Ball-by-ball phase analysis** (coaching analytics) | Medium | Moderate | Medium — depends on electronic scoring consistency | Neutral (new coaching capability) | **Phase 4** |
| **Weather-correlated outcomes** (conditions vs results) | Low | Moderate | Low — requires OpenMeteo integration | Neutral | **Phase 4** (fun, not critical) |

**Reading the matrix:**

The strongest cases for early implementation cluster in the top-left: high value, low complexity, high data availability, and significant volunteer effort reduction. The iCal feed, results digest, and match fee reconciliation are the standout cases.

Phase 4 items are characterised by higher complexity, external data dependencies, or lower immediate value. They become worthwhile once the data layer is stable and trusted after a full season.

The match fee automation use case (participation → payment link → tracking) scores very highly on value but involves complexity beyond the Play-Cricket API alone — it requires payment infrastructure and messaging integration. This is flagged as a separate workstream.

---

## A4. Risk Register Addition (Append to Section 4)

The following risk should be added to the existing risk register:

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Gemini/alternative AI analysis over-indexes on restrictions** — External reviews (e.g., Gemini deep research) interpreted ECB's "own data" wording as an absolute block on cross-club API access, recommending opposition analysis be abandoned entirely. The pyplaycricket library's documentation explicitly demonstrates cross-club querying working in practice, and the public Play-Cricket website displays all clubs' data openly. The truth likely sits between "freely permitted" and "absolutely blocked." | Medium | Moderate — could lead to premature abandonment of a genuinely useful capability if the restrictive interpretation is adopted uncritically | Test cross-club access empirically in Phase 0 (first action on token receipt). If the token returns data for other clubs' site_ids, the question is answered. If it returns 401/403, fall back to public website data for key Premier Division matches. Ask ECB support directly if the response is ambiguous. Do not adopt blanket prohibition without evidence. Note: even if API access is restricted, the same data is publicly visible on Play-Cricket's website — the question is automation convenience, not data availability. |

---

## A5. Match Fee Automation — Scoping Note

This is flagged as a separate workstream rather than a subsection of the API strategy, because it crosses multiple systems and involves payment infrastructure decisions beyond the Play-Cricket API.

**The end-to-end workflow:**

1. **Participation confirmed** — Match Detail API confirms who played (batting/bowling/fielding entries in the scorecard)
2. **Payment link generated** — Automated message sent to each player with a payment link (mechanism TBD: bank transfer request, Zettle payment link, or dedicated match fee collection platform)
3. **Payment tracked** — System monitors whether payment has been received within a defined window
4. **Exceptions flagged** — Outstanding fees surfaced to treasurer/captain after the grace period, with running season totals per player

**Key questions for the separate conversation:**

- What payment mechanism? Zettle payment links, bank transfer with reference matching, SumUp, or a dedicated cricket match fee platform?
- Who sends the message — automated system, captain, or treasurer?
- What channel — WhatsApp, SMS, email?
- What's the grace period before chasing?
- How does this interact with seasonal membership vs pay-per-game models?
- Cultural sensitivity — how to avoid making this feel like surveillance or debt collection in a volunteer club?
- GDPR considerations for automated financial messaging?

**Estimated value:** £500–£1,500/season in recovered match fees [inference based on typical club leakage rates], plus 15–20 hours/season of treasurer reconciliation time saved.

---

*Addendum prepared 29 March 2026. For incorporation into BTCC Play-Cricket API Strategy v2.*
