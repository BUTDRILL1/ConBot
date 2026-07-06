from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass

@dataclass
class ConversionResult:
    success: bool
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    was_backgrounded: bool = False

# Type for an engine function
EngineFunc = Callable[[Path, Path, str], ConversionResult]

# Registry
ENGINES: dict[str, EngineFunc] = {}

def register_engine(name: str):
    def decorator(func: EngineFunc):
        ENGINES[name] = func
        return func
    return decorator

# Import engine modules to run their @register_engine decorators
# This must happen after register_engine is defined
from . import pandoc
from . import libreoffice
from . import image
from . import spreadsheets
from . import ffmpeg
