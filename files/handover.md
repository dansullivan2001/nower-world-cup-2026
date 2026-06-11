# World Cup Score Event — Claude Code Handover
## Mole Valley Orienteering Club — The Nower, 22 June 2026

---

## Project Overview

Dan is organising a score orienteering event on **The Nower** (Dorking, Surrey) as part of the **Mole Valley OC summer series**. The event has a **World Cup 2026 theme**, with a custom progressive scoring system that replaces MapRun's native scoring.

The event is on **Monday 22 June 2026**, starts between **18:30 and 19:30**, 60-minute time limit. The area is small so the format is adjusted to create sufficient distance for faster runners.

---

## Event Format

**31 controls total**, numbered using a deliberate scheme:

| Controls | Numbers | Round | Points each |
|---|---|---|---|
| Group stage (4 groups × 6 controls) | 11–16, 21–26, 31–36, 41–46 | Group | 10 |
| Quarter-finals | 19, 29, 39, 49 | QF | 20 |
| Semi-finals | 79, 89 | SF | 30 |
| Final | 99 | Final | 50 |

The tens digit of group controls identifies the group (11–16 = Group A, 21–26 = Group B, etc.). The "9" suffix on knockout controls (19, 29, 39, 49, 79, 89, 99) is deliberate and thematic.

**Maximum possible score:** 240 (groups) + 80 (QFs) + 60 (SFs) + 50 (Final) = **430 pts**

**Time penalty:** 1 pt per 2 seconds (30 pts/min) over 60 minutes.

---

## Groups and Countries

### Group A — "The Americas Derby"
| No. | Country |
|---|---|
| 11 | Brazil |
| 12 | Argentina |
| 13 | Mexico |
| 14 | Uruguay |
| 15 | USA |
| 16 | Colombia |

### Group B — "Old World, New Blood"
| No. | Country |
|---|---|
| 21 | England |
| 22 | France |
| 23 | Spain |
| 24 | Portugal |
| 25 | Netherlands |
| 26 | Germany |

### Group C — "African Giants"
| No. | Country |
|---|---|
| 31 | Morocco |
| 32 | Senegal |
| 33 | Belgium |
| 34 | Japan |
| 35 | South Korea |
| 36 | Australia |

### Group D — "The Dark Horses"
| No. | Country |
|---|---|
| 41 | Switzerland |
| 42 | Norway |
| 43 | Turkey |
| 44 | Austria |
| 45 | Denmark |
| 46 | Scotland |

---

## Knockout Bracket

```
Group A ──► QF-A (19) ──┐
Group C ──► QF-C (39) ──┴──► SF1 (79) ──┐
                                          ├──► FINAL (99)
Group B ──► QF-B (29) ──┐                │
Group D ──► QF-D (49) ──┴──► SF2 (89) ──┘
```

**Unlock rules:**
- QF unlocks if runner has punched **≥5 controls from its parent group**
- SF1 (79) unlocks if **both QF-A (19) and QF-C (39) scored** (not just punched — locked QFs don't count)
- SF2 (89) unlocks if **both QF-B (29) and QF-D (49) scored**
- Final (99) unlocks if **both SF1 (79) and SF2 (89) scored**

Knockout controls that are punched but not unlocked score **zero**. This is enforced by the scoring script post-hoc; MapRun itself is unaware of the progression rules.

---

## Scoring Script

A Python script (`worldcup_results.py`) has been written and tested. It:

1. Calls the **MapRun public API** to fetch results JSON
2. Parses each runner's `punchControlIds` list
3. Applies group qualification logic and knockout unlock rules
4. Calculates net score with time penalty
5. Outputs a ranked results table to console
6. Optionally exports to CSV (`--csv results.csv`)

**API endpoint used:**
```
https://p.fne.com.au:8886/resultsGetPublicForEventv2?eventName=<Full event name>
```

**Key JSON fields from MapRun API:**
- `punchControlIds` — list of control ID strings punched
- `punchTimeAfterStartSecs` — timestamps in seconds after start (parallel list)
- `TotalTimeSecs` — total elapsed time (integer, for penalty calculation)
- `TotalTimehhmmss` — formatted time string for display
- `Classifier` — "OK", "MP", "DNF" etc.
- `Firstname`, `Surname`, `ClubName`, `Gender`

**Usage:**
```bash
# Test with synthetic demo data
python3 worldcup_results.py --demo --detail

# Live results from MapRun
python3 worldcup_results.py --event "Nower Jun26 MVOC PXAS ScoreQ60"

# With CSV export
python3 worldcup_results.py --event "Nower Jun26 MVOC PXAS ScoreQ60" --csv results.csv

# With detailed per-runner breakdown
python3 worldcup_results.py --event "Nower Jun26 MVOC PXAS ScoreQ60" --detail
```

**Note:** The exact event name string must match the MapRun event file name character for character.

---

## Outstanding Tasks

The following have been discussed but not yet built:

1. **Map overprint / bracket diagram** — The Nower map has a good white space area in the bottom-right. The plan is to overprint a bracket diagram showing:
   - Control number, country name, and a tick box for each group stage control
   - The knockout bracket (which groups feed which QF/SF/Final)
   - This doubles as the runner's tally card during the event
   - Dan uses **Purple Pen** for course setting and map production
   - Map is **1:5,000, 5m contours**, likely printed **A3**

2. **Event briefing text** — Pre-race "commentary" framing the event as a World Cup broadcast. Not yet written.

3. **MapRun event setup** — The event name for MapRun needs to be agreed. Convention is something like:
   `Nower Jun26 MVOC PXAS ScoreQ60`
   Note: MapRun's native ScoreQ scoring will calculate its own results, but these are ignored — the Python script does the actual World Cup scoring post-hoc.

4. **England fixture check** — 22 June falls during the World Cup group stage. Worth checking whether England are playing that evening, as it may affect turnout.

---

## Key Decisions Already Made

- Progression is **self-enforcing via scoring** (not honour system or marshals) — locked controls score zero, checked by script post-hoc
- Qualification threshold: **≥5 controls from a group** to unlock that group's QF
- Groups chosen for interest, not strict adherence to the real 2026 draw (countries reassigned across groups for variety)
- No external Python libraries required — script uses stdlib only (`urllib`, `json`, `csv`, `math`)
- MapRun used purely for GPS punching and result collection; all World Cup scoring logic is external

---

## Files

- `files/worldcup_results.py` — Main scoring script (complete and tested)
- `files/competitor_rules.md` — Full competitor rules sheet
- `files/event-page-wordpress.html` — Website event page (scoring summary only — full rules held back for final details)
- `files/final_details.md` — Final details score-course section with the full scoring rules (publish once course is checked)
- `files/handover.md` — This document
- `index.html` — Live results web page (auto-refreshes every 5 minutes)
- `results.json` — Results data, regenerated by the GitHub Action
- `.github/workflows/fetch-results.yml` — GitHub Action: fetches and publishes results every 5 min on event day

