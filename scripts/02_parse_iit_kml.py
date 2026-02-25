"""
02_parse_iit_kml.py
====================
Parses the IIT Alphawood Arboretum KML file into a clean CSV.

Input  (place in data/raw/):
  - Alphawood_Arboretum_at_Illinois_Tech_Mies_campus.kml

Output:
  - data/processed/iit_trees_clean.csv  (1,643 rows × 16 columns)

Cleaning steps:
  - Removes 5 non-tree placemarks (restrooms, sculptures, etc.)
  - Assigns planting_cohort from placemark name (e.g. 2022-U, 2025-O)
  - Flags 2025 saplings with established = False
  - Handles multi-stem DBH via basal-area equivalent: sqrt(sum of stems²)
"""

import xml.etree.ElementTree as ET
import csv
import re
import math
from pathlib import Path
from collections import Counter

RAW       = Path("data/raw")
PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

KML_PATH = RAW / "Alphawood_Arboretum_at_Illinois_Tech_Mies_campus.kml"

# ── Non-tree placemarks to exclude ────────────────────────────
NON_TREE_NAMES = {
    "Restroom",
    "Water Bottle Fill Station & Fountain",
    "Steel Sculpture IPRO Project Fall Semester 1996",
    "Sculpture",
    "U-Farm",
}

# ── Parse KML ─────────────────────────────────────────────────
print("Loading KML file...")
tree = ET.parse(KML_PATH)
root = tree.getroot()
ns = {"kml": "http://www.opengis.net/kml/2.2"}
placemarks = root.findall(".//kml:Placemark", ns)
print(f"  Found {len(placemarks)} total placemarks")


def parse_description(html_text):
    """Extract key:value pairs from HTML description block."""
    fields = {}
    if not html_text:
        return fields
    field_map = {
        "Common Name":         "common_name",
        "Scientific Name":     "scientific_name",
        "Additional Taxonomy": "additional_taxonomy",
        "Tree ID":             "tree_id",
        "DBH":                 "dbh_raw",
        "Source":              "source",
        "Community Tags":      "community_tags",
        "Memorial":            "memorial",
    }
    for label, col in field_map.items():
        match = re.search(rf"{re.escape(label)}:\s*([^<\n]+)", html_text)
        if match:
            val = match.group(1).strip()
            fields[col] = "" if val in ["...", "None", "N/A", ""] else val
        else:
            fields[col] = ""
    return fields


def get_cohort(name):
    """Extract planting cohort from placemark name (e.g. '42-2022 U' → '2022-U')."""
    match = re.match(r"\d+-(\d{4})\s*(\w*)", name)
    if match:
        year = match.group(1)
        code = match.group(2).upper() if match.group(2) else "U"
        return f"{year}-{code}"
    return "unknown"


def parse_dbh(raw_str):
    """
    Returns (dbh_single, dbh_equiv, is_multi_stem).
    Single stem (≤100"): both values are the same.
    Multi-stem (>100"):  dbh_single is blank, dbh_equiv = basal-area equivalent.

    Multi-stem DBH values are entered as concatenated digits without a separator,
    e.g. "322" = stems of 3", 2", 2" → sqrt(9+4+4) = 4.1"
    """
    if not raw_str:
        return "", "", ""
    try:
        val = float(raw_str)
    except ValueError:
        return "", "", ""

    if val <= 100:
        return val, val, False

    # Parse concatenated stems greedily (take 2-digit numbers when ≥ 10)
    s = str(int(val))
    stems, i = [], 0
    while i < len(s):
        if i + 1 < len(s) and int(s[i:i+2]) >= 10:
            stems.append(int(s[i:i+2]))
            i += 2
        else:
            stems.append(int(s[i]))
            i += 1
    equiv = round(math.sqrt(sum(x**2 for x in stems)), 2)
    return "", equiv, True


# ── Process placemarks ─────────────────────────────────────────
print("Processing placemarks...")
records, removed = [], []

for pm in placemarks:
    name_el  = pm.find("kml:name", ns)
    desc_el  = pm.find("kml:description", ns)
    coord_el = pm.find(".//kml:coordinates", ns)

    name = name_el.text.strip() if name_el is not None else ""

    if name in NON_TREE_NAMES:
        removed.append(name)
        continue
    if coord_el is None:
        continue

    try:
        parts     = coord_el.text.strip().split(",")
        longitude = float(parts[0])
        latitude  = float(parts[1])
    except (ValueError, IndexError):
        continue

    fields      = parse_description(desc_el.text if desc_el is not None else "")
    cohort      = get_cohort(name)
    established = not cohort.startswith("2025")
    dbh_s, dbh_e, is_multi = parse_dbh(fields.get("dbh_raw", ""))

    records.append({
        "tree_id":             fields.get("tree_id", ""),
        "placemark_name":      name,
        "planting_cohort":     cohort,
        "established":         established,
        "common_name":         fields.get("common_name", ""),
        "scientific_name":     fields.get("scientific_name", ""),
        "additional_taxonomy": fields.get("additional_taxonomy", ""),
        "dbh_inches":          dbh_s,
        "dbh_raw":             fields.get("dbh_raw", ""),
        "dbh_equiv":           dbh_e,
        "is_multi_stem":       is_multi,
        "source":              fields.get("source", ""),
        "community_tags":      fields.get("community_tags", ""),
        "memorial":            fields.get("memorial", ""),
        "latitude":            latitude,
        "longitude":           longitude,
    })

print(f"  Removed {len(removed)} non-tree placemarks")
print(f"  Kept {len(records)} tree records")


# ── Write CSV ──────────────────────────────────────────────────
fieldnames = [
    "tree_id", "placemark_name", "planting_cohort", "established",
    "common_name", "scientific_name", "additional_taxonomy",
    "dbh_inches", "dbh_raw", "dbh_equiv", "is_multi_stem",
    "source", "community_tags", "memorial", "latitude", "longitude",
]

out_path = PROCESSED / "iit_trees_clean.csv"
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)

print(f"\nSaved → {out_path}")


# ── Summary ────────────────────────────────────────────────────
cohorts = Counter(r["planting_cohort"] for r in records)
print("\n── Cohort Breakdown ─────────────────────────────────────")
for cohort, count in sorted(cohorts.items()):
    label = "newly planted" if cohort.startswith("2025") else "established"
    print(f"  {count:4d}  {cohort}  ({label})")

established = [r for r in records if r["established"]]
print(f"\n  Established trees: {len(established)}")
print(f"  2025 plantings:    {len(records) - len(established)}")

species = Counter(r["common_name"] for r in established if r["common_name"])
print(f"\n── Top 10 Species (established) ─────────────────────────")
for sp, count in species.most_common(10):
    print(f"  {count:4d}  {sp}")

print("\nDone! ✓")
