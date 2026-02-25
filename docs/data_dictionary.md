# Data Dictionary

## `merged_chicago_data.csv`
801 Chicago census tracts. One row per tract.

### Geographic Identifiers
| Column | Type | Description |
|---|---|---|
| `GEOID` | int | 11-digit census tract FIPS code (e.g. 17031010501) |
| `tract_name` | str | Census tract label (e.g. "Census Tract 105.01") |
| `community_area_num` | int | Chicago community area number (1–77) |
| `COMMUNITY` | str | Chicago community area name (e.g. "Bronzeville") |

### CRTI Environmental Variables
Source: Chicago Region Trees Initiative / Morton Arboretum

| Column | Type | Range | Description |
|---|---|---|---|
| `PERCENT_CA` | float | 0.6–69.0 | Tree canopy cover (%) |
| `SURFACE_TE` | float | — | Surface temperature score |
| `FLOOD_SUSC` | float | — | Flood susceptibility score |
| `AIR_TOXINS` | float | — | Air toxins exposure score |
| `VULNERABLE` | float | — | Social vulnerability score |
| `PRIORITY` | float | — | CRTI composite planting priority score |
| `RANK` | str | — | CRTI priority rank category |
| `VULRANK` | str | — | Vulnerability rank category |

### CDC PLACES Health Outcomes
Source: CDC PLACES 2025 release. All values are % prevalence among adults.

| Column | Type | Citywide Range | Description |
|---|---|---|---|
| `asthma_pct` | float | 7.5–15.8% | Current asthma prevalence |
| `copd_pct` | float | — | COPD prevalence |
| `depression_pct` | float | — | Depression prevalence |
| `obesity_pct` | float | — | Obesity prevalence |
| `physical_inactivity_pct` | float | 8.5–51.7% | Physical inactivity prevalence |
| `mental_health_pct` | float | — | Poor mental health days prevalence |
| `TotalPopulation` | str | — | Tract population (from CDC PLACES) |

### AQH Air Quality + Health Index
Source: Chicago Health Atlas, 2020. Higher score = worse air quality + health burden.

| Column | Type | Citywide Range | Description |
|---|---|---|---|
| `AQH_score_popweighted` | float | 7.7–84.2 | Population-weighted mean AQH score across block groups in tract |
| `AQH_score` | float | — | Simple mean AQH score across block groups |
| `AQH_score_max` | float | — | Worst block group AQH score within tract |
| `AQH_percentile` | float | 0–99 | Mean AQH percentile rank within Chicago |
| `AQH_block_group_count` | int | — | Number of block groups in tract |
| `AQH_tract_population` | int | — | Tract population (from AQH dataset) |

---

## `iit_trees_corrected.csv`
1,643 trees from the IIT Alphawood Arboretum on the Mies Campus (Bronzeville, Chicago).

| Column | Type | Description |
|---|---|---|
| `tree_id` | int | Unique tree ID from IIT campus map |
| `placemark_name` | str | Original placemark label (e.g. "42-2022 U") |
| `planting_cohort` | str | Cohort code: `2022-U` (main survey), `2025-O` (Openlands 2025), etc. |
| `established` | bool | `True` = mature tree; `False` = 2025 sapling |
| `common_name` | str | Common species name (e.g. "Honeylocust-Thornless Common") |
| `scientific_name` | str | Scientific name (e.g. "Gleditsia triacanthos") |
| `additional_taxonomy` | str | Cultivar or variety if recorded |
| `dbh_inches` | float | DBH for single-stem trees (inches); blank if multi-stem |
| `dbh_raw` | str | Original raw DBH value from map |
| `dbh_equiv` | float | Basal-area equivalent DBH for multi-stem trees: sqrt(Σstems²) |
| `dbh_clean` | float | **Use this for analysis.** Blank if excluded or no data. |
| `dbh_status` | str | `clean`, `excluded_single_stem_...`, `excluded_multi_stem_...`, `no_dbh`, `new_planting` |
| `is_multi_stem` | bool | `True` if multiple stems were recorded in original map |
| `source` | str | Planting source (e.g. "Plant", "Unknown", "Fiore nursery") |
| `community_tags` | str | Tags from map (e.g. "Planted by Openlands TreeKeepers spring 2025") |
| `memorial` | str | Memorial dedication if applicable |
| `latitude` | float | GPS latitude |
| `longitude` | float | GPS longitude |
