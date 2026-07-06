from pathlib import Path
from PIL import Image
import pillow_heif
from . import register_engine, ConversionResult

# Register HEIF opener so Pillow can read .heic/.heif
pillow_heif.register_heif_opener()

@register_engine("image")
def convert_image(source_path: Path, target_path: Path, rule_warning: str | None) -> ConversionResult:
    try:
        with Image.open(source_path) as img:
            # If converting to JPEG or PDF, we need to convert RGBA to RGB
            if img.mode in ('RGBA', 'P') and target_path.suffix.lower() in ('.jpg', '.jpeg', '.pdf'):
                img = img.convert('RGB')
                
            img.save(target_path)
        return ConversionResult(success=True, output_path=target_path)
    except Exception as e:
        if target_path.exists():
            try:
                target_path.unlink()
            except OSError:
                pass
        return ConversionResult(success=False, error_message=str(e))
