# UK Energy Consumption Dashboard Build Guide

## What is already built

- Official DESNZ data is downloaded to `Source Data/raw`.
- Model-ready CSVs are generated in `Source Data/processed`.
- The PBIP semantic model has import tables, relationships, and DAX measures.
- The semantic model indentation fault that broke visuals has been corrected in the fact-table TMDL files.
- The PBIP report visuals are generated directly into PBIR JSON.
- The report has 4 finished pages:
  - Executive Summary
  - National Demand Shift
  - Local Authority Hotspots
  - Consumption Structure
- The report builder and validator live in `.build/build_report.py` and `.build/validate_report.py`.

## Refresh the data layer

Run from the project root:

```powershell
python "Source Data\download_uk_energy_data.py"
python "Source Data\build_uk_energy_model.py"
```

The transform script writes a compact QA summary to `Source Data/processed/data_quality_report.json`.

## Open and refresh in Power BI Desktop

1. Close Power BI Desktop fully before opening the project again. Check the system tray instance too.
2. Open `UK Energy Consumption Dashboard.pbip`.
3. Refresh the semantic model.
4. Confirm these relationships are active:
   - `Fact Energy Consumption[YearKey]` to `Dim Date[YearKey]`
   - `Fact Energy Consumption[GeographyKey]` to `Dim Geography[GeographyKey]`
   - `Fact Energy Consumption[Fuel]` to `Dim Fuel[Fuel]`
   - `Fact Energy Consumption[Sector]` to `Dim Sector[Sector]`
   - `Fact Electricity Profile[YearKey]` to `Dim Date[YearKey]`
   - `Fact Electricity Profile[GeographyKey]` to `Dim Geography[GeographyKey]`
   - `Fact Electricity Profile[ElectricityProfile]` to `Dim Electricity Profile[ElectricityProfile]`
5. Mark `Dim Date` as the date table using `YearStartDate`.
6. Save once the visuals render cleanly.

## Report page build status

### 1. Executive Summary

Already built:

- KPI cards:
  - `Latest Snapshot Label`
  - `Great Britain Latest Consumption GWh`
  - `Great Britain Latest YoY Change %`
  - `Great Britain Latest vs 2021 Change %`
  - `Great Britain Structural Change Signal`
- Synced year slicer:
  - `Dim Date[YearStartDate]`
- Line chart:
  - `Great Britain Electricity Consumption GWh`
  - `Great Britain Gas Consumption GWh`
- Bar chart:
  - `Great Britain Latest Consumption GWh` by `Dim Sector[Sector]`
- Pivot table:
  - latest electricity, gas, and domestic share by `Dim Geography[RegionName]`

### 2. National Demand Shift

Already built:

- KPI cards:
  - `Latest Snapshot Label`
  - `Great Britain Latest Consumption GWh`
  - `Great Britain Latest YoY Change %`
  - `Great Britain Latest Electricity Share %`
  - `Great Britain Latest Gas Share %`
- Synced year slicer:
  - `Dim Date[YearStartDate]`
- Line chart:
  - `Great Britain Consumption GWh`
  - `Great Britain 3Y Rolling Avg GWh`
- Bar chart:
  - latest Great Britain fuel split by `Dim Fuel[Fuel]`
- Bar chart:
  - latest regional total from local-authority roll-up
- Pivot table:
  - `Latest Consumption GWh`, `Latest YoY Change %`, `Ten Year CAGR`, `Share of Great Britain %`

### 3. Local Authority Hotspots

Already built:

- Synced year slicer:
  - `Dim Date[YearStartDate]`
- Slicers:
  - `Dim Fuel[Fuel]`
  - `Dim Sector[Sector]`
  - `Dim Geography[CountryName]`
- KPI cards:
  - `Latest Snapshot Label`
  - `Filtered Local Authorities`
  - `Top Local Authority Label`
  - `Top Local Authority Latest GWh`
  - `Top Local Authority Share of Great Britain %`
- Scatter chart:
  - `Latest Mean kWh per meter` vs `Latest vs 2021 Change %`
  - size: `Latest Consumption GWh`
- Treemap:
  - latest regional hotspot context from local-authority data
- Table:
  - `GeographyName`, `Latest Consumption GWh`, `Latest Mean kWh per meter`, `Latest vs 2021 Change %`, `Local Authority Demand Rank`

### 4. Consumption Structure

Already built:

- KPI cards:
  - `Latest Snapshot Label`
  - `Great Britain Latest Domestic Mix Share %`
  - `Great Britain Latest Non-domestic Mix Share %`
  - `Great Britain Latest Standard Domestic GWh`
  - `Great Britain Latest Economy 7 Domestic GWh`
- Synced year slicer:
  - `Dim Date[YearStartDate]`
- Line chart:
  - `Great Britain Domestic Consumption GWh`
  - `Great Britain Non-domestic Consumption GWh`
- Bar chart:
  - latest Great Britain fuel split by `Dim Fuel[Fuel]`
- Line chart:
  - `Great Britain Standard Domestic GWh`
  - `Great Britain Economy 7 Domestic GWh`
- Pivot table:
  - regional structure and efficiency diagnostics

## Important modelling notes

- `Sector = All` rows are retained because DESNZ publishes source all-sector mean and median metrics. The main DAX measures avoid double-counting by summing only domestic and non-domestic rows when no single sector is selected.
- Local authority history includes historical and current geography codes. For latest-year local analysis, filter `Dim Date[IsLatestYear] = True` or use the latest measures.
- Gas data are weather-corrected in the DESNZ subnational publication and exclude unique sites for consistent time series.

## Remaining manual GUI tasks

- Close Power BI Desktop fully before regenerating PBIR files.
- Refresh the model in Power BI Desktop.
- Mark the date table.
- Confirm the 4 pages render without red Xs.
- Check that the synced year slicer filters all four pages.
- Save the PBIP once Desktop has rebound the regenerated visual metadata.
