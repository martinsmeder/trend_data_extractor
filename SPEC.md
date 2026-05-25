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
- JSON canonical shape: dataset-level metadata plus a `series` array, where each series contains shared metadata and an `observations` array of yearly values.
- CSV: export one row per normalized record.
- Prefer long format over wide format for the main dataset.
- Treat JSON and CSV as two renderings of the same underlying observations, not as separately designed datasets.
- The sample structure in `examples/sweden_sample_dataset.json` is the current reference shape.

Canonical JSON schema:

- Top-level required fields:
  - `dataset_id`
  - `title`
  - `description`
  - `scope`
  - `series`
- Top-level `scope` fields:
  - `geography`
  - `included_sources`
  - `is_sample`
- Series-level required fields:
  - `metric`
  - `label`
  - `source`
  - `url`
  - `source_file`
  - `source_sheet`
  - `source_description`
  - `unit`
  - `dimensions`
  - `notes`
  - `observations`
- Series-level optional fields:
  - `note_refs`
  - `series_key`
  - `source_notes_raw`
- Observation-level required fields:
  - `year`
  - `value`
- Observation-level optional fields:
  - `value_text`

Schema decisions finalized for implementation:

- The canonical JSON format is `dataset metadata + series + observations`.
- Shared metadata belongs on the series object, not on every yearly observation.
- `observations` remains the only place where year-value pairs are stored.
- `source_file` and `source_sheet` are retained for provenance.
- `source_notes_raw` is optional and used only when raw note preservation adds value.
- No additional top-level metadata fields are required before implementation begins.

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

Extraction approach:

- Build a deterministic extractor rather than doing ad hoc manual extraction.
- Parse `.xlsx` workbooks directly in code.
- Implement source-specific parsers first, one for `euda` and one for `fohm`.
- Normalize both sources into the shared canonical JSON structure.
- Generate CSV only from the normalized JSON-level records, not from a separate parsing path.

Validation approach:

- Validate that every extracted year comes from an actual source header cell.
- Validate that every observation count aligns with the parsed year columns.
- Validate that each relevant `euda` sheet contains exactly one `Sweden` row used for extraction.
- Validate that `fohm` note blocks and source metadata are captured when present.
- Preserve raw text placeholders such as `..` when values are not numeric.
- Add automated tests using representative fixture workbooks from both source families.
- Manually spot-check a small number of extracted series against the source workbooks before treating output as final.

Open questions:

- Whether to ship only one long CSV or also provide a chart-friendly wide CSV later.
- How aggressively to normalize source labels into canonical dimension values.

## Web Page
