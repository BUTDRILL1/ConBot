import pandas as pd
from pathlib import Path
from . import register_engine, ConversionResult
from .libreoffice import convert_libreoffice
import warnings

@register_engine("spreadsheets")
def convert_spreadsheets(source_path: Path, target_path: Path, rule_warning: str | None) -> ConversionResult:
    # If the target is a PDF, we must use LibreOffice because pandas cannot render PDFs.
    if target_path.suffix.lower() == ".pdf":
        return convert_libreoffice(source_path, target_path, rule_warning)
    
    try:
        # 1. Read and Write
        src_ext = source_path.suffix.lower()
        tgt_ext = target_path.suffix.lower()
        
        if src_ext == ".csv":
            df = pd.read_csv(source_path)
            if tgt_ext == ".csv":
                df.to_csv(target_path, index=False)
            elif tgt_ext == ".xlsx":
                df.to_excel(target_path, index=False, engine="openpyxl")
            else:
                return ConversionResult(success=False, error_message=f"Unsupported spreadsheet target format: {tgt_ext}")
            return ConversionResult(success=True, output_path=target_path)
            
        elif src_ext in [".xlsx", ".xls"]:
            # Suppress default styling warnings from openpyxl
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                # Read all sheets into a dictionary: {sheet_name: DataFrame}
                dfs = pd.read_excel(source_path, sheet_name=None)
                
            if tgt_ext == ".csv":
                if len(dfs) == 1:
                    # Single sheet, standard export
                    sheet_name, df = list(dfs.items())[0]
                    df.to_csv(target_path, index=False)
                    return ConversionResult(success=True, output_path=target_path)
                else:
                    # Multi-sheet fan-out
                    for sheet_name, df in dfs.items():
                        # Sanitize sheet name for valid filename
                        safe_sheet_name = "".join(c for c in str(sheet_name) if c.isalnum() or c in (' ', '-', '_')).strip()
                        fan_out_path = target_path.parent / f"{target_path.stem}_{safe_sheet_name}.csv"
                        df.to_csv(fan_out_path, index=False)
                    # Return the parent folder path since multiple files were generated
                    return ConversionResult(success=True, output_path=target_path.parent)
                    
            elif tgt_ext == ".xlsx":
                with pd.ExcelWriter(target_path, engine="openpyxl") as writer:
                    for sheet_name, df in dfs.items():
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                return ConversionResult(success=True, output_path=target_path)
            else:
                return ConversionResult(success=False, error_message=f"Unsupported spreadsheet target format: {tgt_ext}")
        else:
            return ConversionResult(success=False, error_message=f"Unsupported spreadsheet source format: {src_ext}")
        
    except Exception as e:
        return ConversionResult(success=False, error_message=f"Spreadsheet conversion failed: {str(e)}")
