"""
01_merge_chicago_data.py
========================
Merges four datasets into a single census-tract-level file.

Inputs (place in data/raw/):
  - SevenCensusWCommunity.csv
  - PLACES__Local_Data_for_Better_Health_Census_Tract_Data_2025_release_20260124.csv
  - CensusTractsTIGER2010_20260129.csv
  - Air_Quality_and_Health_Index_Scores_by_Census_Block_Group.xlsx

Output:
  - data/processed/merged_chicago_data.csv  (801 rows × 26 columns)
"""

import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────
RAW       = Path("data/raw")
PROCESSED = Path("data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

# ── Step 1: Load raw files ─────────────────────────────────────
print("Loading raw files...")
crti   = pd.read_csv(RAW / "SevenCensusWCommunity.csv")
places = pd.read_csv(RAW / "PLACES__Local_Data_for_Better_Health_Census_Tract_Data_2025_release_20260124.csv")
tiger  = pd.read_csv(RAW / "CensusTractsTIGER2010_20260129.csv")
aqh    = pd.read_excel(RAW / "Air_Quality_and_Health_Index_Scores_by_Census_Block_Group.xlsx",
                       sheet_name="AQH Index Scores")

print(f"  CRTI rows:   {len(crti):,}")
print(f"  PLACES rows: {len(places):,}")
print(f"  TIGER rows:  {len(tiger):,}")
print(f"  AQH rows:    {len(aqh):,}")


# ── Step 2: Create shared join key (11-digit census tract GEOID) ──
print("\nCreating join keys...")

# CRTI AFFGEOID format: "1400000US17031010501" — last 11 digits are GEOID
crti["GEOID"] = crti["AFFGEOID"].str[-11:].astype(int)

# CDC PLACES LocationID is already the 11-digit GEOID as integer
places["GEOID"] = places["LocationID"].astype(int)

# TIGER GEOID10 is already an integer
tiger["GEOID"] = tiger["GEOID10"].astype(int)


# ── Step 3: Reshape CDC PLACES from long → wide ───────────────
# PLACES has one row per (tract × health measure)
# We want one row per tract with each measure as its own column
print("Reshaping CDC PLACES (long → wide)...")

places_slim = places[["GEOID", "MeasureId", "Data_Value", "TotalPopulation"]].copy()

places_wide = places_slim.pivot_table(
    index="GEOID",
    columns="MeasureId",
    values="Data_Value",
    aggfunc="first"
).reset_index()
places_wide.columns.name = None

places_wide = places_wide.rename(columns={
    "CASTHMA":    "asthma_pct",
    "COPD":       "copd_pct",
    "DEPRESSION": "depression_pct",
    "LPA":        "physical_inactivity_pct",
    "MHLTH":      "mental_health_pct",
    "OBESITY":    "obesity_pct",
})

# Add population (same across measures for each tract)
pop = places_slim.groupby("GEOID")["TotalPopulation"].first().reset_index()
places_wide = places_wide.merge(pop, on="GEOID", how="left")

print(f"  PLACES wide shape: {places_wide.shape}")


# ── Step 4: Aggregate AQH block-group scores to tract level ───
# AQH is at census block group level — aggregate up using population weighting
# Exclude flagged block groups before aggregating
print("Aggregating AQH scores to census tract level...")

aqh_clean = aqh[aqh["FLAGGED"] == "NO"].copy()
print(f"  Excluded {len(aqh) - len(aqh_clean)} flagged block groups")

# Extract 11-digit tract GEOID from 12-digit block group ID
aqh_clean["GEOID"] = aqh_clean["census_block_group"].astype(str).str[:11].astype(int)
aqh_clean["weighted_score"] = aqh_clean["AQH_index_score"] * aqh_clean["ACSTOTPOP"]

tract_aqh = aqh_clean.groupby("GEOID").agg(
    AQH_score_popweighted = ("weighted_score",          "sum"),
    AQH_score             = ("AQH_index_score",         "mean"),
    AQH_score_max         = ("AQH_index_score",         "max"),
    AQH_percentile        = ("AQH_index_percentile",    "mean"),
    AQH_block_group_count = ("census_block_group",      "count"),
    AQH_tract_population  = ("ACSTOTPOP",               "sum"),
).reset_index()

# Finish population-weighted mean
tract_aqh["AQH_score_popweighted"] = (
    tract_aqh["AQH_score_popweighted"] / tract_aqh["AQH_tract_population"]
).round(3)
tract_aqh["AQH_score"]     = tract_aqh["AQH_score"].round(3)
tract_aqh["AQH_score_max"] = tract_aqh["AQH_score_max"].round(3)
tract_aqh["AQH_percentile"]= tract_aqh["AQH_percentile"].round(1)

print(f"  AQH aggregated to {len(tract_aqh)} census tracts")


# ── Step 5: Slim TIGER to needed columns ──────────────────────
tiger_slim = tiger[["GEOID", "COMMAREA", "COMMAREA_N", "NAMELSAD10"]].copy()
tiger_slim = tiger_slim.rename(columns={
    "NAMELSAD10": "tract_name",
    "COMMAREA":   "community_area_num",
    "COMMAREA_N": "community_area_num2",
})


# ── Step 6: Merge all datasets ────────────────────────────────
# Base: TIGER (801 Chicago census tracts)
# Left-join everything else to preserve all 801 tracts
print("\nMerging all datasets...")

merged = tiger_slim.copy()

# + CRTI canopy/environmental data
crti_slim = crti.drop(columns=["FID", "AFFGEOID", "Shape__Area", "Shape__Length"],
                       errors="ignore")
merged = merged.merge(crti_slim, on="GEOID", how="left")

# + CDC PLACES health outcomes
merged = merged.merge(places_wide, on="GEOID", how="left")

# + AQH air quality/health index
merged = merged.merge(tract_aqh, on="GEOID", how="left")

print(f"  Final shape: {merged.shape}  ({len(merged)} tracts × {len(merged.columns)} columns)")


# ── Step 7: Quality check ─────────────────────────────────────
print("\nMissing value report:")
missing = merged.isnull().sum()
missing = missing[missing > 0].sort_values(ascending=False)
if len(missing) == 0:
    print("  No missing values.")
else:
    for col, n in missing.items():
        print(f"  {col:<35} {n:>4} missing ({n/len(merged)*100:.1f}%)")


# ── Step 8: Save ──────────────────────────────────────────────
out_path = PROCESSED / "merged_chicago_data.csv"
merged.to_csv(out_path, index=False)
print(f"\nSaved → {out_path}")


# ── Step 9: Summary statistics ────────────────────────────────
print("\n── Summary Statistics ──────────────────────────────────")
summary_cols = [
    "PERCENT_CA", "AIR_TOXINS", "SURFACE_TE", "FLOOD_SUSC", "VULNERABLE",
    "asthma_pct", "copd_pct", "depression_pct",
    "physical_inactivity_pct", "mental_health_pct", "obesity_pct",
    "AQH_score_popweighted", "AQH_percentile",
]
available = [c for c in summary_cols if c in merged.columns]
print(merged[available].describe().round(2).to_string())

print("\nDone! ✓")
