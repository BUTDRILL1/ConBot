import sys
import argparse
from .ui import print_banner, print_success, print_error, print_warning, spinner, prompt_warning
from .bootstrap import check_dependencies, get_install_command, get_manual_install_links
from .menu import run_menu
from .format_graph import get_valid_targets
from .output_handler import get_output_dir, handle_collision

# Import engines to register them
from .engines import ENGINES
from .engines import pandoc, libreoffice, image, spreadsheets, ffmpeg
import questionary

def main():
    parser = argparse.ArgumentParser(description="ConBot - Convert anything to anything, fast.")
    parser.add_argument("--recheck", action="store_true", help="Force recheck of system dependencies")
    args = parser.parse_args()

    # 1. Dependency check
    available_engines = check_dependencies(force_recheck=args.recheck)
    
    missing_deps = [dep for dep, available in available_engines.items() if not available]
    if missing_deps:
        print_warning(f"Missing dependencies: {', '.join(missing_deps)}")
        install_cmd = get_install_command(missing_deps)
        if install_cmd:
            print(f"\nRun this yourself, then restart ConBot:\n  {install_cmd}\n")
            prompt_warning("", choices=["> OK, got it"])
        else:
            links = get_manual_install_links(missing_deps)
            print(f"\nInstall manually from:\n  {links}\n")
            prompt_warning("", choices=["> OK, continue with limited features"])

    # 2. Print Banner
    print_banner()

    # 3. Run Menu Loop
    current_state = None
    start_step = 0
    
    while True:
        state = run_menu(available_engines, initial_state=current_state, start_step=start_step)
        if not state or not state.source_file or not state.target_ext:
            break

        source_path = state.source_file
        target_ext = state.target_ext
        
        # 4. Engine Resolution & Warning
        rule = get_valid_targets(state.source_ext)[target_ext]
        if rule.warning:
            ans = prompt_warning(rule.warning, choices=["Continue anyway", "Go back"])
            if ans != "Continue anyway":
                # User aborted warning, just restart at the same state
                current_state = state
                start_step = 4 # target_ext selection
                continue

        # 5. Output Collision Handling
        out_dir = get_output_dir()
        target_path = out_dir / f"{source_path.stem}{target_ext}"
        
        resolved_target = handle_collision(target_path)
        if not resolved_target:
            # Cancelled collision
            current_state = state
            start_step = 4
            continue
            
        engine_func = ENGINES.get(rule.engine)
        if not engine_func:
            print_error(f"Engine '{rule.engine}' is not implemented yet.")
            break
            
        # 6. Conversion
        with spinner(f"Converting `{source_path.name}` → `{resolved_target.name}`..."):
            result = engine_func(source_path, resolved_target, rule.warning)
            
        if result.was_backgrounded:
            sys.exit(0)
        elif result.success:
            final_path = result.output_path or resolved_target
            print_success(f"Done! Saved to {final_path}")
            
            # Post-conversion Exit Menu
            try:
                ans = questionary.select(
                    "What would you like to do next?",
                    choices=["Generate with diff. format", "Start Over", "Exit"]
                ).unsafe_ask()
                
                if ans == "Generate with diff. format":
                    current_state = state
                    start_step = 3 # target_category selection
                    continue
                elif ans == "Start Over":
                    current_state = None
                    start_step = 0
                    continue
                else:
                    break
            except KeyboardInterrupt:
                break
        else:
            print_error(f"Conversion failed: {result.error_message}")
            break

if __name__ == "__main__":
    main()
