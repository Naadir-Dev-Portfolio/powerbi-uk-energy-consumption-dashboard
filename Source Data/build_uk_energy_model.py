from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"

LOCAL_AUTHORITY_FILES = [
    ("Electricity", RAW_DIR / "elec_LA_stacked_2005-2024.csv"),
    ("Gas", RAW_DIR / "gas_LA_stacked_2005-2024.csv"),
]

REGION_FILES = [
    ("Electricity", RAW_DIR / "elec_region_stacked_2005-2024.csv"),
    ("Gas", RAW_DIR / "gas_region_stacked_2005-2024.csv"),
]

ENGLISH_REGIONS = {
    "North East",
    "North West",
    "Yorkshire and The Humber",
    "East Midlands",
    "West Midlands",
    "East of England",
    "London",
    "South East",
    "South West",
}

REGION_COUNTRY_MAP = {
    "Great Britain": "Great Britain",
    "England": "England",
    "Scotland": "Scotland",
    "Wales": "Wales",
}


def clean_text(value: str | None) -> str:
    return (value or "").strip()


def number(value: str | None) -> float | None:
    value = clean_text(value)
    if not value or value.lower() == "not set":
        return None
    value = value.replace(",", "")
    try:
        return float(value)
    except ValueError:
        return None


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def geography_country(region_name: str) -> str:
    if region_name in REGION_COUNTRY_MAP:
        return REGION_COUNTRY_MAP[region_name]
    if region_name in ENGLISH_REGIONS:
        return "England"
    return "Unclassified"


def regional_level(code: str, name: str) -> str:
    if name == "Great Britain" or code == "K03000001":
        return "Great Britain"
    if name in {"England", "Scotland", "Wales"}:
        return "Country"
    return "Region"


def ensure_geography(
    geographies: dict[str, dict],
    key: str,
    code: str,
    name: str,
    level: str,
    region_name: str,
    country_name: str,
) -> None:
    if key in geographies:
        return
    geographies[key] = {
        "GeographyKey": key,
        "GeographyCode": code,
        "GeographyName": name,
        "GeographyLevel": level,
        "RegionName": region_name,
        "CountryName": country_name,
        "IsLocalAuthority": level == "Local authority",
        "IsRegionOrCountry": level in {"Great Britain", "Country", "Region"},
    }


def consumption_columns(sector: str) -> tuple[str, str, str, str]:
    prefix = {
        "Domestic": "Domestic",
        "Non-domestic": "Non_domestic",
        "All": "All",
    }[sector]
    meters = f"{prefix}_meters_thousands"
    if sector == "Domestic":
        meters = "Domestic_meters_thouasands"
    return (
        meters,
        f"{prefix}_consumption_GWh",
        f"{prefix}_mean_consumption_KWh_per_meter" if sector != "All" else "All_mean_consumption_kWh_per_meter",
        f"{prefix}_median_consumption_kWh_per_meter" if sector != "Domestic" else "Domestic_median_consumption_kWh_per_meter",
    )


def build_consumption_rows() -> tuple[list[dict], dict[str, dict]]:
    fact_rows: list[dict] = []
    geographies: dict[str, dict] = {}

    for fuel, path in REGION_FILES:
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            for row in csv.DictReader(handle):
                year = int(row["Year"])
                code = clean_text(row["Code"])
                name = clean_text(row["Region"])
                level = regional_level(code, name)
                country = geography_country(name)
                region_name = name if level == "Region" else ""
                geography_key = f"{level}|{code}|{name}"
                ensure_geography(geographies, geography_key, code, name, level, region_name, country)
                add_sector_rows(fact_rows, row, fuel, year, geography_key, "Regional and national")

    for fuel, path in LOCAL_AUTHORITY_FILES:
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            for row in csv.DictReader(handle):
                year = int(row["Year"])
                code = clean_text(row["LA_Code"])
                name = clean_text(row["LA"])
                region_name = clean_text(row["Region"])
                country = geography_country(region_name)
                geography_key = f"Local authority|{code}|{name}"
                ensure_geography(
                    geographies,
                    geography_key,
                    code,
                    name,
                    "Local authority",
                    region_name,
                    country,
                )
                add_sector_rows(fact_rows, row, fuel, year, geography_key, "Local authority")

    return fact_rows, geographies


