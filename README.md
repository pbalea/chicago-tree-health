# Species-Specific Tree Equity and Health Benefits in Chicago

**Tomas Rebelatto & Paul Balea**  
Illinois Institute of Technology — SoReMo Initiative

---

## Project Overview

This project investigates whether specific tree species and tree attributes provide distinct environmental and health benefits at the neighborhood scale in Chicago. We focus especially on the South Side, where tree canopy coverage is historically inequitable. Our long-term goal is to provide evidence-based guidance to [Keeler Gardens](https://www.keelergardens.org/) and other community organizations on which species to prioritize for planting.

---

## Repository Structure

```
chicago-tree-health/
│
├── data/
│   ├── raw/                        # Original source files (not tracked by git — see below)
│   │   ├── SevenCensusWCommunity.csv
│   │   ├── PLACES__Local_Data_for_Better_Health_Census_Tract_Data_2025_release_20260124.csv
│   │   ├── CensusTractsTIGER2010_20260129.csv
│   │   ├── Most_Common_Tree_Species_Data.xlsx
│   │   ├── Air_Quality_and_Health_Index_Scores_by_Census_Block_Group.xlsx
│   │   └── Alphawood_Arboretum_at_Illinois_Tech_Mies_campus.kml
│   │
│   └── processed/                  # Cleaned, analysis-ready files (output of scripts)
│       ├── merged_chicago_data.csv
│       ├── iit_trees_corrected.csv
│       └── iit_species_dbh_reference.xlsx
│
├── scripts/
│   ├── 01_merge_chicago_data.py    # Merges CRTI + CDC PLACES + TIGER + AQH datasets
│   ├── 02_parse_iit_kml.py         # Parses IIT campus tree map KML → clean CSV
│   └── 03_clean_iit_dbh.py         # Flags and removes implausible DBH values
│
├── outputs/                        # Figures, tables, and analysis outputs (generated)
│
├── docs/
│   └── data_dictionary.md          # Description of all variables in merged_chicago_data.csv
│
├── .gitignore
└── README.md
```

---

## Data Sources

| Dataset | Source | Description |
|---|---|---|
| CRTI Priority Map | [Chicago Region Trees Initiative](https://chicagorti.org/) | Census-tract level canopy %, surface temp, flood risk, air toxins, vulnerability scores |
| CDC PLACES 2025 | [CDC PLACES](https://www.cdc.gov/places/) | Census-tract health outcomes: asthma, COPD, depression, obesity, physical inactivity |
| TIGER 2010 | [Chicago Data Portal](https://data.cityofchicago.org/) | Chicago census tract boundaries + community area assignments |
| AQH Index | [Chicago Health Atlas](https://www.chicagohealthatlas.org/) | Air Quality + Health Index scores by census block group (2020) |
| IIT Alphawood Arboretum | Illinois Institute of Technology Facilities | Campus tree inventory: 1,643 trees with species, DBH, and GPS coordinates |
| USDA Urban Forest Report | [USDA Forest Service rb_nrs84](https://www.fs.usda.gov/nrs/pubs/rb/rb_nrs84.pdf) | Species-level benefit estimates: carbon storage, sequestration, pollution removal |

---

## Scripts

### `01_merge_chicago_data.py`
Merges four datasets into a single census-tract-level file (`merged_chicago_data.csv`):
- Extracts 11-digit GEOIDs from CRTI's AFFGEOID format
- Reshapes CDC PLACES from long to wide format (one row per tract)
- Aggregates AQH block-group scores to tract level using population weighting
- Left-joins all datasets onto the TIGER census tract base (801 Chicago tracts)

**Input:** Raw CSVs and XLSX from `data/raw/`  
**Output:** `data/processed/merged_chicago_data.csv` (801 rows × 26 columns)

---

### `02_parse_iit_kml.py`
Parses the IIT campus tree map KML file into a clean, analysis-ready CSV:
- Extracts all tree attributes from KML description fields (species, DBH, GPS, source)
- Removes 5 non-tree placemarks (restrooms, sculptures, etc.)
- Assigns a `planting_cohort` label (e.g. `2022-U`, `2025-O`) from placemark name patterns
- Flags 2025 newly-planted saplings with `established = False`
- Handles multi-stem DBH entries using basal-area equivalent: `sqrt(sum of stems²)`

**Input:** `Alphawood_Arboretum_at_Illinois_Tech_Mies_campus.kml`  
**Output:** `data/processed/iit_trees_clean.csv` (1,643 rows × 16 columns)

---

### `03_clean_iit_dbh.py`
Applies species-specific DBH validation to flag data entry errors:
- Sets realistic maximum DBH thresholds per species (e.g. Redbud ≤ 15", Hawthorn ≤ 16")
- Flags single-stem entries exceeding species max as implausible
- Flags multi-stem entries where greedy digit-parsing produces implausible per-stem values
- Adds `dbh_clean` (use for analysis) and `dbh_status` (explains each tree's flag) columns
- 212 trees excluded (13.4% of established trees) — documented as data quality limitation

**Input:** `data/processed/iit_trees_clean.csv`  
**Output:** `data/processed/iit_trees_corrected.csv` (1,643 rows × 18 columns)

---

## Key Variables — `merged_chicago_data.csv`

| Column | Description |
|---|---|
| `GEOID` | 11-digit census tract identifier |
| `COMMUNITY` | Chicago community area name |
| `PERCENT_CA` | Tree canopy cover (%) — CRTI |
| `SURFACE_TE` | Surface temperature score — CRTI |
| `AIR_TOXINS` | Air toxins exposure score — CRTI |
| `FLOOD_SUSC` | Flood susceptibility score — CRTI |
| `VULNERABLE` | Social vulnerability score — CRTI |
| `PRIORITY` | CRTI planting priority score |
| `asthma_pct` | Current asthma prevalence (%) — CDC PLACES |
| `copd_pct` | COPD prevalence (%) — CDC PLACES |
| `depression_pct` | Depression prevalence (%) — CDC PLACES |
| `obesity_pct` | Obesity prevalence (%) — CDC PLACES |
| `physical_inactivity_pct` | Physical inactivity prevalence (%) — CDC PLACES |
| `mental_health_pct` | Poor mental health days (%) — CDC PLACES |
| `AQH_score_popweighted` | Population-weighted AQH score (higher = worse) |
| `AQH_percentile` | AQH percentile rank within Chicago (0–100) |

---

## Key Variables — `iit_trees_corrected.csv`

| Column | Description |
|---|---|
| `tree_id` | Unique tree ID from IIT map |
| `planting_cohort` | Cohort code (e.g. `2022-U`, `2025-O`) |
| `established` | `True` = mature tree; `False` = 2025 sapling |
| `common_name` | Common species name |
| `scientific_name` | Scientific species name |
| `dbh_inches` | DBH for single-stem trees (inches) |
| `dbh_equiv` | Basal-area equivalent DBH for multi-stem trees |
| `dbh_clean` | **Use this for analysis** — blank if excluded |
| `dbh_status` | Explains why each tree is clean or excluded |
| `is_multi_stem` | `True` if multiple stems were recorded |
| `latitude` / `longitude` | GPS coordinates |

---

## Reproducibility

### Requirements
```
python >= 3.9
pandas
openpyxl
```

Install dependencies:
```bash
pip install pandas openpyxl
```

### Run order
```bash
# 1. Merge Chicago neighborhood data
python scripts/01_merge_chicago_data.py

# 2. Parse IIT campus tree map
python scripts/02_parse_iit_kml.py

# 3. Clean DBH values
python scripts/03_clean_iit_dbh.py
```

All scripts expect raw data files to be placed in `data/raw/` before running.

---

## Status

- [x] Dataset merging (CRTI + CDC PLACES + TIGER + AQH)
- [x] IIT campus tree inventory parsed and cleaned
- [x] DBH data quality validation
- [ ] Species benefits table (carbon, pollution removal) — in progress
- [ ] Correlation analysis: canopy coverage vs. health outcomes
- [ ] IIT campus benefit calculations by species
- [ ] Neighborhood priority mapping
- [ ] Interactive dashboard

---

## Contact

Paul Balea — Illinois Institute of Technology  
Tomas Rebelatto — Illinois Institute of Technology
