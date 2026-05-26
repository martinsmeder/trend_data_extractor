from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from src.workbook_reader import Row, Sheet, load_workbook


SWEDEN_NAME = "Sweden"


EUDA_SERIES_CONFIG: dict[str, dict[str, Any]] = {
    "drug-law-offences-euda.xlsx": {
        "metric": "drug_law_offences",
        "label": "Total number of drug law offences",
        "unit": "count",
        "dimensions": {
            "measure_type": "number_of_dlos",
            "offence_scope": "offences",
            "drug_group": "total",
        },
    },
    "drug-related-deaths-euda.xlsx": {
        "metric": "drug_related_deaths",
        "label": "Total number of overdose deaths",
        "unit": "count",
        "dimensions": {
            "measure_type": "number_of_deaths",
            "definition_scope": "national_definition",
            "drug_group": "total",
        },
    },
    "treatment-demand-euda.xlsx": {
        "metric": "treatment_demand",
        "label": "Total number of clients entering treatment for all drugs",
        "unit": "count",
        "dimensions": {
            "measure_type": "number_of_clients",
            "entrant_type": "all_entrants",
            "drug_group": "all_drugs",
        },
    },
}


@dataclass(frozen=True)
class ParsedEudaSheet:
    title: str
    source_url: str
    years: list[int]
    year_columns: list[int]
    sweden_row: Row
    row_label: str
    footnotes: list[str]
    sweden_notes: list[str]
    note_refs: list[str]


def is_euda_workbook(path: Path) -> bool:
    return path.name.endswith("-euda.xlsx")


def extract_euda_dataset(input_dir: Path) -> dict[str, Any]:
    workbooks = sorted(path for path in input_dir.glob("*-euda.xlsx") if path.is_file())
    series = [parse_euda_workbook(path) for path in workbooks]
    return {
        "dataset_id": "sweden-drug-trends-euda",
        "title": "Sweden drug trends dataset from EUDA workbooks",
        "description": "Normalized Sweden-only dataset extracted from EUDA Excel workbooks.",
        "scope": {
            "geography": "Sweden",
            "included_sources": ["euda"],
            "is_sample": False,
        },
        "series": series,
    }


def parse_euda_workbook(path: Path) -> dict[str, Any]:
    workbook = load_workbook(path)
    if len(workbook.sheets) != 1:
        raise ValueError(f"Expected exactly one sheet in {path.name}, found {len(workbook.sheets)}")
    sheet = workbook.sheets[0]
    parsed = parse_euda_sheet(sheet)
    config = EUDA_SERIES_CONFIG.get(path.name)
    if config is None:
        raise ValueError(f"Missing EUDA series configuration for {path.name}")

    return {
        "metric": config["metric"],
        "label": config["label"],
        "source": "euda",
        "url": parsed.source_url,
        "source_file": path.name,
        "source_sheet": sheet.name,
        "source_description": parsed.title,
        "unit": config["unit"],
        "dimensions": config["dimensions"],
        "notes": build_notes(parsed),
        "note_refs": parsed.note_refs,
        "series_key": f"euda:{config['metric']}:sweden",
        "observations": build_observations(parsed),
    }


def parse_euda_sheet(sheet: Sheet) -> ParsedEudaSheet:
    title = _get_first_cell_value(_require_row(sheet, 2))
    source_url = _extract_source_url(_get_first_cell_value(_require_row(sheet, 3)))
    header_row = _find_row(sheet, lambda row: row.get_cell(1).value == "Country")
    if header_row is None:
        raise ValueError(f"Could not find EUDA header row in sheet {sheet.name}")

    years: list[int] = []
    year_columns: list[int] = []
    for column_index in range(2, header_row.max_column + 1):
        value = header_row.get_cell(column_index).value
        if isinstance(value, int):
            years.append(value)
            year_columns.append(column_index)

    if not years:
        raise ValueError(f"No year columns found in EUDA sheet {sheet.name}")

    sweden_rows = [
        row for row in sheet.rows if _normalize_country_name(_get_first_cell_value(row)) == SWEDEN_NAME
    ]
    if len(sweden_rows) != 1:
        raise ValueError(
            f"Expected exactly one Sweden row in EUDA sheet {sheet.name}, found {len(sweden_rows)}"
        )
    sweden_row = sweden_rows[0]
    row_label = _get_first_cell_value(sweden_row)

    footnotes = _extract_footnotes(sheet)
    sweden_notes = [note for note in footnotes if note.startswith("Sweden:")]
    note_refs = _extract_note_refs(row_label)

    return ParsedEudaSheet(
        title=title,
        source_url=source_url,
        years=years,
        year_columns=year_columns,
        sweden_row=sweden_row,
        row_label=row_label,
        footnotes=footnotes,
        sweden_notes=sweden_notes,
        note_refs=note_refs,
    )