def add_sector_rows(
    fact_rows: list[dict],
    source_row: dict,
    fuel: str,
    year: int,
    geography_key: str,
    source_granularity: str,
) -> None:
    for sector in ["Domestic", "Non-domestic", "All"]:
        meters_col, consumption_col, mean_col, median_col = consumption_columns(sector)
        meters_thousands = number(source_row.get(meters_col))
        consumption_gwh = number(source_row.get(consumption_col))
        mean_kwh_per_meter = number(source_row.get(mean_col))
        median_kwh_per_meter = number(source_row.get(median_col))
        fact_rows.append(
            {
                "YearKey": year,
                "GeographyKey": geography_key,
                "Fuel": fuel,
                "Sector": sector,
                "MetersThousands": meters_thousands,
                "Meters": meters_thousands * 1000 if meters_thousands is not None else None,
                "ConsumptionGWh": consumption_gwh,
                "ConsumptionKWh": consumption_gwh * 1_000_000 if consumption_gwh is not None else None,
                "MeanKWhPerMeter": mean_kwh_per_meter,
                "MedianKWhPerMeter": median_kwh_per_meter,
                "SourceGranularity": source_granularity,
            }
        )


def build_electricity_profile_rows() -> list[dict]:
    profile_rows: list[dict] = []
    profile_specs = [
        (
            "Standard domestic",
            "Standard_domestic_meters_thousands",
            "Standard_domestic_consumption_GWh",
            "Standard_domestic_mean_consumption_KWh",
            "Standard_domestic_median_consumption_kWh_per_meter",
        ),
        (
            "Economy 7 domestic",
            "E7_domestic_meters_thousands",
            "E7_domestic_consumption_GWh",
            "E7_domestic_mean_consumption_KWh_per_meter",
            "E7_domestic_median_consumption_kWh_per_meter",
        ),
    ]

    for path, source_granularity, code_col, name_col in [
        (RAW_DIR / "elec_region_stacked_2005-2024.csv", "Regional and national", "Code", "Region"),
        (RAW_DIR / "elec_LA_stacked_2005-2024.csv", "Local authority", "LA_Code", "LA"),
    ]:
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            for row in csv.DictReader(handle):
                year = int(row["Year"])
                code = clean_text(row[code_col])
                name = clean_text(row[name_col])
                if source_granularity == "Local authority":
                    geography_key = f"Local authority|{code}|{name}"
                else:
                    level = regional_level(code, name)
                    geography_key = f"{level}|{code}|{name}"

                for profile, meters_col, consumption_col, mean_col, median_col in profile_specs:
                    meters_thousands = number(row.get(meters_col))
                    consumption_gwh = number(row.get(consumption_col))
                    if meters_thousands is None and consumption_gwh is None:
                        continue
                    profile_rows.append(
                        {
                            "YearKey": year,
                            "GeographyKey": geography_key,
                            "ElectricityProfile": profile,
                            "MetersThousands": meters_thousands,
                            "Meters": meters_thousands * 1000 if meters_thousands is not None else None,
                            "ConsumptionGWh": consumption_gwh,
                            "ConsumptionKWh": consumption_gwh * 1_000_000 if consumption_gwh is not None else None,
                            "MeanKWhPerMeter": number(row.get(mean_col)),
                            "MedianKWhPerMeter": number(row.get(median_col)),
                            "SourceGranularity": source_granularity,
                        }
                    )

    return profile_rows


def build_dates(fact_rows: list[dict]) -> list[dict]:
    years = sorted({int(row["YearKey"]) for row in fact_rows})
    latest = max(years)
    return [
        {
            "YearKey": year,
            "YearStartDate": f"{year}-01-01",
            "YearLabel": str(year),
            "YearSort": year,
            "PeriodGroup": (
                "Pre-2022 baseline"
                if year <= 2021
                else "Energy price shock"
                if year in {2022, 2023}
                else "Latest year"
            ),
            "IsLatestYear": year == latest,
            "YearsSinceStart": year - min(years),
        }
        for year in years
    ]


