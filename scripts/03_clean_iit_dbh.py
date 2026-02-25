"""
03_clean_iit_dbh.py
====================
Applies species-specific DBH validation to flag data entry errors
in the IIT campus tree inventory.

Input:
  - data/processed/iit_trees_clean.csv

Output:
  - data/processed/iit_trees_corrected.csv  (1,643 rows × 18 columns)

New columns added:
  dbh_clean  — use this for all benefit calculations (blank if excluded)
  dbh_status — explains whether each tree is clean or excluded, and why

Filter for analysis:
  established == True  AND  dbh_status == 'clean'

Background:
  Multi-stem DBH values in the original map were entered as concatenated
  digits without a separator (e.g. "322" = stems of 3", 2", 2"). Our
  greedy parser splits these correctly for most trees, but produces
  implausible values for some entries (e.g. parsing "643" as [64, 3]
  instead of [6, 4, 3]). Trees where any parsed stem exceeds the
  species-specific max DBH are excluded.

  Additionally, some single-stem entries have DBH values that far
  exceed biological maxima for their species (e.g. Redbud with 98"
  DBH), almost certainly from data entry errors in the original map.
"""

import csv
import math
from pathlib import Path

PROCESSED = Path("data/processed")

# ── Species-specific max realistic DBH (inches) ───────────────
# Derived from species biology and clean data distribution.
# Species not listed here use DEFAULT_MAX = 40".
SPECIES_MAX = {
    "Redbud-Eastern":        15,
    "Hawthorn":              16,
    "Serviceberry":          10,
    "Hornbeam-American":     10,
    "Arborvitae-Eastern":    12,
    "Crabapple":             14,
    "Birch-Gray":            14,
    "Dogwood-Pagoda":         8,
    "Maple-Amur":            12,
    "Hophornbeam- American": 10,
    "Viburnum":               6,
    "Black Lace Elderberry":  6,
}
DEFAULT_MAX = 40


def get_max(species):
    return SPECIES_MAX.get(species, DEFAULT_MAX)


def parse_stems(raw_str):
    """Greedy parse of concatenated multi-stem DBH string."""
    s = str(int(float(raw_str)))
    stems, i = [], 0
    while i < len(s):
        if i + 1 < len(s) and int(s[i:i+2]) >= 10:
            stems.append(int(s[i:i+2]))
            i += 2
        else:
            stems.append(int(s[i]))
            i += 1
    return stems


# ── Load trees ────────────────────────────────────────────────
with open(PROCESSED / "iit_trees_clean.csv") as f:
    all_rows = list(csv.DictReader(f))

print(f"Loaded {len(all_rows)} trees")

# ── Classify each tree ─────────────────────────────────────────
output = []
stats = {k: 0 for k in ["clean_single", "clean_multi",
                          "flagged_single", "flagged_multi",
                          "no_dbh", "new_planting"]}

for r in all_rows:
    row = dict(r)
    sp  = row["common_name"]
    mx  = get_max(sp)

    # 2025 plantings — pass through, don't validate
    if row["established"] == "False":
        row["dbh_clean"]  = row["dbh_equiv"]
        row["dbh_status"] = "new_planting"
        stats["new_planting"] += 1

    # No DBH data
    elif row["dbh_raw"] == "":
        row["dbh_clean"]  = ""
        row["dbh_status"] = "no_dbh"
        stats["no_dbh"] += 1

    # Single-stem
    elif row["is_multi_stem"] == "False":
        try:
            val = float(row["dbh_inches"])
            if val <= mx:
                row["dbh_clean"]  = val
                row["dbh_status"] = "clean"
                stats["clean_single"] += 1
            else:
                row["dbh_clean"]  = ""
                row["dbh_status"] = f"excluded_single_stem_exceeds_{mx}in_max_for_species"
                stats["flagged_single"] += 1
        except ValueError:
            row["dbh_clean"]  = ""
            row["dbh_status"] = "no_dbh"
            stats["no_dbh"] += 1

    # Multi-stem
    elif row["is_multi_stem"] == "True":
        try:
            stems = parse_stems(row["dbh_raw"])
            if any(s > mx for s in stems):
                row["dbh_clean"]  = ""
                row["dbh_status"] = (f"excluded_multi_stem_implausible_parse_{stems}_"
                                     f"exceeds_{mx}in_max_for_species")
                stats["flagged_multi"] += 1
            else:
                equiv = round(math.sqrt(sum(s**2 for s in stems)), 2)
                row["dbh_clean"]  = equiv
                row["dbh_status"] = "clean"
                stats["clean_multi"] += 1
        except Exception:
            row["dbh_clean"]  = ""
            row["dbh_status"] = "no_dbh"
            stats["no_dbh"] += 1

    else:
        row["dbh_clean"]  = ""
        row["dbh_status"] = "no_dbh"
        stats["no_dbh"] += 1

    output.append(row)

# ── Write CSV ──────────────────────────────────────────────────
fieldnames = [
    "tree_id", "placemark_name", "planting_cohort", "established",
    "common_name", "scientific_name", "additional_taxonomy",
    "dbh_inches", "dbh_raw", "dbh_equiv", "dbh_clean", "dbh_status",
    "is_multi_stem", "source", "community_tags", "memorial",
    "latitude", "longitude",
]

out_path = PROCESSED / "iit_trees_corrected.csv"
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(output)

# ── Report ─────────────────────────────────────────────────────
total_flagged = stats["flagged_single"] + stats["flagged_multi"]
total_clean   = stats["clean_single"]   + stats["clean_multi"]

print(f"\nSaved → {out_path}")
print(f"\n── DBH Cleaning Summary ─────────────────────────────────")
print(f"  Clean single-stem:    {stats['clean_single']:>4}")
print(f"  Clean multi-stem:     {stats['clean_multi']:>4}")
print(f"  Total clean:          {total_clean:>4}")
print(f"  Excluded single-stem: {stats['flagged_single']:>4}  (exceeds species max DBH)")
print(f"  Excluded multi-stem:  {stats['flagged_multi']:>4}  (implausible stem parse)")
print(f"  Total excluded:       {total_flagged:>4}  ({total_flagged/(total_clean+total_flagged)*100:.1f}% of established trees)")
print(f"  No DBH data:          {stats['no_dbh']:>4}")
print(f"  New plantings (2025): {stats['new_planting']:>4}")
print()
print("  To filter for analysis in pandas:")
print("  df = df[(df['established'] == True) & (df['dbh_status'] == 'clean')]")
print("\nDone! ✓")
