#!/usr/bin/env python3
"""
World Cup Score Event - Results Processor
Mole Valley Orienteering Club - The Nower, 22 June 2026

Fetches results from the MapRun API and applies World Cup scoring rules:
  - Group stage controls: 10 pts each (groups A/B/C/D, 6 controls each)
  - Quarter-final controls: 20 pts each (unlocked if >=3 from parent group)
  - Semi-final controls: 30 pts each (unlocked if both QFs in the half scored)
  - Final control: 50 pts (unlocked if both SFs scored)
  - Time penalty: -10 pts per minute (or part thereof) over 60 minutes

Usage:
    python3 worldcup_results.py --event "Nower Jun26 MVOC PXAS ScoreQ60"
    python3 worldcup_results.py --demo   (runs with synthetic test data)
"""

import argparse
import json
import math
import sys
import urllib.request
import urllib.parse
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Event configuration
# ---------------------------------------------------------------------------

TIME_LIMIT_SECS = 60 * 60          # 60 minutes
PENALTY_PER_MIN = 10                # points deducted per minute (or part) over

# Group stage: control number -> (group, country)
GROUP_CONTROLS = {
    # Group A — The Americas Derby
    11: ("A", "Brazil"),
    12: ("A", "Argentina"),
    13: ("A", "Mexico"),
    14: ("A", "Uruguay"),
    15: ("A", "USA"),
    16: ("A", "Colombia"),
    # Group B — Old World, New Blood
    21: ("B", "England"),
    22: ("B", "France"),
    23: ("B", "Spain"),
    24: ("B", "Portugal"),
    25: ("B", "Netherlands"),
    26: ("B", "Germany"),
    # Group C — African Giants
    31: ("C", "Morocco"),
    32: ("C", "Senegal"),
    33: ("C", "Belgium"),
    34: ("C", "Japan"),
    35: ("C", "South Korea"),
    36: ("C", "Australia"),
    # Group D — The Dark Horses
    41: ("D", "Switzerland"),
    42: ("D", "Norway"),
    43: ("D", "Turkey"),
    44: ("D", "Austria"),
    45: ("D", "Denmark"),
    46: ("D", "Scotland"),
}

# Knockout controls: control number -> (round, label, parent_groups)
# parent_groups: which groups must be qualified (QF) or which QFs must be scored (SF/Final)
KNOCKOUT_CONTROLS = {
    19: ("QF", "QF-A", ["A"]),        # unlocked if qualified from Group A
    29: ("QF", "QF-B", ["B"]),        # unlocked if qualified from Group B
    39: ("QF", "QF-C", ["C"]),        # unlocked if qualified from Group C
    49: ("QF", "QF-D", ["D"]),        # unlocked if qualified from Group D
    59: ("SF", "SF1",  [19, 29]),     # unlocked if QF-A and QF-B both scored
    69: ("SF", "SF2",  [39, 49]),     # unlocked if QF-C and QF-D both scored
    99: ("F",  "Final",[59, 69]),     # unlocked if SF1 and SF2 both scored
}

POINTS = {
    "group": 10,
    "QF":    20,
    "SF":    30,
    "F":     50,
}

QUALIFY_THRESHOLD = 3   # controls needed from a group to unlock that group's QF

# ---------------------------------------------------------------------------
# Scoring engine
# ---------------------------------------------------------------------------

