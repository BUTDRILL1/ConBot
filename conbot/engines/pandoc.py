import subprocess
from pathlib import Path
from . import register_engine, ConversionResult
from ..process_control import run_interruptible_subprocess
from ..bootstrap import get_pandoc_path
from .libreoffice import convert_libreoffice
import tempfile
import os
import re
import base64
import zlib

def encode_kroki(text: str) -> str:
    compressed = zlib.compress(text.encode('utf-8'), 9)
    return base64.urlsafe_b64encode(compressed).decode('ascii')

def preprocess_mermaid(markdown_text: str) -> str:
    pattern = re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL)
    def replacer(match):
        mermaid_code = match.group(1).strip()
        url = f"https://kroki.io/mermaid/png/{encode_kroki(mermaid_code)}"
        return f"![Mermaid Diagram]({url})"
    return pattern.sub(replacer, markdown_text)

@register_engine("pandoc")
def convert_pandoc(source_path: Path, target_path: Path, rule_warning: str | None) -> ConversionResult:
    # Get the absolute path from bootstrap
    bin_path = get_pandoc_path()
    if not bin_path:
        return ConversionResult(success=False, error_message="Pandoc executable not found.")

    input_path = source_path
    temp_md_path = None
    
    if source_path.suffix.lower() == ".md":
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '```mermaid' in content:
                processed_content = preprocess_mermaid(content)
                fd, temp_md_str = tempfile.mkstemp(suffix=".md")
                os.close(fd)
                temp_md_path = Path(temp_md_str)
                with open(temp_md_path, 'w', encoding='utf-8') as f:
                    f.write(processed_content)
                input_path = temp_md_path
        except Exception:
            pass

    # Automatic Chaining: if the user asks for a PDF, Pandoc cannot do it natively
    # without LaTeX. Instead, we invisibly convert to .docx, and use LibreOffice to print the PDF.
    is_pdf_chain = (target_path.suffix.lower() == ".pdf")
    
    if is_pdf_chain:
        fd, temp_docx_path = tempfile.mkstemp(suffix=".docx")
        os.close(fd)
        actual_target = Path(temp_docx_path)
    else:
        actual_target = target_path

    args = [
        bin_path,
        str(input_path),
        "-o",
        str(actual_target)
    ]
    
    # Simple subprocess.run for now, as pandoc is generally fast and 
    # capturing stderr is easier this way.
    try:
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode == 0:
            if is_pdf_chain:
                # Chain into LibreOffice
                chain_result = convert_libreoffice(actual_target, target_path, rule_warning)
                # Cleanup temporary docx
                try:
                    actual_target.unlink()
                except OSError:
                    pass
                return chain_result
            else:
                return ConversionResult(success=True, output_path=target_path)
        else:
            if is_pdf_chain and actual_target.exists():
                try: actual_target.unlink()
                except OSError: pass
            return ConversionResult(success=False, error_message=result.stderr.strip())
    except KeyboardInterrupt:
        if target_path.exists():
            try: target_path.unlink()
            except OSError: pass
        return ConversionResult(success=False, error_message="Conversion stopped by user.")
    except Exception as e:
        return ConversionResult(success=False, error_message=str(e))
    finally:
        if temp_md_path and temp_md_path.exists():
            try: temp_md_path.unlink()
            except OSError: pass
