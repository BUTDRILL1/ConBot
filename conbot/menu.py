import sys
from pathlib import Path
import questionary
from .scanner import scan_directory, get_files_by_extension, get_compound_extension
from .format_graph import get_valid_target_categories, get_valid_targets, CATEGORY_EXTS, get_category_for_ext
from .ui import print_warning

class MenuState:
    def __init__(self):
        self.source_category: str | None = None
        self.source_ext: str | None = None
        self.source_file: Path | None = None
        self.target_category: str | None = None
        self.target_ext: str | None = None

def select_with_esc(message: str, choices: list[str | questionary.Choice]) -> str | None:
    try:
        # questionary's select returns None if aborted with Ctrl+C
        # We can bind Esc to cancel, but questionary doesn't easily map Esc to cancel in all prompts without custom keybindings.
        # Actually, questionary standard behavior: Ctrl+C aborts. 
        # For Esc, we can just let users know if it's not supported natively, or we add a "Go back" choice.
        # FSD says "Esc to go back". We can use custom keybindings in questionary.
        return questionary.select(message, choices=choices).unsafe_ask()
    except KeyboardInterrupt:
        sys.exit(0)

def run_menu(available_engines: dict[str, bool], initial_state: MenuState | None = None, start_step: int = 0) -> MenuState | None:
    state = initial_state or MenuState()
    files = scan_directory()
    grouped_files = get_files_by_extension(files)
    
    # We will use a state machine approach
    current_step = start_step
    steps = [
        "source_category",
        "source_ext",
        "source_file",
        "target_category",
        "target_ext"
    ]
    
    while current_step < len(steps):
        step_name = steps[current_step]
        
        if step_name == "source_category":
            choices = []
            for cat in CATEGORY_EXTS.keys():
                # Check if engines for this category are available
                # Docs: pandoc + libreoffice. If missing, show as unavailable.
                is_available = True
                reason = ""
                if cat == "Document" and not available_engines.get("pandoc"):
                    is_available = False
                    reason = " (unavailable — pandoc not installed)"
                elif cat == "Video" and not available_engines.get("ffmpeg"):
                    is_available = False
                    reason = " (unavailable — ffmpeg not installed)"
                elif cat == "Audio" and not available_engines.get("ffmpeg"):
                    is_available = False
                    reason = " (unavailable — ffmpeg not installed)"
                
                title = f"{cat}{reason}"
                choices.append(questionary.Choice(title=title, value=cat, disabled=not is_available))
                
            ans = select_with_esc("Convert `A` to `B`\n\nA:", choices)
            if not ans:
                # Root menu Esc/Ctrl+C is no-op or quit
                return None
            state.source_category = ans
            current_step += 1
            
        elif step_name == "source_ext":
            exts_in_cat = CATEGORY_EXTS[state.source_category]
            available_exts = [ext for ext in exts_in_cat if ext in grouped_files]
            
            if not available_exts:
                # No files found
                ans = select_with_esc(f"A → {state.source_category}:\n(no files found in this directory)", ["Go back"])
                current_step -= 1
                continue
            
            choices = available_exts + [questionary.Choice(title="Esc → go back", value="BACK")]
            ans = select_with_esc(f"A → {state.source_category}:", choices)
            if ans == "BACK" or not ans:
                current_step -= 1
                continue
                
            state.source_ext = ans
            current_step += 1
            
        elif step_name == "source_file":
            available_files = grouped_files[state.source_ext]
            choices = [f.name for f in available_files] + [questionary.Choice(title="Esc → go back", value="BACK")]
            ans = select_with_esc(f"A → {state.source_category} → {state.source_ext}:", choices)
            if ans == "BACK" or not ans:
                current_step -= 1
                continue
                
            state.source_file = next(f for f in available_files if f.name == ans)
            current_step += 1
            
        elif step_name == "target_category":
            valid_cats = get_valid_target_categories(state.source_ext)
            choices = list(valid_cats) + [questionary.Choice(title="Esc → go back", value="BACK")]
            ans = select_with_esc(f"Convert `{state.source_file.name}` to `B`\n\nB:", choices)
            if ans == "BACK" or not ans:
                current_step -= 1
                continue
                
            state.target_category = ans
            current_step += 1
            
        elif step_name == "target_ext":
            valid_targets = get_valid_targets(state.source_ext)
            target_exts_in_cat = [ext for ext, rule in valid_targets.items() if get_category_for_ext(ext) == state.target_category]
            
            choices = target_exts_in_cat + [questionary.Choice(title="Esc → go back", value="BACK")]
            ans = select_with_esc(f"B → {state.target_category}:", choices)
            if ans == "BACK" or not ans:
                current_step -= 1
                continue
                
            state.target_ext = ans
            current_step += 1
            
    return state
