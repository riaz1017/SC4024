# SC4024 Exoplanet Discovery

Pair project for SC4024 Data Visualisation. The question is how time, detection method, and survey design shape which confirmed exoplanets end up in the catalog, and where they appear to sit.

The data is the NASA Exoplanet Archive Planetary Systems Composite Parameters table, one row per confirmed planet. The copy used here is `data/pscomppars_raw.csv`.

## Run the notebook

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter notebook exoplanet_discovery_analysis.ipynb
```

Run the cells from the top. The notebook reads `data/pscomppars_raw.csv`.

## Charts in the notebook

1. Discoveries per year, stacked by method, plus a cumulative count with mission years marked.
2. How many planets each method has found, and boxplots of radius and mass.
3. Orbital period against planet radius, with marker size for mass. A second plot puts mass on the y-axis, because many radial-velocity radii in this table are estimates near Jupiter's size.
4. Distance from Earth against discovery year.
5. A 3D view with Earth at the origin. Dropdowns switch the colour between method and facility, and change the distance cutoff. It opens at 2,000 parsecs so the Kepler wedge stays visible. A sky map under that shows the same facilities in direction only. Right ascension runs right to left.

## Files

| Path | What it is |
| --- | --- |
| `exoplanet_discovery_analysis.ipynb` | Main notebook |
| `src/prepare_data.py` | Cleans the raw table and writes `data/planets_clean.csv` and `data/stats.json` |
| `src/make_figures.py` | Writes the HTML and PNG files in `figures/` |
| `figures/` | Charts for the video. Open the `.html` files in a browser. |
| `requirements.txt` | Python packages |

To rebuild the files in `figures/`:

```bash
python src/prepare_data.py
python src/make_figures.py
```

Data source: [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/).
