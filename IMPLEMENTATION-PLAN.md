# Implementation Plan

## Dataset / Extractor

Objective: build a deterministic extractor that reads all relevant `.xlsx` files in `data/`, extracts Sweden-only data, normalizes it into the canonical JSON format, and then derives a CSV export from the same underlying records.

Planned steps:

- [x] Finalize the canonical JSON schema.

- Use the sample dataset shape in `examples/sweden_sample_dataset.json` as the starting point.
- Confirm the stable top-level fields and the `series` plus `observations` structure.
- Decide whether any additional metadata fields are required before implementation begins.

- [x] Scaffold the extractor project structure.

- Add `src/` for implementation code.
- Add source-specific modules, likely `src/euda/` and `src/fohm/`.
- Add a small CLI entry point that can run the extraction end to end.

- [x] Implement workbook reading utilities.

- Add shared `.xlsx` reading helpers for workbook, sheet, row, and cell access.
- Handle shared strings, inline strings, numeric cells, and empty cells explicitly.
- Keep parsing logic deterministic and auditable.

- [x] Implement the `euda` parser.

- Detect the title row, source URL row, year header row, and country rows.
- Extract only the `Sweden` row from each relevant sheet.
- Convert the title-path wording into canonical `metric`, `label`, `dimensions`, and `source_description` fields.
- Preserve source-specific irregularities such as note markers where present.

- [ ] Implement the `fohm` parser.

- Detect the title, unit, subgroup headers, year header row, value rows, note block, and source metadata block.
- Extract each Sweden-only series from the workbook structure.
- Clean embedded HTML fragments from note cells.
- Translate or summarize notes into English while preserving raw note text when useful.

- [ ] Normalize extracted output.

- Map both source families into the same canonical JSON shape.
- Keep series-level metadata attached to each series and yearly values in `observations`.
- Preserve non-numeric placeholders through `value_text` when needed.

- [ ] Generate output files.

- Write the canonical JSON dataset.
- Flatten the same normalized records into a long-form CSV export.
- Keep JSON as the single source of truth and avoid a second independent CSV transformation path.

- [ ] Add automated validation.

- Check that extracted years match actual source header cells.
- Check that observation counts align with year columns.
- Check that each relevant `euda` sheet yields exactly one Sweden row.
- Check that `fohm` notes and source metadata are captured when present.
- Check that missing values such as `..` are preserved correctly.

- [ ] Add tests.

- Add `pytest` coverage for one or more representative `euda` workbooks.
- Add `pytest` coverage for one or more representative `fohm` workbooks.
- Assert both structural correctness and exact sample values for selected years.

- [ ] Run end-to-end extraction and review.

- Run the extractor against all current files in `data/`.
- Manually spot-check a handful of generated series against the source workbooks.
- Adjust normalization rules only where source evidence supports the change.

- [ ] Document usage.

- Document input expectations, output locations, and command usage in `README.md`.
- Record any known source-specific assumptions or limitations.

## Web Page
