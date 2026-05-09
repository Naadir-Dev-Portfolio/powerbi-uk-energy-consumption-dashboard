from __future__ import annotations

import json
import ssl
import sys
import time
import urllib.request
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
RAW_DIR = BASE_DIR / "raw"

SOURCES = [
    {
        "name": "Electricity consumption by Local Authority (LA), 2005 to 2024",
        "fuel": "Electricity",
        "geography": "Local Authority",
        "page_url": "https://www.gov.uk/government/statistical-data-sets/stacked-electricity-consumption-statistics-data",
        "download_url": "https://assets.publishing.service.gov.uk/media/694295bd9273c48f554cf4ef/elec_LA_stacked_2005-2024.csv",
        "file_name": "elec_LA_stacked_2005-2024.csv",
        "publisher": "Department for Energy Security and Net Zero",
        "release_note": "Stacked CSV time series for 2005 to 2024. GOV.UK page last updated 18 December 2025.",
    },
    {
        "name": "Electricity consumption by Region, 2005 to 2024",
        "fuel": "Electricity",
        "geography": "Region",
        "page_url": "https://www.gov.uk/government/statistical-data-sets/stacked-electricity-consumption-statistics-data",
        "download_url": "https://assets.publishing.service.gov.uk/media/6942957636f089d38be1f1f8/elec_region_stacked_2005-2024.csv",
        "file_name": "elec_region_stacked_2005-2024.csv",
        "publisher": "Department for Energy Security and Net Zero",
        "release_note": "Stacked CSV time series for 2005 to 2024. GOV.UK page last updated 18 December 2025.",
    },
    {
        "name": "Gas consumption by Local Authority (LA), 2005 to 2024",
        "fuel": "Gas",
        "geography": "Local Authority",
        "page_url": "https://www.gov.uk/government/statistical-data-sets/stacked-gas-consumption-statistics-data",
        "download_url": "https://assets.publishing.service.gov.uk/media/694579d472075a1d4a508994/gas_LA_stacked_2005-2024.csv",
        "file_name": "gas_LA_stacked_2005-2024.csv",
        "publisher": "Department for Energy Security and Net Zero",
        "release_note": "Stacked CSV time series for 2005 to 2024. GOV.UK page last updated 19 December 2025 after a 2023 non-domestic gas correction.",
    },
    {
        "name": "Gas consumption by Region, 2005 to 2024",
        "fuel": "Gas",
        "geography": "Region",
        "page_url": "https://www.gov.uk/government/statistical-data-sets/stacked-gas-consumption-statistics-data",
        "download_url": "https://assets.publishing.service.gov.uk/media/694579c81a2e540ccd8a542a/gas_region_stacked_2005-2024.csv",
        "file_name": "gas_region_stacked_2005-2024.csv",
        "publisher": "Department for Energy Security and Net Zero",
        "release_note": "Stacked CSV time series for 2005 to 2024. GOV.UK page last updated 19 December 2025 after a 2023 non-domestic gas correction.",
    },
]


def repo_relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT_DIR).as_posix()
    except ValueError:
        return path.name


def download(url: str, target: Path, retries: int = 3) -> None:
    context = ssl.create_default_context()
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (portfolio-dashboard-data-refresh; contact: local project)",
        },
    )

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, context=context, timeout=90) as response:
                data = response.read()
            target.write_bytes(data)
            return
        except Exception:
            if attempt == retries:
                raise
            time.sleep(2 * attempt)


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = []

    for source in SOURCES:
        target = RAW_DIR / source["file_name"]
        print(f"Downloading {source['name']} -> {target}")
        download(source["download_url"], target)
        downloaded.append({**source, "local_path": repo_relative_path(target), "bytes": target.stat().st_size})

    metadata_path = BASE_DIR / "source_metadata.json"
    metadata_path.write_text(json.dumps(downloaded, indent=2), encoding="utf-8")
    print(f"Wrote metadata to {repo_relative_path(metadata_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
