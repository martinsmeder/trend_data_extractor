from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path
import re
from typing import Any

from src.workbook_reader import Row, Sheet, load_workbook


COMMON_FOHM_NOTES = [
    "The 2024 statistics are fully included in Sweden's official statistics, while the 2022 release was only partly included.",
    "Survey rounds before 2022 were produced under similar quality requirements but were not formally quality declared.",
    "Values are presented as non-age-standardized percentages.",
]


FOHM_SERIES_CONFIG: dict[str, dict[str, Any]] = {
    "all-drugs-prevalence-fohm.xlsx": {
        "metric": "all_drugs_prevalence",
        "label": "Prevalence of all drug use in the last 12 months, total population aged 16-84",
        "dimensions": {
            "age_group": "16-84",
            "sex": "total",
            "measure_type": "self_reported_prevalence",
            "recall_period": "last_12_months",
            "drug_group": "all_drugs",
        },
        "english_note": "The figures are based on National Public Health Survey questions about cannabis use and use of other narcotic drugs.",
    },
    "cannabis-prevalence-fohm.xlsx": {
        "metric": "cannabis_prevalence",
        "label": "Prevalence of cannabis use in the last 12 months, total population aged 16-84",
        "dimensions": {
            "age_group": "16-84",
            "sex": "total",
            "measure_type": "self_reported_prevalence",
            "recall_period": "last_12_months",
            "drug_group": "cannabis",
        },
        "english_note": "The figures are based on National Public Health Survey questions about cannabis use.",
    },
    "non-cannabis-drugs-prevalence-fohm.xlsx": {
        "metric": "non_cannabis_drugs_prevalence",
        "label": "Prevalence of non-cannabis drug use in the last 12 months, total population aged 16-84",
        "dimensions": {
            "age_group": "16-84",
            "sex": "total",
            "measure_type": "self_reported_prevalence",
            "recall_period": "last_12_months",
            "drug_group": "non_cannabis_drugs",
        },
        "english_note": "The figures are based on National Public Health Survey questions about narcotic drug use other than cannabis.",
    },
    "prescription-drugs-prevalence-fohm.xlsx": {
        "metric": "prescription_drugs_prevalence",
        "label": "Prevalence of non-prescribed narcotic-classified medication misuse in the last 12 months, total population aged 16-84",
        "dimensions": {
            "age_group": "16-84",
            "sex": "total",
            "measure_type": "self_reported_prevalence",
            "recall_period": "last_12_months",
            "drug_group": "prescription_drugs",
        },
        "english_note": "The figures are based on National Public Health Survey questions about using prescribed narcotic-classified medication in a way other than prescribed.",
    },
}


@dataclass(frozen=True)
class ParsedFohmSheet:
    title: str
    population: str
    subgroup: str
    unit_label: str
    value_row_label: str
    years: list[int]
    year_columns: list[int]
    source_url: str
    source_notes_raw: list[str]
    cleaned_notes: list[str]
    values_row: Row


def is_fohm_workbook(path: Path) -> bool:
    return path.name.endswith("-fohm.xlsx")


def extract_fohm_dataset(input_dir: Path) -> dict[str, Any]:
    workbooks = sorted(path for path in input_dir.glob("*-fohm.xlsx") if path.is_file())
    series = [parse_fohm_workbook(path) for path in workbooks]
    return {
        "dataset_id": "sweden-drug-trends-fohm",
        "title": "Sweden drug trends dataset from FOHM workbooks",
        "description": "Normalized Sweden-only dataset extracted from FOHM Excel workbooks.",
        "scope": {
            "geography": "Sweden",
            "included_sources": ["fohm"],
            "is_sample": False,
        },
        "series": series,
    }


def parse_fohm_workbook(path: Path) -> dict[str, Any]:
    workbook = load_workbook(path)
    if len(workbook.sheets) != 1:
        raise ValueError(f"Expected exactly one sheet in {path.name}, found {len(workbook.sheets)}")
    sheet = workbook.sheets[0]
    parsed = parse_fohm_sheet(sheet)
    config = FOHM_SERIES_CONFIG.get(path.name)
    if config is None:
        raise ValueError(f"Missing FOHM series configuration for {path.name}")

    notes = list(COMMON_FOHM_NOTES)
    notes.append(config["english_note"])
    if any("urvalsundersökning bland befolkningen 16 år och äldre" in note for note in parsed.cleaned_notes):
        notes.append(
            "The survey covers the population aged 16 years and older, while 2020 and earlier editions cover ages 16-84."
        )

    return {
        "metric": config["metric"],
        "label": config["label"],
        "source": "fohm",
        "url": parsed.source_url,
        "source_file": path.name,
        "source_sheet": sheet.name,
        "source_description": " / ".join(
            [parsed.title, parsed.population, parsed.subgroup, parsed.value_row_label]
        ),
        "unit": "percent",
        "dimensions": config["dimensions"],
        "notes": notes,
        "series_key": f"fohm:{config['metric']}:sweden",
        "source_notes_raw": parsed.source_notes_raw,
        "observations": build_fohm_observations(parsed),
    }


