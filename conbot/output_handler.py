from pathlib import Path
from .ui import prompt_warning

def get_output_dir() -> Path:
    out_dir = Path("conbot_output")
    out_dir.mkdir(exist_ok=True)
    return out_dir

def handle_collision(target_path: Path) -> Path | None:
    """
    Checks if target_path exists.
    If it does, prompts the user: Overwrite, Save as new name, Cancel.
    Returns the resolved Path, or None if cancelled.
    """
    if not target_path.exists():
        return target_path
    
    choice = prompt_warning(
        f"{target_path} already exists.",
        choices=["Overwrite", "Save as new name", "Cancel"]
    )
    
    if choice == "Overwrite":
        return target_path
    elif choice == "Save as new name":
        stem = target_path.stem
        ext = target_path.suffix
        counter = 1
        while True:
            new_path = target_path.with_name(f"{stem}({counter}){ext}")
            if not new_path.exists():
                return new_path
            counter += 1
    else:
        # Cancel or KeyboardInterrupt
        return None