def build_latest_snapshot(fact_rows: list[dict], geographies: dict[str, dict]) -> list[dict]:
    latest_year = max(int(row["YearKey"]) for row in fact_rows)
    lookup: dict[tuple, dict] = {}
    for row in fact_rows:
        lookup[(row["YearKey"], row["GeographyKey"], row["Fuel"], row["Sector"])] = row

    snapshot = []
    for row in fact_rows:
        if row["YearKey"] != latest_year or row["Sector"] != "All":
            continue
        base_2021 = lookup.get((2021, row["GeographyKey"], row["Fuel"], row["Sector"]))
        prior = lookup.get((latest_year - 1, row["GeographyKey"], row["Fuel"], row["Sector"]))
        latest = row["ConsumptionGWh"]
        yoy = pct_change(latest, prior["ConsumptionGWh"] if prior else None)
        since_2021 = pct_change(latest, base_2021["ConsumptionGWh"] if base_2021 else None)
        mean_since_2021 = pct_change(
            row["MeanKWhPerMeter"],
            base_2021["MeanKWhPerMeter"] if base_2021 else None,
        )
        geography = geographies[row["GeographyKey"]]
        snapshot.append(
            {
                "YearKey": latest_year,
                "GeographyKey": row["GeographyKey"],
                "GeographyName": geography["GeographyName"],
                "GeographyLevel": geography["GeographyLevel"],
                "RegionName": geography["RegionName"],
                "CountryName": geography["CountryName"],
                "Fuel": row["Fuel"],
                "ConsumptionGWh": latest,
                "MeanKWhPerMeter": row["MeanKWhPerMeter"],
                "YoYChangePct": yoy,
                "ChangeSince2021Pct": since_2021,
                "MeanChangeSince2021Pct": mean_since_2021,
                "TrendSignal": trend_signal(yoy, since_2021),
                "EfficiencySignal": efficiency_signal(mean_since_2021),
            }
        )
    return snapshot


def pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return (current - previous) / previous


def trend_signal(yoy: float | None, since_2021: float | None) -> str:
    if yoy is None or since_2021 is None:
        return "Insufficient history"
    if since_2021 <= -0.10 and abs(yoy) <= 0.03:
        return "Lower plateau after 2021"
    if since_2021 <= -0.10 and yoy > 0.03:
        return "Partial rebound from lower base"
    if since_2021 < -0.03:
        return "Lower than 2021"
    if yoy >= 0.05:
        return "Short-term pressure rising"
    if yoy <= -0.05:
        return "Recent demand easing"
    return "Broadly stable"


def efficiency_signal(mean_change_since_2021: float | None) -> str:
    if mean_change_since_2021 is None or math.isnan(mean_change_since_2021):
        return "No comparison"
    if mean_change_since_2021 <= -0.10:
        return "Large reduction in mean use"
    if mean_change_since_2021 <= -0.03:
        return "Moderate reduction in mean use"
    if mean_change_since_2021 >= 0.03:
        return "Mean use rising"
    return "Mean use stable"


def build_quality_report(fact_rows: list[dict], profile_rows: list[dict], geographies: dict[str, dict]) -> dict:
    years = sorted({int(row["YearKey"]) for row in fact_rows})
    counts_by_level = defaultdict(int)
    for geo in geographies.values():
        counts_by_level[geo["GeographyLevel"]] += 1
    return {
        "processed_at": "Refresh generated by Source Data/build_uk_energy_model.py",
        "year_min": min(years),
        "year_max": max(years),
        "fact_energy_consumption_rows": len(fact_rows),
        "fact_electricity_profile_rows": len(profile_rows),
        "geography_rows": len(geographies),
        "geography_counts_by_level": dict(sorted(counts_by_level.items())),
        "notes": [
            "Gas data are weather-corrected in the DESNZ subnational publication.",
            "Gas consumption excludes unique sites to preserve time-series consistency, per DESNZ methodology notes.",
            "Rows with Sector = All are retained to support source median and mean metrics; DAX measures avoid double-counting when multiple sectors are selected.",
            "Electricity profile data are available from 2015 onward where DESNZ separates Standard domestic and Economy 7 domestic meters.",
        ],
    }


