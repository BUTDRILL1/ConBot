import json
import platform
import shutil
import os
import glob
from pathlib import Path

def get_binary_path(binary_name: str, windows_fallbacks: list[str] | None = None) -> str | None:
    # First, check the system PATH (this automatically solves Linux and macOS)
    system_path = shutil.which(binary_name)
    if system_path:
        return system_path
        
    if platform.system() == "Windows" and windows_fallbacks:
        for fallback in windows_fallbacks:
            expanded = os.path.expandvars(fallback)
            for match in glob.glob(expanded):
                if Path(match).is_file():
                    return match
    return None

def get_pandoc_path() -> str | None:
    return get_binary_path("pandoc", [
        r"%LOCALAPPDATA%\Pandoc\pandoc.exe",
        r"%ProgramFiles%\Pandoc\pandoc.exe",
        r"C:\Program Files\Pandoc\pandoc.exe"
    ])

def get_ffmpeg_path() -> str | None:
    return get_binary_path("ffmpeg", [
        r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\*\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe"
    ])

def get_ffprobe_path() -> str | None:
    return get_binary_path("ffprobe", [
        r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_*\*\bin\ffprobe.exe",
        r"C:\ffmpeg\bin\ffprobe.exe"
    ])

def get_libreoffice_path() -> str | None:
    path = get_binary_path("soffice", [
        r"%ProgramFiles%\LibreOffice\program\soffice.exe",
        r"C:\Program Files\LibreOffice\program\soffice.exe"
    ])
    if path: return path
    return get_binary_path("libreoffice")

def get_cache_dir() -> Path:
    system = platform.system()
    if system == "Windows":
        base = Path.home() / "AppData" / "Roaming"
    else:
        base = Path.home()
    
    cache_dir = base / ".conbot"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def detect_package_manager() -> str | None:
    system = platform.system()
    candidates = {
        "Linux": ["pacman", "apt", "dnf", "zypper"],
        "Darwin": ["brew"],
        "Windows": ["winget", "choco"],
    }
    for mgr in candidates.get(system, []):
        if shutil.which(mgr):
            return mgr
    return None

def get_install_command(missing_deps: list[str]) -> str | None:
    if not missing_deps:
        return None
    
    mgr = detect_package_manager()
    if not mgr:
        return None
    
    if mgr == "pacman":
        return f"sudo pacman -S {' '.join(missing_deps)}"
    elif mgr == "apt":
        return f"sudo apt install {' '.join(missing_deps)}"
    elif mgr == "dnf":
        return f"sudo dnf install {' '.join(missing_deps)}"
    elif mgr == "brew":
        return f"brew install {' '.join(missing_deps)}"
    elif mgr == "winget":
        # winget requires specific IDs, we'll map them
        cmds = []
        for dep in missing_deps:
            if dep == "pandoc": cmds.append("winget install --id JohnMacFarlane.Pandoc -e")
            elif dep == "ffmpeg": cmds.append("winget install --id Gyan.FFmpeg -e")
            elif dep == "libreoffice": cmds.append("winget install --id TheDocumentFoundation.LibreOffice -e")
        return "\n".join(cmds)
    elif mgr == "choco":
        return f"choco install {' '.join(missing_deps)} -y"
    
    return None

def check_dependencies(force_recheck: bool = False) -> dict[str, bool]:
    cache_file = get_cache_dir() / "deps_cache.json"
    
    if not force_recheck and cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
            
    # Check binaries
    deps = {
        "pandoc": get_pandoc_path() is not None,
        "ffmpeg": get_ffmpeg_path() is not None,
        "libreoffice": get_libreoffice_path() is not None
    }
    
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(deps, f)
        
    return deps

def get_manual_install_links(missing_deps: list[str]) -> str:
    links = []
    if "pandoc" in missing_deps:
        links.append("pandoc:  https://pandoc.org/installing.html")
    if "ffmpeg" in missing_deps:
        links.append("ffmpeg:  https://ffmpeg.org/download.html")
    if "libreoffice" in missing_deps:
        links.append("libreoffice:  https://www.libreoffice.org/download/download-libreoffice/")
    return "\n  ".join(links)
