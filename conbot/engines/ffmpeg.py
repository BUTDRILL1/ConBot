import subprocess
from pathlib import Path
from . import register_engine, ConversionResult
from ..bootstrap import get_ffmpeg_path

@register_engine("ffmpeg")
def convert_ffmpeg(source_path: Path, target_path: Path, rule_warning: str | None) -> ConversionResult:
    bin_path = get_ffmpeg_path()
    if not bin_path:
        return ConversionResult(success=False, error_message="FFmpeg executable not found.")

    # Base args for privacy (strip metadata) and overwrite
    base_args = [
        bin_path,
        "-y",               # Overwrite if exists (output_handler already handles collisions)
        "-i", str(source_path),
        "-map_metadata", "-1" # Privacy: drop embedded metadata
    ]
    
    # Fast Remux-First Logic: Try to copy streams without re-encoding to save time and quality.
    remux_args = base_args + ["-c", "copy", str(target_path)]
    
    try:
        # Suppress output to avoid spamming the console
        remux_result = subprocess.run(remux_args, capture_output=True, text=True)
        if remux_result.returncode == 0:
            return ConversionResult(success=True, output_path=target_path)
            
        # If remux fails (e.g., incompatible codec for the new container), fallback to full re-encode
        if target_path.exists():
            try: target_path.unlink()
            except OSError: pass
            
        encode_args = base_args + [str(target_path)]
        encode_result = subprocess.run(encode_args, capture_output=True, text=True)
        
        if encode_result.returncode == 0:
            return ConversionResult(success=True, output_path=target_path)
        else:
            return ConversionResult(success=False, error_message=encode_result.stderr.strip())
            
    except KeyboardInterrupt:
        if target_path.exists():
            try: target_path.unlink()
            except OSError: pass
        return ConversionResult(success=False, error_message="Conversion stopped by user.")
    except Exception as e:
        return ConversionResult(success=False, error_message=str(e))