def main() -> None:
    fact_rows, geographies = build_consumption_rows()
    profile_rows = build_electricity_profile_rows()
    dates = build_dates(fact_rows)
    latest_snapshot = build_latest_snapshot(fact_rows, geographies)

    write_csv(
        PROCESSED_DIR / "fact_energy_consumption.csv",
        fact_rows,
        [
            "YearKey",
            "GeographyKey",
            "Fuel",
            "Sector",
            "MetersThousands",
            "Meters",
            "ConsumptionGWh",
            "ConsumptionKWh",
            "MeanKWhPerMeter",
            "MedianKWhPerMeter",
            "SourceGranularity",
        ],
    )
    write_csv(
        PROCESSED_DIR / "fact_electricity_profile.csv",
        profile_rows,
        [
            "YearKey",
            "GeographyKey",
            "ElectricityProfile",
            "MetersThousands",
            "Meters",
            "ConsumptionGWh",
            "ConsumptionKWh",
            "MeanKWhPerMeter",
            "MedianKWhPerMeter",
            "SourceGranularity",
        ],
    )
    write_csv(
        PROCESSED_DIR / "dim_date.csv",
        dates,
        [
            "YearKey",
            "YearStartDate",
            "YearLabel",
            "YearSort",
            "PeriodGroup",
            "IsLatestYear",
            "YearsSinceStart",
        ],
    )
    write_csv(
        PROCESSED_DIR / "dim_geography.csv",
        sorted(geographies.values(), key=lambda row: (row["GeographyLevel"], row["CountryName"], row["RegionName"], row["GeographyName"])),
        [
            "GeographyKey",
            "GeographyCode",
            "GeographyName",
            "GeographyLevel",
            "RegionName",
            "CountryName",
            "IsLocalAuthority",
            "IsRegionOrCountry",
        ],
    )
    write_csv(
        PROCESSED_DIR / "dim_fuel.csv",
        [{"Fuel": "Electricity"}, {"Fuel": "Gas"}],
        ["Fuel"],
    )
    write_csv(
        PROCESSED_DIR / "dim_sector.csv",
        [
            {"Sector": "Domestic", "SectorSort": 1, "CountsInAdditiveTotal": True},
            {"Sector": "Non-domestic", "SectorSort": 2, "CountsInAdditiveTotal": True},
            {"Sector": "All", "SectorSort": 3, "CountsInAdditiveTotal": False},
        ],
        ["Sector", "SectorSort", "CountsInAdditiveTotal"],
    )
    write_csv(
        PROCESSED_DIR / "dim_electricity_profile.csv",
        [
            {"ElectricityProfile": "Standard domestic", "ProfileSort": 1},
            {"ElectricityProfile": "Economy 7 domestic", "ProfileSort": 2},
        ],
        ["ElectricityProfile", "ProfileSort"],
    )
    write_csv(
        PROCESSED_DIR / "latest_snapshot.csv",
        latest_snapshot,
        [
            "YearKey",
            "GeographyKey",
            "GeographyName",
            "GeographyLevel",
            "RegionName",
            "CountryName",
            "Fuel",
            "ConsumptionGWh",
            "MeanKWhPerMeter",
            "YoYChangePct",
            "ChangeSince2021Pct",
            "MeanChangeSince2021Pct",
            "TrendSignal",
            "EfficiencySignal",
        ],
    )

    quality_report = build_quality_report(fact_rows, profile_rows, geographies)
    (PROCESSED_DIR / "data_quality_report.json").write_text(json.dumps(quality_report, indent=2), encoding="utf-8")
    print(json.dumps(quality_report, indent=2))


if __name__ == "__main__":
    main()
