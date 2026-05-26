from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.euda import extract_euda_dataset, is_euda_workbook, validate_euda_dataset
from src.fohm import extract_fohm_dataset, is_fohm_workbook, validate_fohm_dataset
from src.workbook_reader import load_workbook


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Trend data extractor CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect workbook structure and print a JSON summary.",
    )
    inspect_parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing .xlsx files.",
    )
    inspect_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output.",
    )

    extract_parser = subparsers.add_parser(
        "extract",
        help="Run the current extraction scaffold and write JSON output.",
    )
    extract_parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing .xlsx files.",
    )
    extract_parser.add_argument(
        "output",
        type=Path,
        help="Path to the JSON output file.",
    )
    extract_parser.add_argument(
        "--source",
        choices=["euda", "fohm"],
        default="euda",
        help="Source family to extract.",
    )

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate extracted dataset output against source workbooks.",
    )
    validate_parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing .xlsx files.",
    )
    validate_parser.add_argument(
        "dataset",
        type=Path,
        help="Path to the extracted JSON dataset file.",
    )
    validate_parser.add_argument(
        "--source",
        choices=["euda", "fohm"],
        default="euda",
        help="Source family to validate.",
    )

    return parser


def summarize_workbook(path: Path) -> dict[str, Any]:
    workbook = load_workbook(path)
    detected_source = "unknown"
    if is_euda_workbook(path):
        detected_source = "euda"
    elif is_fohm_workbook(path):
        detected_source = "fohm"

    return {
        "file": path.name,
        "source": detected_source,
        "sheet_count": len(workbook.sheets),
        "sheets": [
            {
                "name": sheet.name,
                "row_count": len(sheet.rows),
                "max_column": sheet.max_column,
                "preview": sheet.preview_values(limit=5),
            }
            for sheet in workbook.sheets
        ],
    }


def inspect_command(input_dir: Path, pretty: bool) -> int:
    summaries = summarize_directory(input_dir)
    indent = 2 if pretty else None
    print(json.dumps({"workbooks": summaries}, indent=indent, ensure_ascii=False))
    return 0


def extract_command(input_dir: Path, output: Path, source: str) -> int:
    if source == "euda":
        payload = extract_euda_dataset(input_dir)
    elif source == "fohm":
        payload = extract_fohm_dataset(input_dir)
    else:
        raise ValueError(f"Unsupported source: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return 0


def validate_command(input_dir: Path, dataset: Path, source: str) -> int:
    payload = json.loads(dataset.read_text())
    if source == "euda":
        errors = validate_euda_dataset(payload, input_dir)
    elif source == "fohm":
        errors = validate_fohm_dataset(payload, input_dir)
    else:
        raise ValueError(f"Unsupported source: {source}")
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2, ensure_ascii=False))
        return 1
    print(json.dumps({"valid": True, "errors": []}, indent=2, ensure_ascii=False))
    return 0


def summarize_directory(input_dir: Path) -> list[dict[str, Any]]:
    return [summarize_workbook(path) for path in sorted(input_dir.glob("*.xlsx"))]


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "inspect":
        return inspect_command(args.input_dir, args.pretty)
    if args.command == "extract":
        return extract_command(args.input_dir, args.output, args.source)
    if args.command == "validate":
        return validate_command(args.input_dir, args.dataset, args.source)

    parser.error(f"Unsupported command: {args.command}")
    return 2
