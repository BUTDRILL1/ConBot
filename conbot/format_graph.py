from dataclasses import dataclass
from typing import Optional

@dataclass
class ConversionRule:
    source_exts: list[str]
    target_exts: list[str]
    engine: str
    warning: Optional[str] = None
    
# Mapping extensions to Categories
CATEGORY_EXTS = {
    "Document": [".md", ".html", ".docx", ".doc", ".odt", ".rtf", ".pdf", ".epub"],
    "Image": [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".heic", ".heif"],
    "Spreadsheet": [".xlsx", ".xls", ".csv", ".ods"],
    "Video": [".mp4", ".mkv", ".mov", ".webm", ".avi", ".flv", ".wmv"],
    "Audio": [".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg"]
}

# The matrix from TRD
CONVERSION_RULES = [
    ConversionRule(
        source_exts=[".md"],
        target_exts=[".pdf", ".docx", ".html", ".epub"],
        engine="pandoc"
    ),
    ConversionRule(
        source_exts=[".docx"],
        target_exts=[".pdf"],
        engine="libreoffice"
    ),
    ConversionRule(
        source_exts=[".docx"],
        target_exts=[".epub"],
        engine="pandoc",
        warning="Converting .docx to .epub may not preserve custom paragraph styles or heading structure correctly."
    ),
    ConversionRule(
        source_exts=[".doc", ".odt", ".rtf"],
        target_exts=[".pdf", ".docx", ".html", ".epub"],
        engine="libreoffice"
    ),
    ConversionRule(
        source_exts=[".xlsx", ".ods"],
        target_exts=[".pdf"],
        engine="libreoffice"
    ),
    ConversionRule(
        source_exts=[".xls"],
        target_exts=[".xlsx", ".csv", ".pdf"],
        engine="libreoffice"
    ),
    ConversionRule(
        source_exts=[".xlsx"],
        target_exts=[".csv"],
        engine="spreadsheets",
        warning="Dates may become serial numbers; multi-sheet workbooks fan out to one CSV per sheet."
    ),
    ConversionRule(
        source_exts=[".csv"],
        target_exts=[".xlsx"],
        engine="spreadsheets"
    ),
    ConversionRule(
        source_exts=CATEGORY_EXTS["Image"],
        target_exts=CATEGORY_EXTS["Image"],
        engine="image"
    ),
    ConversionRule(
        source_exts=CATEGORY_EXTS["Image"],
        target_exts=[".pdf"],
        engine="image"
    ),
    ConversionRule(
        source_exts=CATEGORY_EXTS["Video"],
        target_exts=CATEGORY_EXTS["Video"],
        engine="ffmpeg"
    ),
    ConversionRule(
        source_exts=CATEGORY_EXTS["Audio"],
        target_exts=CATEGORY_EXTS["Audio"],
        engine="ffmpeg"
    )
]

def get_category_for_ext(ext: str) -> str | None:
    ext = ext.lower()
    for cat, exts in CATEGORY_EXTS.items():
        if ext in exts:
            return cat
    return None

def get_valid_targets(source_ext: str) -> dict[str, ConversionRule]:
    """Returns a dict mapping target_ext -> ConversionRule for a given source extension."""
    source_ext = source_ext.lower()
    valid_targets = {}
    for rule in CONVERSION_RULES:
        if source_ext in rule.source_exts:
            for target_ext in rule.target_exts:
                if target_ext != source_ext:
                    valid_targets[target_ext] = rule
    return valid_targets

def get_valid_target_categories(source_ext: str) -> set[str]:
    valid_targets = get_valid_targets(source_ext)
    categories = set()
    for ext in valid_targets.keys():
        cat = get_category_for_ext(ext)
        if cat:
            categories.add(cat)
    return categories