def build_observations(parsed: ParsedEudaSheet) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for year, column_index in zip(parsed.years, parsed.year_columns):
        cell = parsed.sweden_row.get_cell(column_index)
        observation: dict[str, Any] = {"year": year, "value": None}
        if isinstance(cell.value, (int, float)):
            observation["value"] = cell.value
        elif isinstance(cell.value, str):
            observation["value_text"] = cell.value
        observations.append(observation)
    return observations


def build_notes(parsed: ParsedEudaSheet) -> list[str]:
    notes = [
        "Values come from the EUDA workbook and include only the Sweden row.",
    ]
    notes.extend(parsed.sweden_notes)
    if parsed.note_refs and not parsed.sweden_notes:
        notes.append("The source row includes note markers that should be reviewed alongside the workbook footnotes.")
    return notes


def validate_euda_dataset(dataset: dict[str, Any], input_dir: Path) -> list[str]:
    errors: list[str] = []
    series_by_file = {series["source_file"]: series for series in dataset.get("series", [])}

    expected_files = sorted(path.name for path in input_dir.glob("*-euda.xlsx"))
    if sorted(series_by_file) != expected_files:
        errors.append(
            "Extracted EUDA series files do not match the available EUDA workbooks."
        )

    for path in sorted(input_dir.glob("*-euda.xlsx")):
        series = series_by_file.get(path.name)
        if series is None:
            errors.append(f"Missing extracted series for {path.name}.")
            continue

        workbook = load_workbook(path)
        sheet = workbook.sheets[0]
        parsed = parse_euda_sheet(sheet)
        observations = series.get("observations", [])

        if len(observations) != len(parsed.years):
            errors.append(
                f"{path.name}: observation count {len(observations)} does not match "
                f"year column count {len(parsed.years)}."
            )

        observation_years = [observation.get("year") for observation in observations]
        if observation_years != parsed.years:
            errors.append(f"{path.name}: extracted years do not match source header years.")

        for observation, column_index in zip(observations, parsed.year_columns):
            cell = parsed.sweden_row.get_cell(column_index)
            expected_value = cell.value if isinstance(cell.value, (int, float)) else None
            actual_value = observation.get("value")
            if actual_value != expected_value:
                errors.append(
                    f"{path.name}: year {observation.get('year')} value {actual_value} "
                    f"does not match source value {expected_value}."
                )
            if isinstance(cell.value, str) and observation.get("value_text") != cell.value:
                errors.append(
                    f"{path.name}: year {observation.get('year')} text value does not match source."
                )

        if series.get("url") != parsed.source_url:
            errors.append(f"{path.name}: source URL does not match workbook content.")

        if series.get("source_description") != parsed.title:
            errors.append(f"{path.name}: source description does not match workbook title.")

        if parsed.note_refs != series.get("note_refs", []):
            errors.append(f"{path.name}: note refs do not match the Sweden row markers.")

    return errors


def _require_row(sheet: Sheet, row_index: int) -> Row:
    row = sheet.get_row(row_index)
    if row is None:
        raise ValueError(f"Missing expected row {row_index} in sheet {sheet.name}")
    return row


def _get_first_cell_value(row: Row) -> str:
    value = row.get_cell(1).value
    if not isinstance(value, str):
        raise ValueError(f"Expected text in first cell of row {row.index}")
    return value.strip()


def _find_row(sheet: Sheet, predicate: Any) -> Row | None:
    for row in sheet.rows:
        if predicate(row):
            return row
    return None


def _extract_source_url(value: str) -> str:
    if value.startswith("Source:"):
        return value.split("Source:", 1)[1].strip()
    return value.strip()


def _normalize_country_name(value: str) -> str:
    return value.replace("*", "").strip()


def _extract_footnotes(sheet: Sheet) -> list[str]:
    footnotes: list[str] = []
    for row in sheet.rows:
        value = row.get_cell(1).value
        if isinstance(value, str) and re.match(r"^\(\d+\)\s+", value):
            footnotes.append(_strip_footnote_index(value))
    return footnotes


def _strip_footnote_index(value: str) -> str:
    return re.sub(r"^\(\d+\)\s*", "", value).strip()


def _extract_note_refs(row_label: str) -> list[str]:
    refs: list[str] = []
    if "*" in row_label:
        refs.append("*")
    return refs