def score_runner(punch_ids_str):
    """
    Given an ordered list of control ID strings (from MapRun API),
    return a detailed scoring breakdown dict.

    Controls are processed in punch order. Duplicate punches are resolved by
    first-occurrence-wins (subsequent punches of the same control are ignored).
    A knockout control only scores if its prerequisites were already satisfied
    at the moment it was punched.
    """
    # Group controls: deduplicate by first occurrence — protects against accidental
    # re-punches when a control lies on the route back.
    # Knockout controls: re-punchable. Each punch gets a fresh eligibility check;
    # once scored it is skipped on any later re-punch. This lets a runner who
    # visits a QF before qualifying return to it after earning qualification.
    seen_group = set()

    group_hits = {"A": [], "B": [], "C": [], "D": []}
    qualified  = {"A": False, "B": False, "C": False, "D": False}
    group_pts  = 0
    group_detail = []

    scored_knockouts = set()
    ko_punched       = set()   # all knockout controls punched at least once
    knockout_pts     = 0

    for c in punch_ids_str:
        ctrl = int(c.split()[0])

        if ctrl in GROUP_CONTROLS:
            if ctrl not in seen_group:
                seen_group.add(ctrl)
                grp, country = GROUP_CONTROLS[ctrl]
                group_hits[grp].append(ctrl)
                group_pts += POINTS["group"]
                group_detail.append(f"{ctrl} {country}")
                if len(group_hits[grp]) >= QUALIFY_THRESHOLD:
                    qualified[grp] = True

        elif ctrl in KNOCKOUT_CONTROLS:
            ko_punched.add(ctrl)
            if ctrl not in scored_knockouts:
                round_type, label, parents = KNOCKOUT_CONTROLS[ctrl]
                if round_type == "QF":
                    unlocked = all(qualified[g] for g in parents)
                else:
                    # SF / Final: parent knockout controls must already be scored
                    unlocked = all(p in scored_knockouts for p in parents)

                if unlocked:
                    scored_knockouts.add(ctrl)
                    knockout_pts += POINTS[round_type]

    # Build knockout detail in canonical bracket order, one entry per control
    knockout_detail = []
    for ctrl in [19, 29, 39, 49, 59, 69, 99]:
        if ctrl in ko_punched:
            round_type, label, _ = KNOCKOUT_CONTROLS[ctrl]
            if ctrl in scored_knockouts:
                knockout_detail.append(f"{ctrl} {label} +{POINTS[round_type]}")
            else:
                knockout_detail.append(f"{ctrl} {label} LOCKED (0)")

    return {
        "group_pts":        group_pts,
        "knockout_pts":     knockout_pts,
        "raw_score":        group_pts + knockout_pts,
        "group_hits":       group_hits,
        "qualified":        qualified,
        "scored_knockouts": scored_knockouts,
        "group_detail":     group_detail,
        "knockout_detail":  knockout_detail,
    }


def apply_penalty(raw_score, total_time_secs):
    """Apply time penalty and return (net_score, penalty_pts, overtime_secs)."""
    overtime = max(0, total_time_secs - TIME_LIMIT_SECS)
    if overtime == 0:
        return raw_score, 0, 0
    # Ceiling: any part of a minute counts
    overtime_mins = math.ceil(overtime / 60)
    penalty = overtime_mins * PENALTY_PER_MIN
    net = max(0, raw_score - penalty)
    return net, penalty, overtime


