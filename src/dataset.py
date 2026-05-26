from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from src.euda import extract_euda_dataset
from src.fohm import extract_fohm_dataset


def build_combined_dataset(input_dir: Path) -> dict[str, Any]:
    euda_dataset = extract_euda_dataset(input_dir)
    fohm_dataset = extract_fohm_dataset(input_dir)

    series = sorted(
        [_simplify_series(item) for item in [*euda_dataset["series"], *fohm_dataset["series"]]],
        key=lambda item: (item["source"], item["metric"], item["label"]),
    )

    return {
        "dataset_id": "sweden-drug-trends",
        "title": "Sweden drug trends dataset",
        "description": "Normalized Sweden-only dataset extracted from EUDA and FOHM Excel workbooks.",
        "scope": {
            "geography": "Sweden",
            "included_sources": ["euda", "fohm"],
        },
        "series": series,
    }


def _simplify_series(series: dict[str, Any]) -> dict[str, Any]:
    simplified = {
        "metric": series["metric"],
        "label": series["label"],
        "source": series["source"],
        "url": series["url"],
        "unit": series["unit"],
        "dimensions": series.get("dimensions", {}),
        "notes": series.get("notes", []),
        "observations": [_simplify_observation(item) for item in series.get("observations", [])],
    }
    return simplified


def _simplify_observation(observation: dict[str, Any]) -> dict[str, Any]:
    simplified = {
        "year": observation["year"],
        "value": observation.get("value"),
    }
    if "value_text" in observation:
        simplified["value_text"] = observation["value_text"]
    return simplified


def dataset_to_csv_rows(dataset: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    series = dataset.get("series", [])
    dimension_keys = sorted(
        {
            key
            for item in series
            for key in item.get("dimensions", {}).keys()
        }
    )

    fieldnames = [
        "metric",
        "label",
        "source",
        "url",
        "unit",
        "year",
        "value",
        "value_text",
        "notes",
        *dimension_keys,
    ]

    rows: list[dict[str, Any]] = []
    for item in series:
        base_row = {
            "metric": item.get("metric"),
            "label": item.get("label"),
            "source": item.get("source"),
            "url": item.get("url"),
            "unit": item.get("unit"),
            "notes": json.dumps(item.get("notes", []), ensure_ascii=False),
        }

        for key in dimension_keys:
            base_row[key] = item.get("dimensions", {}).get(key)

        for observation in item.get("observations", []):
            row = dict(base_row)
            row["year"] = observation.get("year")
            row["value"] = observation.get("value")
            row["value_text"] = observation.get("value_text")
            rows.append(row)

    return fieldnames, rows


def write_json_dataset(dataset: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(dataset, indent=2, ensure_ascii=False) + "\n")


def write_csv_dataset(dataset: dict[str, Any], output_path: Path) -> None:
    fieldnames, rows = dataset_to_csv_rows(dataset)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
