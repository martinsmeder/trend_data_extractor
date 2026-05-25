from pathlib import Path


def is_euda_workbook(path: Path) -> bool:
    return path.name.endswith("-euda.xlsx")


__all__ = ["is_euda_workbook"]
