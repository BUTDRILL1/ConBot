import os
import signal
import subprocess
import time
from pathlib import Path
from .ui import prompt_warning, print_error, print_warning

def run_interruptible_subprocess(args: list[str], output_path: Path, cwd: Path | None = None) -> int:
    """
    Runs a subprocess. If Ctrl+C is pressed, prompts the user:
    Stop (kill process, delete output), Background (detach), Cancel (keep waiting).
    """
    # Use process group so we can manage it easily
    creationflags = 0
    preexec_fn = None
    if os.name == 'nt':
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        preexec_fn = os.setpgrp

    # Start the process
    process = subprocess.Popen(
        args,
        cwd=cwd,
        creationflags=creationflags,
        preexec_fn=preexec_fn
    )

    while True:
        try:
            # Wait for the process to finish
            retcode = process.wait(timeout=0.5)
            return retcode
        except subprocess.TimeoutExpired:
            continue
        except KeyboardInterrupt:
            # User pressed Ctrl+C
            choice = prompt_warning(
                f"Conversion in progress: {args[0]}",
                choices=[
                    "Stop conversion (kills process, deletes partial output)",
                    "Let it finish in background, exit ConBot now",
                    "Cancel, keep waiting"
                ]
            )
            
            if choice == "Stop conversion (kills process, deletes partial output)":
                _kill_process_group(process)
                if output_path.exists():
                    try:
                        output_path.unlink()
                    except OSError:
                        pass
                print_error("Conversion stopped.")
                return -1
                
            elif choice == "Let it finish in background, exit ConBot now":
                print_warning(
                    "ConBot will exit now. The conversion will continue running,\n"
                    "but you won't see its progress or be notified when it finishes.\n"
                    "Check ./conbot_output/ later for the result."
                )
                # Just return a special code and leave the process running
                return 999
                
            else:
                # Cancel or another KeyboardInterrupt
                continue

def _kill_process_group(process: subprocess.Popen):
    """Kills the process group to ensure children die too."""
    try:
        if os.name == 'nt':
            # Sends CTRL_BREAK_EVENT to the process group
            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
            time.sleep(0.5)
            process.kill()
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            time.sleep(0.5)
            if process.poll() is None:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except OSError:
        pass
