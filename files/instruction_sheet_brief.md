# Design brief — The Nower World Cup 2026 competitor instruction sheet

> Paste everything below the line into Claude (the design / artifact tool) to
> generate the on-the-day instruction sheet. It is self-contained: every fact,
> number and example the design needs is included, so the tool should not
> invent any rules. A ready-made progression diagram already exists at
> `files/bracket_diagram.svg` (and `.png`) if you would rather drop that in
> than have the tool redraw it.

---

## What I need you to design

A **single-page, print-ready competitor instruction sheet** for a World Cup–themed
score orienteering event, to be handed out at registration and read on the day.
Design for **A5 portrait** (so two copies fit on an A4 sheet), but keep the layout
robust enough to scale to A4. It must be **black-and-white-printer friendly** —
use the colour palette below for screen/colour print, but make sure every element
still reads clearly in greyscale (rely on shape, weight and borders, not colour alone).

**Audience & context:** orienteers of mixed experience, reading quickly at the
start in evening daylight. Clarity and at-a-glance hierarchy matter far more than
decoration. The single most important thing a runner must take away is the
*progression logic* — what unlocks what — because they have to hold their progress
in their head during the run.

**Tone:** crisp and confident, with a light World Cup broadcast flavour in headings
only (e.g. "THE GROUP STAGE", "THE KNOCKOUTS", "LIFTING THE TROPHY"). Do not let
the theme get in the way of legibility.

