# Repository Guidelines

## Project Structure & Module Organization

This repository is currently centered on source spreadsheets in [`data/`](/home/martin/repos/trend_data_extractor/data) and high-level notes in [`README.md`](/home/martin/repos/trend_data_extractor/README.md). Keep raw input files in `data/` and treat them as immutable reference inputs. Add extractor code under `src/` as the project grows, organized by dataset or source, for example `src/euda/` or `src/parsers/treatment_demand.py`. Place tests in `tests/` with fixtures in `tests/fixtures/`.

## Build, Test, and Development Commands

There is no build system checked in yet, so contributors should keep automation simple and scriptable.

- `python -m venv .venv && source .venv/bin/activate`: create a local environment.
- `pip install -r requirements.txt`: install dependencies once that file exists.
- `pytest`: run the test suite.
- `python -m src.<module>`: run a parser module directly during development.

If you introduce a task runner such as `Makefile` or `justfile`, document the canonical commands here and in `README.md`.

## Coding Style & Naming Conventions

Prefer Python for extraction code unless the repository adopts another runtime explicitly. Use 4-space indentation, type hints on public functions, and small pure transformation functions where practical. Use `snake_case` for files, functions, and variables; `PascalCase` for classes; and descriptive dataset names such as `drug_related_deaths.py`. Format with `black` and lint with `ruff` if those tools are added.

## Testing Guidelines

Use `pytest` for parser and transformation coverage. Name tests `test_<module>.py` and keep one fixture per source workbook when possible. Favor assertions on normalized output rows, schema shape, and edge cases such as merged cells, missing years, and alternate sheet names. New parsing logic should include tests before or alongside implementation.

## Commit & Pull Request Guidelines

The current history starts with a single `Initial commit`, so adopt short imperative commit messages such as `Add treatment demand parser` or `Normalize prevalence year columns`. Keep commits focused on one dataset or transformation. Pull requests should state the source files affected, the output format changed, and how the result was validated. Include sample rows or schema diffs when extractor output changes.

## Data & Configuration Notes

`data/` is ignored by Git, so do not rely on checked-in spreadsheets for reproducibility. Document required input filenames, workbook versions, and any manual preprocessing in `README.md` or a dedicated config file.
