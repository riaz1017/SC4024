import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "pscomppars_raw.csv"
CLEAN_PATH = ROOT / "data" / "planets_clean.csv"
STATS_PATH = ROOT / "data" / "stats.json"

KEPLER_RA = 290.6667
KEPLER_DEC = 44.5
NEAR_PC = 2000.0

METHOD_ORDER = [
    "Transit",
    "Radial Velocity",
    "Microlensing",
    "Imaging",
    "Other",
]

SURVEY_ORDER = [
    "Kepler",
    "K2",
    "TESS",
    "Radial Velocity",
    "Microlensing",
    "Imaging",
    "Other transit",
    "Other",
]


def method_group(method):
    if method in ("Transit", "Radial Velocity", "Microlensing", "Imaging"):
        return method
    return "Other"


def survey_group(facility, method):
    if facility == "K2":
        return "K2"
    if facility == "Kepler":
        return "Kepler"
    if "TESS" in facility:
        return "TESS"
    if method == "Radial Velocity":
        return "Radial Velocity"
    if method == "Microlensing":
        return "Microlensing"
    if method == "Imaging":
        return "Imaging"
    if method == "Transit":
        return "Other transit"
    return "Other"


def angular_separation_deg(ra, dec, ra0, dec0):
    ra_r = np.deg2rad(ra)
    dec_r = np.deg2rad(dec)
    ra0_r = np.deg2rad(ra0)
    dec0_r = np.deg2rad(dec0)
    cosang = np.sin(dec0_r) * np.sin(dec_r) + np.cos(dec0_r) * np.cos(dec_r) * np.cos(ra_r - ra0_r)
    return np.rad2deg(np.arccos(np.clip(cosang, -1.0, 1.0)))


def equatorial_to_cartesian(ra, dec, dist):
    ra_r = np.deg2rad(ra)
    dec_r = np.deg2rad(dec)
    x = dist * np.cos(dec_r) * np.cos(ra_r)
    y = dist * np.cos(dec_r) * np.sin(ra_r)
    z = dist * np.sin(dec_r)
    return x, y, z


def _median(series):
    if series.notna().sum() == 0:
        return None
    return round(float(series.median()), 2)


def build_stats(df):
    spatial = df["has_distance"]
    kepler = df["survey"] == "Kepler"
    year_counts = df.groupby("disc_year").size()
    transit_counts = df[df["method"] == "Transit"].groupby("disc_year").size()

    def year_share(year):
        total = int(year_counts.get(year, 0))
        transit = int(transit_counts.get(year, 0))
        kepler_n = int(((df["disc_year"] == year) & kepler).sum())
        share = round(transit / total, 3) if total else None
        return {
            "year": year,
            "discoveries": total,
            "transits": transit,
            "transit_share": share,
            "kepler_facility": kepler_n,
        }

    by_method = {}
    for name, part in df.groupby("method", observed=False):
        by_method[str(name)] = {
            "n": int(len(part)),
            "median_distance_pc": _median(part["sy_dist"]),
            "median_radius_rearth": _median(part["pl_rade"]),
            "median_period_days": _median(part["pl_orbper"]),
        }

    by_survey = {}
    for name, part in df.groupby("survey", observed=False):
        by_survey[str(name)] = {
            "n": int(len(part)),
            "with_distance": int(part["has_distance"].sum()),
            "within_2000_pc": int((part["sy_dist"] <= NEAR_PC).sum()),
            "median_distance_pc": _median(part["sy_dist"]),
            "median_offset_from_kepler_deg": _median(part["kepler_offset_deg"]),
            "max_offset_from_kepler_deg": round(float(part["kepler_offset_deg"].max()), 2),
        }

    beyond = df[spatial & (df["sy_dist"] > NEAR_PC)]
    return {
        "source": "NASA Exoplanet Archive pscomppars",
        "n_planets": int(len(df)),
        "n_hosts": int(df["hostname"].nunique()),
        "year_min": int(df["disc_year"].min()),
        "year_max": int(df["disc_year"].max()),
        "n_with_distance": int(spatial.sum()),
        "n_missing_distance": int((~spatial).sum()),
        "n_within_2000_pc": int((df["sy_dist"] <= NEAR_PC).sum()),
        "n_beyond_2000_pc": int(len(beyond)),
        "beyond_2000_pc_by_survey": beyond["survey"].value_counts().astype(int).to_dict(),
        "cumulative": {
            "through_2009": int((df["disc_year"] <= 2009).sum()),
            "through_2014": int((df["disc_year"] <= 2014).sum()),
            "through_2018": int((df["disc_year"] <= 2018).sum()),
        },
        "years": {
            "2009": year_share(2009),
            "2014": year_share(2014),
            "2016": year_share(2016),
        },
        "by_method": by_method,
        "by_survey": by_survey,
        "kepler_field_center_deg": {"ra": KEPLER_RA, "dec": KEPLER_DEC},
        "near_limit_pc": NEAR_PC,
    }


def prepare(raw_path=RAW_PATH):
    df = pd.read_csv(raw_path)
    df["method"] = df["discoverymethod"].map(method_group)
    df["survey"] = [
        survey_group(facility, method)
        for facility, method in zip(df["disc_facility"], df["discoverymethod"])
    ]
    df["method"] = pd.Categorical(df["method"], METHOD_ORDER, ordered=True)
    df["survey"] = pd.Categorical(df["survey"], SURVEY_ORDER, ordered=True)
    df["has_distance"] = df["sy_dist"].notna()
    df["kepler_offset_deg"] = angular_separation_deg(
        df["ra"].to_numpy(), df["dec"].to_numpy(), KEPLER_RA, KEPLER_DEC
    )

    x = np.full(len(df), np.nan)
    y = np.full(len(df), np.nan)
    z = np.full(len(df), np.nan)
    ok = df["has_distance"].to_numpy()
    x[ok], y[ok], z[ok] = equatorial_to_cartesian(
        df.loc[ok, "ra"].to_numpy(),
        df.loc[ok, "dec"].to_numpy(),
        df.loc[ok, "sy_dist"].to_numpy(),
    )
    df["x_pc"] = np.round(x, 2)
    df["y_pc"] = np.round(y, 2)
    df["z_pc"] = np.round(z, 2)
    df["within_2000_pc"] = df["sy_dist"] <= NEAR_PC
    return df


def main():
    df = prepare()
    stats = build_stats(df)
    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_PATH, index=False)
    STATS_PATH.write_text(json.dumps(stats, indent=2))
    print(f"wrote {CLEAN_PATH} ({len(df)} rows)")
    print(f"wrote {STATS_PATH}")


if __name__ == "__main__":
    main()