def process_results(api_results):
    """Process a list of runner dicts from the MapRun API."""
    processed = []
    for r in api_results:
        if r.get("Classifier") not in ("OK", None, ""):
            # Include DNF etc but flag them
            pass

        punch_ids = r.get("punchControlIds", [])
        breakdown = score_runner(punch_ids)

        total_secs = r.get("TotalTimeSecs", 0)
        net_score, penalty, overtime = apply_penalty(
            breakdown["raw_score"], total_secs
        )

        processed.append({
            "name":          f"{r.get('Firstname', '')} {r.get('Surname', '')}".strip(),
            "club":          r.get("ClubName", ""),
            "classifier":    r.get("Classifier", ""),
            "start_local":   r.get("StartPunchTimeLocal", ""),
            "finish_local":  r.get("FinishPunchTimeLocal", ""),
            "total_time":    r.get("TotalTimehhmmss", ""),
            "total_secs":    total_secs,
            "group_pts":     breakdown["group_pts"],
            "knockout_pts":  breakdown["knockout_pts"],
            "raw_score":     breakdown["raw_score"],
            "penalty":       penalty,
            "overtime_secs": overtime,
            "net_score":     net_score,
            "qualified":     breakdown["qualified"],
            "scored_knockouts": breakdown["scored_knockouts"],
            "group_detail":  breakdown["group_detail"],
            "knockout_detail": breakdown["knockout_detail"],
            "group_hits":    breakdown["group_hits"],
        })

    # Sort: net score descending, then time ascending
    processed.sort(key=lambda x: (-x["net_score"], x["total_secs"]))
    return processed


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def format_results_table(processed):
    """Return a formatted results table as a string."""
    lines = []
    lines.append("=" * 80)
    lines.append("WORLD CUP SCORE EVENT — THE NOWER — MOLE VALLEY OC")
    lines.append(f"Results generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    lines.append("=" * 80)
    lines.append(
        f"{'Pos':<4} {'Name':<22} {'Club':<8} {'Time':<9} "
        f"{'Grp':>5} {'KO':>5} {'Pen':>5} {'Net':>5}  Knockouts"
    )
    lines.append("-" * 80)

    for pos, r in enumerate(processed, 1):
        overtime_str = ""
        if r["overtime_secs"] > 0:
            overtime_str = f" (+{r['overtime_secs']//60}m{r['overtime_secs']%60:02d}s)"

        ko_str = " | ".join(r["knockout_detail"]) if r["knockout_detail"] else "-"

        lines.append(
            f"{pos:<4} {r['name']:<22} {r['club']:<8} "
            f"{r['total_time']:<9}{overtime_str:<12}"
            f"{r['group_pts']:>5} {r['knockout_pts']:>5} "
            f"{'-' + str(r['penalty']) if r['penalty'] else '':>5} "
            f"{r['net_score']:>5}  {ko_str}"
        )

    lines.append("=" * 80)
    lines.append(f"Total finishers: {len(processed)}")
    return "\n".join(lines)


def format_detail(r):
    """Return detailed breakdown for a single runner."""
    lines = []
    lines.append(f"\n--- {r['name']} ({r['club']}) ---")
    lines.append(f"Start: {r['start_local']}  Finish: {r['finish_local']}  "
                 f"Time: {r['total_time']}")

    qual_str = "  ".join(
        f"Grp {g}: {'✓' if q else '✗'} ({len(r['group_hits'][g])}/6)"
        for g, q in r["qualified"].items()
    )
    lines.append(f"Qualification: {qual_str}")
    lines.append(f"Group controls: {', '.join(r['group_detail']) or 'none'}")
    lines.append(f"Knockout:       {' | '.join(r['knockout_detail']) or 'none'}")
    lines.append(
        f"Score: {r['group_pts']} (group) + {r['knockout_pts']} (knockout) "
        f"- {r['penalty']} (penalty) = {r['net_score']}"
    )
    return "\n".join(lines)


def export_json(processed, filename, event_name):
    """Write results to JSON for web page consumption."""
    results_list = []
    for pos, r in enumerate(processed, 1):
        sk = r["scored_knockouts"]
        if 99 in sk:
            furthest = "Final"
        elif 59 in sk or 69 in sk:
            furthest = "SF"
        elif sk & {19, 29, 39, 49}:
            furthest = "QF"
        else:
            furthest = "Group"

        results_list.append({
            "pos":              pos,
            "name":             r["name"],
            "club":             r["club"],
            "classifier":       r["classifier"],
            "start_local":      r["start_local"],
            "finish_local":     r["finish_local"],
            "total_time":       r["total_time"],
            "total_secs":       r["total_secs"],
            "group_pts":        r["group_pts"],
            "knockout_pts":     r["knockout_pts"],
            "raw_score":        r["raw_score"],
            "penalty":          r["penalty"],
            "overtime_secs":    r["overtime_secs"],
            "net_score":        r["net_score"],
            "qualified":        r["qualified"],
            "scored_knockouts": sorted(r["scored_knockouts"]),
            "group_detail":     r["group_detail"],
            "knockout_detail":  r["knockout_detail"],
            "group_hits":       {g: hits for g, hits in r["group_hits"].items()},
            "furthest_round":   furthest,
        })

    envelope = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event":         event_name,
        "runner_count":  len(results_list),
        "status":        "live",
        "results":       results_list,
    }

    with open(filename, "w") as f:
        json.dump(envelope, f, indent=2)
    print(f"JSON written to {filename}")


