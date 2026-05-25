# Spec

## Dataset / Extractor

Goal: extract all Sweden-only data from the `fohm` and `euda` workbooks and publish it as one JSON dataset and one CSV dataset.

Recommended approach:

- Define one canonical internal record model first.
- Generate JSON directly from that model.
- Generate CSV from the same normalized records.
- Avoid designing JSON and CSV separately unless a concrete downstream need forces them apart.

Why this approach:

- It keeps one source of truth for parsing and validation.
- JSON can preserve richer structure such as notes, dimensions, and provenance.
- CSV works best as a flattened export of the same records.

Proposed record shape:

- `metric`: canonical metric id, for example `drug_related_deaths` or `treatment_demand`
- `label`: human-readable English label for exactly what is being measured, for example `Total number of overdose deaths`
- `source`: `euda` or `fohm`
- `url`: URL for the source table or workbook
- `source_file`: local workbook filename
- `source_sheet`: worksheet name
- `year`: numeric year
- `value`: numeric value when available
- `value_text`: raw source value when a cell is not cleanly numeric
- `unit`: for example `count`, `percent`, or other source-specific unit
- `dimensions`: extra breakdown fields such as sex, age group, drug type, entrant type, recall period, or population segment
- `notes`: note text attached to the record or series
- `note_refs`: note markers from the source, if present
- `series_key`: stable identifier for a time series across years
- `source_description`: raw source wording from the workbook, preserved for traceability

Recommended output design:

- JSON: make this the canonical output and preserve the full normalized structure.
- CSV: export one row per normalized record.
- Prefer long format over wide format for the main dataset.
- Treat JSON and CSV as two renderings of the same underlying observations, not as separately designed datasets.

Labeling guidance:

- Keep a short canonical `metric` id for grouping related series.
- Use `label` for the user-facing English description of the specific series.
- Preserve the raw workbook wording in `source_description` so the transformation remains auditable.
- Example: `metric = drug_related_deaths`, `label = Total number of overdose deaths`, `source_description = Overdose deaths > Trends > National definition > Number of deaths > Total`
- Example: `metric = all_drugs_prevalence`, `label = Total prevalence of all drugs, age 16-84`, `source_description = Narkotikaanvändning (självrapporterat) efter ålder, kön och år. Andel (procent). / Totalt 16-84 år / Totalt / Senaste året`

Notes handling:

- Keep notes as explicit fields.
- Translate or summarize Swedish source notes into English for `notes`.
- Preserve raw note text separately only if needed later.
- Flatten notes into CSV text fields so no information is lost.
- If notes apply to an entire series rather than a single year, they may repeat across yearly rows in CSV.

Observed source patterns:

- `euda` sheets typically provide a title row, a source URL row, a header row of years, and country rows. For this project, only the `Sweden` row is extracted.
- `fohm` sheets typically provide a title, unit, subgroup rows, year headers, one or more value rows, and then workbook-level notes and source metadata within the same sheet.
- `fohm` notes can contain HTML fragments in the cell text and should be cleaned during extraction.

Open questions:

- Whether to ship only one long CSV or also provide a chart-friendly wide CSV later.
- How aggressively to normalize source labels into canonical dimension values.

## Web Page
