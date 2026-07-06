import subprocess
import tempfile
import shutil
from pathlib import Path
from . import register_engine, ConversionResult
from ..process_control import run_interruptible_subprocess
from ..bootstrap import get_libreoffice_path

@register_engine("libreoffice")
def convert_libreoffice(source_path: Path, target_path: Path, rule_warning: str | None) -> ConversionResult:
    # Get the absolute path from bootstrap
    bin_path = get_libreoffice_path()
    if not bin_path:
        return ConversionResult(success=False, error_message="LibreOffice executable not found.")

    # LibreOffice headless has known flakiness with lock files if soffice is already open
    # We copy the source to a temp dir and convert there to avoid locking issues
    with tempfile.TemporaryDirectory() as temp_dir:
        tmp_dir_path = Path(temp_dir)
        tmp_source = tmp_dir_path / source_path.name
        shutil.copy2(source_path, tmp_source)
        
        # Determine the filter/extension. Usually --convert-to <ext> is enough.
        target_ext = target_path.suffix.lstrip(".")
        
        # e.g., soffice --headless --convert-to pdf outdir source
        args = [
            bin_path,
            "--headless",
            "--convert-to",
            target_ext,
            "--outdir",
            temp_dir,
            str(tmp_source)
        ]
        
        try:
            result = subprocess.run(args, capture_output=True, text=True)
            if result.returncode == 0:
                # Find the converted file in the tmp dir
                expected_tmp_out = tmp_dir_path / f"{tmp_source.stem}.{target_ext}"
                if expected_tmp_out.exists():
                    shutil.move(str(expected_tmp_out), str(target_path))
                    return ConversionResult(success=True, output_path=target_path)
                else:
                    return ConversionResult(success=False, error_message="LibreOffice succeeded but output file not found.")
            else:
                return ConversionResult(success=False, error_message=result.stderr.strip() or result.stdout.strip())
        except KeyboardInterrupt:
            if target_path.exists():
                try:
                    target_path.unlink()
                except OSError:
                    pass
            return ConversionResult(success=False, error_message="Conversion stopped by user.")
        except Exception as e:
            return ConversionResult(success=False, error_message=str(e))
