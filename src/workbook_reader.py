from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"a": MAIN_NS, "r": REL_NS, "pr": PACKAGE_REL_NS}


def column_name_to_index(name: str) -> int:
    index = 0
    for char in name:
        index = index * 26 + (ord(char.upper()) - ord("A") + 1)
    return index


def split_cell_reference(reference: str) -> tuple[int, int]:
    letters = []
    digits = []
    for char in reference:
        if char.isalpha():
            letters.append(char)
        elif char.isdigit():
            digits.append(char)
    if not letters or not digits:
        raise ValueError(f"Invalid cell reference: {reference}")
    return int("".join(digits)), column_name_to_index("".join(letters))


def coerce_numeric(value: str) -> int | float:
    number = float(value)
    if number.is_integer():
        return int(number)
    return number


@dataclass(frozen=True)
class Cell:
    reference: str
    row_index: int
    column_index: int
    value: str | int | float | bool | None
    raw_value: str | None
    cell_type: str

    @property
    def is_empty(self) -> bool:
        return self.cell_type == "empty"


@dataclass(frozen=True)
class Row:
    index: int
    cells: tuple[Cell, ...]
    max_column: int

    def get_cell(self, column_index: int) -> Cell:
        for cell in self.cells:
            if cell.column_index == column_index:
                return cell
        return Cell(
            reference=f"{column_index}:{self.index}",
            row_index=self.index,
            column_index=column_index,
            value=None,
            raw_value=None,
            cell_type="empty",
        )

    def values(self, include_empty: bool = True) -> list[str | int | float | bool | None]:
        if not include_empty:
            return [cell.value for cell in self.cells]
        return [self.get_cell(column_index).value for column_index in range(1, self.max_column + 1)]


@dataclass(frozen=True)
class Sheet:
    name: str
    rows: tuple[Row, ...]
    max_column: int

    def get_row(self, row_index: int) -> Row | None:
        for row in self.rows:
            if row.index == row_index:
                return row
        return None

    def preview_values(self, limit: int = 5) -> list[list[str | int | float | bool | None]]:
        return [row.values() for row in self.rows[:limit]]


@dataclass(frozen=True)
class Workbook:
    path: Path
    sheets: tuple[Sheet, ...]

    def get_sheet(self, name: str) -> Sheet | None:
        for sheet in self.sheets:
            if sheet.name == name:
                return sheet
        return None


def load_workbook(path: Path) -> Workbook:
    with ZipFile(path) as archive:
        workbook_xml = ET.fromstring(archive.read("xl/workbook.xml"))
        workbook_rels = _parse_relationships(archive.read("xl/_rels/workbook.xml.rels"))
        shared_strings = _parse_shared_strings(archive)

        sheets = []
        for sheet_element in workbook_xml.find("a:sheets", NS) or []:
            name = sheet_element.attrib["name"]
            relationship_id = sheet_element.attrib[f"{{{REL_NS}}}id"]
            target = workbook_rels[relationship_id]
            sheet_path = _normalize_xl_path(target)
            sheet_xml = ET.fromstring(archive.read(sheet_path))
            sheets.append(_parse_sheet(name=name, root=sheet_xml, shared_strings=shared_strings))

    return Workbook(path=path, sheets=tuple(sheets))


def _parse_relationships(xml_bytes: bytes) -> dict[str, str]:
    root = ET.fromstring(xml_bytes)
    return {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in root.findall("pr:Relationship", NS)
    }


def _normalize_xl_path(target: str) -> str:
    normalized = target.lstrip("/")
    if normalized.startswith("xl/"):
        return normalized
    return f"xl/{normalized}"


def _parse_shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []

    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    strings = []
    for item in root.findall("a:si", NS):
        text = "".join(node.text or "" for node in item.iterfind(".//a:t", NS))
        strings.append(text)
    return strings


def _parse_sheet(name: str, root: ET.Element, shared_strings: list[str]) -> Sheet:
    rows = []
    max_column = 0

    for row_element in root.findall(".//a:sheetData/a:row", NS):
        cells = []
        row_max_column = 0
        for cell_element in row_element.findall("a:c", NS):
            cell = _parse_cell(cell_element, shared_strings)
            cells.append(cell)
            row_max_column = max(row_max_column, cell.column_index)
        row_index = int(row_element.attrib["r"])
        max_column = max(max_column, row_max_column)
        rows.append(Row(index=row_index, cells=tuple(cells), max_column=row_max_column))

    normalized_rows = tuple(
        Row(index=row.index, cells=row.cells, max_column=max_column) for row in rows
    )
    return Sheet(name=name, rows=normalized_rows, max_column=max_column)


def _parse_cell(cell_element: ET.Element, shared_strings: list[str]) -> Cell:
    reference = cell_element.attrib["r"]
    row_index, column_index = split_cell_reference(reference)
    cell_type = cell_element.attrib.get("t", "number")

    value_element = cell_element.find("a:v", NS)
    inline_element = cell_element.find("a:is", NS)

    if value_element is None and inline_element is None:
        return Cell(
            reference=reference,
            row_index=row_index,
            column_index=column_index,
            value=None,
            raw_value=None,
            cell_type="empty",
        )

    if cell_type == "s" and value_element is not None:
        raw_value = value_element.text or ""
        return Cell(
            reference=reference,
            row_index=row_index,
            column_index=column_index,
            value=shared_strings[int(raw_value)],
            raw_value=raw_value,
            cell_type="shared_string",
        )

    if cell_type == "inlineStr" and inline_element is not None:
        value = "".join(node.text or "" for node in inline_element.iterfind(".//a:t", NS))
        return Cell(
            reference=reference,
            row_index=row_index,
            column_index=column_index,
            value=value,
            raw_value=value,
            cell_type="inline_string",
        )

    if cell_type == "b" and value_element is not None:
        raw_value = value_element.text or "0"
        return Cell(
            reference=reference,
            row_index=row_index,
            column_index=column_index,
            value=raw_value == "1",
            raw_value=raw_value,
            cell_type="boolean",
        )

    if cell_type in {"str", "e"} and value_element is not None:
        raw_value = value_element.text or ""
        return Cell(
            reference=reference,
            row_index=row_index,
            column_index=column_index,
            value=raw_value,
            raw_value=raw_value,
            cell_type="string",
        )

    raw_value = value_element.text if value_element is not None else ""
    return Cell(
        reference=reference,
        row_index=row_index,
        column_index=column_index,
        value=coerce_numeric(raw_value or "0"),
        raw_value=raw_value,
        cell_type="number",
    )
