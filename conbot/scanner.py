from pathlib import Path
from typing import Iterable

def get_compound_extension(path: Path) -> str:
    """Returns the compound extension of a file, e.g., '.tar.gz' or '.md'."""
    # This handles things like .tar.gz
    # For conbot, we mainly care about our specific supported extensions, but doing it generally:
    suffixes = path.suffixes
    if not suffixes:
        return ""
    return "".join(suffixes).lower()

def scan_directory(directory: Path | str = ".") -> list[Path]:
    """Returns a list of all files in the directory, excluding dotfiles."""
    dir_path = Path(directory)
    files = []
    for item in dir_path.iterdir():
        if item.is_file() and not item.name.startswith("."):
            files.append(item)
    return files

def get_files_by_extension(files: Iterable[Path]) -> dict[str, list[Path]]:
    """Groups a list of files by their compound extension (lowercase)."""
    grouped: dict[str, list[Path]] = {}
    for f in files:
        ext = get_compound_extension(f)
        if ext:
            grouped.setdefault(ext, []).append(f)
    return grouped