def parse_fohm_sheet(sheet: Sheet) -> ParsedFohmSheet:
    title = _get_value_at(sheet, 1, 1)
    unit_label = _get_value_at(sheet, 3, 2)
    population = _get_value_at(sheet, 4, 2)
    subgroup = _get_value_at(sheet, 5, 2)
    years_row = _require_row(sheet, 6)
    values_row = _require_row(sheet, 7)
    value_row_label = _get_first_cell_value(values_row)

    years: list[int] = []
    year_columns: list[int] = []
    for column_index in range(2, years_row.max_column + 1):
        value = years_row.get_cell(column_index).value
        if isinstance(value, int):
            years.append(value)
            year_columns.append(column_index)
        elif isinstance(value, str) and value.isdigit():
            years.append(int(value))
            year_columns.append(column_index)

    if not years:
        raise ValueError(f"No year columns found in FOHM sheet {sheet.name}")

    source_url = _extract_source_url(sheet)
    raw_notes = _extract_note_block(sheet)
    cleaned_notes = [_clean_note_text(note) for note in raw_notes]

    return ParsedFohmSheet(
        title=title,
        population=population,
        subgroup=subgroup,
        unit_label=unit_label,
        value_row_label=value_row_label,
        years=years,
        year_columns=year_columns,
        source_url=source_url,
        source_notes_raw=cleaned_notes,
        cleaned_notes=cleaned_notes,
        values_row=values_row,
    )


def build_fohm_observations(parsed: ParsedFohmSheet) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []
    for year, column_index in zip(parsed.years, parsed.year_columns):
        cell = parsed.values_row.get_cell(column_index)
        observation: dict[str, Any] = {"year": year, "value": None}
        if isinstance(cell.value, (int, float)):
            observation["value"] = cell.value
        elif isinstance(cell.value, str):
            observation["value_text"] = cell.value
        observations.append(observation)
    return observations


def validate_fohm_dataset(dataset: dict[str, Any], input_dir: Path) -> list[str]:
    errors: list[str] = []
    series_by_file = {series["source_file"]: series for series in dataset.get("series", [])}
    expected_files = sorted(path.name for path in input_dir.glob("*-fohm.xlsx"))

    if sorted(series_by_file) != expected_files:
        errors.append("Extracted FOHM series files do not match the available FOHM workbooks.")

    for path in sorted(input_dir.glob("*-fohm.xlsx")):
        series = series_by_file.get(path.name)
        if series is None:
            errors.append(f"Missing extracted series for {path.name}.")
            continue

        workbook = load_workbook(path)
        sheet = workbook.sheets[0]
        parsed = parse_fohm_sheet(sheet)
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
            cell = parsed.values_row.get_cell(column_index)
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

        expected_source_description = " / ".join(
            [parsed.title, parsed.population, parsed.subgroup, parsed.value_row_label]
        )
        if series.get("source_description") != expected_source_description:
            errors.append(f"{path.name}: source description does not match source rows.")

        if series.get("source_notes_raw") != parsed.source_notes_raw:
            errors.append(f"{path.name}: raw notes do not match the source note block.")

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


def _get_value_at(sheet: Sheet, row_index: int, column_index: int) -> str:
    row = _require_row(sheet, row_index)
    value = row.get_cell(column_index).value
    if not isinstance(value, str):
        raise ValueError(
            f"Expected text at row {row_index}, column {column_index} in sheet {sheet.name}"
        )
    return value.strip()


def _extract_note_block(sheet: Sheet) -> list[str]:
    note_rows: list[str] = []
    for row in sheet.rows:
        first = row.get_cell(1).value
        if not isinstance(first, str):
            continue
        if row.index <= 7:
            continue
        if first.strip() == "Senaste uppdatering:":
            break
        if first.strip():
            note_rows.append(first)
    return note_rows


def _extract_source_url(sheet: Sheet) -> str:
    source_label_row = _find_row(sheet, lambda row: row.get_cell(1).value == "Källa:")
    if source_label_row is None:
        raise ValueError(f"Could not find source label row in FOHM sheet {sheet.name}")

    for row in sheet.rows:
        if row.index <= source_label_row.index:
            continue
        value = row.get_cell(1).value
        if isinstance(value, str) and value.strip().startswith("http"):
            return value.strip()

    raise ValueError(f"Could not find source URL after source label row in FOHM sheet {sheet.name}")


def _clean_note_text(value: str) -> str:
    text = unescape(value)
    text = re.sub(r"<a [^>]+>.*?</a>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _find_row(sheet: Sheet, predicate: Any) -> Row | None:
    for row in sheet.rows:
        if predicate(row):
            return row
    return None