def export_csv(processed, filename):
    """Write results to CSV."""
    import csv
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Pos", "Name", "Club", "Start", "Finish", "Time",
            "GrpA", "GrpB", "GrpC", "GrpD",
            "QualA", "QualB", "QualC", "QualD",
            "GroupPts", "KnockoutPts", "Penalty", "NetScore",
            "Knockouts"
        ])
        for pos, r in enumerate(processed, 1):
            writer.writerow([
                pos,
                r["name"],
                r["club"],
                r["start_local"],
                r["finish_local"],
                r["total_time"],
                len(r["group_hits"]["A"]),
                len(r["group_hits"]["B"]),
                len(r["group_hits"]["C"]),
                len(r["group_hits"]["D"]),
                "Y" if r["qualified"]["A"] else "N",
                "Y" if r["qualified"]["B"] else "N",
                "Y" if r["qualified"]["C"] else "N",
                "Y" if r["qualified"]["D"] else "N",
                r["group_pts"],
                r["knockout_pts"],
                r["penalty"],
                r["net_score"],
                " | ".join(r["knockout_detail"]),
            ])
    print(f"CSV written to {filename}")


# ---------------------------------------------------------------------------
# MapRun API fetch
# ---------------------------------------------------------------------------

API_URL = "https://p.fne.com.au:8886/resultsGetPublicForEventv2"

def fetch_maprun_results(event_name):
    """Fetch results JSON from the MapRun API."""
    params = urllib.parse.urlencode({"eventName": event_name})
    url = f"{API_URL}?{params}"
    print(f"Fetching: {url}")
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"ERROR fetching results: {e}", file=sys.stderr)
        sys.exit(1)

    if data.get("errorFlag"):
        print(f"MapRun API error: {data.get('statusMessage')}", file=sys.stderr)
        sys.exit(1)

    return data["results"]


# ---------------------------------------------------------------------------
# Demo / test data
# ---------------------------------------------------------------------------

