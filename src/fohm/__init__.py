from pathlib import Path


def is_fohm_workbook(path: Path) -> bool:
    return path.name.endswith("-fohm.xlsx")


__all__ = ["is_fohm_workbook"]