**Palette (to match the event's results page and map):**
- Dark green `#0d2b0d`, mid green `#1a5c1a`
- Gold `#ffd700`, dim gold `#c9a227`
- Penalty/warning red `#c0392b`
- Neutral text near-black on white

**Suggested layout / sections (in priority order):**
1. **Title block** — "THE NOWER WORLD CUP 2026", subtitle "Mole Valley Orienteering Club · Monday 22 June 2026 · 60-minute score". One-line hook: *"Thirty-one controls. Sixty minutes. One champion."*
2. **How it works** — three or four lines (the format paragraph below).
3. **Points table** — the controls/points table below.
4. **The progression diagram** — the bracket (described below). Give this real estate; it is the heart of the sheet.
5. **The rules** — group qualification, knockout unlocking, the "qualify first" timing rule, scoring of locked controls.
6. **Worked examples** — 3–4 short scenarios in a sidebar or boxes (provided below).
7. **Time penalty** — a small, visually distinct warning box.
8. **Footer strip** — max score 430; results are processed after the event so the app's on-the-day score may differ; good luck line.

---

## CONTENT — use these facts and wording (do not change the numbers)

### The format
This is a **60-minute score event**. There is no set course: the map shows
**31 controls** and you choose which and how many to visit, in any order. You score
points for valid controls and lose points if you finish after 60 minutes. Controls
are organised like the World Cup — a **group stage**, then **knockout rounds**
(quarter-finals, semi-finals, a Final). Knockout controls are worth more but only
score once you have **qualified** for them.

### Controls and points
| Stage | Controls | Points each |
|---|---|---|
| Group A — *The Americas Derby* | 11, 12, 13, 14, 15, 16 | 10 |
| Group B — *Old World, New Blood* | 21, 22, 23, 24, 25, 26 | 10 |
| Group C — *African Giants* | 31, 32, 33, 34, 35, 36 | 10 |
| Group D — *The Dark Horses* | 41, 42, 43, 44, 45, 46 | 10 |
| Quarter-finals | 19, 29, 39, 49 | 20 |
| Semi-finals | 79, 89 | 30 |
| Final | 99 | 50 |

**Maximum possible score: 430 points** (240 group + 80 QF + 60 SF + 50 Final).

### The progression rules
- **Qualify for a quarter-final:** visit **at least 5 of the 6 controls** in its group.
  - QF **19** ← 5 of Group A (11–16)
  - QF **29** ← 5 of Group B (21–26)
  - QF **39** ← 5 of Group C (31–36)
  - QF **49** ← 5 of Group D (41–46)
- **Qualify for a semi-final:** score **both** of its quarter-finals.
  - SF **79** ← QF 19 **and** QF 39 *(the A + C half)*
  - SF **89** ← QF 29 **and** QF 49 *(the B + D half)*
- **Qualify for the Final:** score **both** semi-finals.
  - Final **99** ← SF 79 **and** SF 89
- **"Scored" means punched *and* unlocked.** A locked quarter-final does not count
  towards a semi-final.
- **Locked controls score zero.** If you punch a knockout control you haven't
  qualified for, the app still beeps and records the visit, but it scores **0**.
- **Order matters.** You must qualify **before** you punch the knockout control.
  If you punch it too early it scores nothing — but you may **return to it later**
  once you've qualified, and it will then count.
- Qualification is checked automatically when results are processed **after** the
  event, so the raw score shown in the MapRun app on the day may **differ** from
  the official result.

### Time penalty
You have **60 minutes** from your own start. Finishing late costs **1 point per
2 seconds** over the limit — that's **30 points per minute**. Example: finishing
at **61:30** is 90 seconds late = **−45 points** (more than a whole quarter-final).
A late finish can wipe out an entire knockout round — plan your route to get back
in time.

---

## THE PROGRESSION DIAGRAM — draw this

A left-to-right bracket. **Order the four groups top-to-bottom as A, C, B, D** so the
lines feeding the semi-finals don't cross. Flow:

```
GROUP A (11–16) ─[any 5 of 6]→ QF 19 (20) ┐
                                            ├─→ SEMI 79 (30) ┐
GROUP C (31–36) ─[any 5 of 6]→ QF 39 (20) ┘                 │
                                                              ├─→ FINAL 99 (50)
GROUP B (21–26) ─[any 5 of 6]→ QF 29 (20) ┐                 │
                                            ├─→ SEMI 89 (30) ┘
GROUP D (41–46) ─[any 5 of 6]→ QF 49 (20) ┘
```

Label each arrow into a QF with **"any 5 of 6"**. Label each knockout box with its
control number and points (QF = 20, SF = 30, Final = 50). Under each semi note its
requirement ("needs 19 + 39", "needs 29 + 49"); under the Final note "needs 79 + 89".
Style: groups in green, QFs in bronze/amber, semis in silver/grey, the Final in gold
and visually the biggest. Add a one-line caption: *"Locked knockout controls score
0 — qualify first, then punch."*

---

## WORKED EXAMPLES — include as short boxed scenarios

**1. The complete run (maximum).** Visit all 6 controls in every group (24 × 10 =
240), which qualifies all four quarter-finals; punch all four QFs (+80), both
semis (+60) and the Final (+50). Finish inside the hour: **430 points** — the
perfect tournament.

**2. Five is enough.** You visit **5** of Group A's controls (50 pts) — that's enough
to unlock QF 19, so you punch it for **+20**. The 6th control would add 10 more but
isn't needed to qualify. Five qualifies; six just scores an extra ten.

**3. One short = locked.** You collect all of Group A (qualify) but only **4** of
Group C. QF 19 scores, but QF 39 stays **locked (0)**. Because Semi 79 needs *both*
19 **and** 39, your semi-final is locked too — even if you punch it. One missing
group control can cost you a whole half of the bracket.

**4. Right control, wrong time.** You reach QF 19 after only 4 Group-A controls — it
beeps but scores **0**. You then pick up your 5th Group-A control (now qualified)
and **return to 19**, which this time scores **+20**. Punch order matters: qualify
first, or come back.

**To lift the trophy** you need 5-of-6 from **all four** groups (≥20 group controls),
all four QFs, both semis and the Final — a balanced route across the whole map, not
a deep dive into one corner.

---

## Footer line
*Results are calculated after the event with the World Cup progression rules; the
MapRun app's live score is provisional. Max score 430. Good luck — the world is
watching.*
