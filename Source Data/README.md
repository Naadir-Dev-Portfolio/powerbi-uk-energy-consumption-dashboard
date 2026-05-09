# Source Data

This folder contains the repeatable data pipeline for the UK Energy Consumption Dashboard.

## Official public sources

The project uses DESNZ stacked subnational energy consumption CSV files because they are official, public, no-account-required, and designed for analytical users.

- Electricity stacked data page: https://www.gov.uk/government/statistical-data-sets/stacked-electricity-consumption-statistics-data
- Gas stacked data page: https://www.gov.uk/government/statistical-data-sets/stacked-gas-consumption-statistics-data
- Electricity collection: https://www.gov.uk/government/collections/sub-national-electricity-consumption-data
- Gas collection: https://www.gov.uk/government/collections/sub-national-gas-consumption-data

Latest source coverage at build time:

- Electricity: 2005 to 2024, GOV.UK page last updated 18 December 2025.
- Gas: 2005 to 2024, GOV.UK page last updated 19 December 2025 after a 2023 non-domestic gas correction.

## Refresh

Run these from the project root:

```powershell
python "Source Data\download_uk_energy_data.py"
python "Source Data\build_uk_energy_model.py"
```

The first script writes raw source files to `Source Data/raw`. The second script writes model-ready CSV files to `Source Data/processed`.

## Model-ready files

- `fact_energy_consumption.csv`: normalized electricity and gas consumption by year, geography, fuel, and sector.
- `fact_electricity_profile.csv`: Standard domestic vs Economy 7 domestic electricity profile rows where available.
- `dim_date.csv`: annual date dimension for 2005-2024.
- `dim_geography.csv`: Great Britain, countries, English regions, and local authorities.
- `dim_fuel.csv`: electricity and gas.
- `dim_sector.csv`: domestic, non-domestic, and source all-sector rows.
- `dim_electricity_profile.csv`: electricity profile labels.
- `latest_snapshot.csv`: precomputed latest-year trend flags for QA and optional report annotations.
- `data_quality_report.json`: row counts and processing notes.