DEMO_RESULTS = [
    {   # Clean run through all groups and knockouts
        "Id": 1, "Firstname": "Alice", "Surname": "Runner", "Gender": "F",
        "ClubName": "MVOC", "Classifier": "OK",
        "StartPunchTimeLocal": "18:30:00", "FinishPunchTimeLocal": "19:27:45",
        "TotalTimehhmmss": "0:57:45", "TotalTimeSecs": 3465,
        "punchControlIds": ["11","12","13","14","15","16",   # All Group A
                            "21","22","23","24","25","26",   # All Group B
                            "31","32","33","34","35","36",   # All Group C
                            "41","42","43","44","45","46",   # All Group D
                            "19","29","39","49",             # All QFs
                            "59","69",                       # Both SFs
                            "99"],                           # Final
        "punchTimeAfterStartSecs": list(range(100, 3400, 100)),
    },
    {   # Good group stage, gets QF-A and QF-B, reaches SF1 but not SF2
        "Id": 2, "Firstname": "Bob", "Surname": "Smith", "Gender": "M",
        "ClubName": "MVOC", "Classifier": "OK",
        "StartPunchTimeLocal": "18:35:00", "FinishPunchTimeLocal": "19:33:10",
        "TotalTimehhmmss": "0:58:10", "TotalTimeSecs": 3490,
        "punchControlIds": ["11","12","13","14","15","16",   # All Group A
                            "21","22","23","24","25","26",   # All Group B
                            "31","32","33",                  # 3 from Group C (qualifies)
                            "41","42",                       # 2 from Group D (doesn't qualify)
                            "19","29","39","49",             # Punches all QFs
                            "59","69",                       # Punches both SFs
                            "99"],                           # Punches Final
        "punchTimeAfterStartSecs": list(range(80, 3490, 90)),
    },
    {   # Greedy: skips groups, punches knockouts — most score zero
        "Id": 3, "Firstname": "Charlie", "Surname": "Greedy", "Gender": "M",
        "ClubName": "MVOC", "Classifier": "OK",
        "StartPunchTimeLocal": "18:40:00", "FinishPunchTimeLocal": "19:38:20",
        "TotalTimehhmmss": "0:58:20", "TotalTimeSecs": 3500,
        "punchControlIds": ["11","12",                       # 2 from Group A (doesn't qualify)
                            "21","22","23",                  # 3 from Group B (qualifies)
                            "31","32",                       # 2 from Group C (doesn't qualify)
                            "41","42","43",                  # 3 from Group D (qualifies)
                            "19","29","39","49","59","69","99"],
        "punchTimeAfterStartSecs": list(range(60, 3500, 80)),
    },
    {   # Steady completer — finishes 3 mins late
        "Id": 4, "Firstname": "Diana", "Surname": "Steady", "Gender": "F",
        "ClubName": "MVOC", "Classifier": "OK",
        "StartPunchTimeLocal": "18:45:00", "FinishPunchTimeLocal": "19:48:30",
        "TotalTimehhmmss": "1:03:30", "TotalTimeSecs": 3810,
        "punchControlIds": ["11","12","13","14",             # 4 from Group A
                            "21","22","23","24",             # 4 from Group B
                            "31","32","33","34",             # 4 from Group C
                            "41","42","43","44",             # 4 from Group D
                            "19","29","39","49"],            # All QFs
        "punchTimeAfterStartSecs": list(range(120, 3810, 120)),
    },
    {   # Beginner — just group stage controls
        "Id": 5, "Firstname": "Ed", "Surname": "Newbie", "Gender": "M",
        "ClubName": "MVOC", "Classifier": "OK",
        "StartPunchTimeLocal": "19:00:00", "FinishPunchTimeLocal": "19:55:00",
        "TotalTimehhmmss": "0:55:00", "TotalTimeSecs": 3300,
        "punchControlIds": ["11","12","13",                  # 3 from Group A
                            "21","22","23",                  # 3 from Group B
                            "31","32","33",                  # 3 from Group C
                            "41","42","43"],                 # 3 from Group D
        "punchTimeAfterStartSecs": list(range(200, 3300, 200)),
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="World Cup Score Event Results Processor — MVOC Nower 2026"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--event", metavar="NAME",
                       help="Full MapRun event name (as published)")
    group.add_argument("--demo", action="store_true",
                       help="Run with synthetic demo data to test scoring logic")
    parser.add_argument("--csv", metavar="FILE",
                        help="Export results to CSV file")
    parser.add_argument("--json", metavar="FILE",
                        help="Export results to JSON file (for web results page)")
    parser.add_argument("--detail", action="store_true",
                        help="Show detailed breakdown for each runner")
    args = parser.parse_args()

    if args.demo:
        print("Running in DEMO mode with synthetic test data\n")
        raw_results = DEMO_RESULTS
    else:
        raw_results = fetch_maprun_results(args.event)

    if not raw_results:
        print("No results found.")
        return

    event_name = args.event or "DEMO"
    processed = process_results(raw_results)
    print(format_results_table(processed))

    if args.detail:
        for r in processed:
            print(format_detail(r))

    if args.csv:
        export_csv(processed, args.csv)

    if args.json:
        export_json(processed, args.json, event_name)


if __name__ == "__main__":
    main()
