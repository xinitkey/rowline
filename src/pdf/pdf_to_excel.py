"""
PDF to Excel Converter using Camelot

"""

import camelot
from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd


def convert_pdf_to_excel(
    pdf_path: str,
    pages: str = "all",
    flavor: str = "lattice",
    output_path: Optional[str] = None
) -> Tuple[List[str], int]:

    """
   
    Args:
        pdf_path: Path to the input PDF file
        pages: Pages to process (e.g., "1", "1-3", "1,3,5", "all")
        flavor: Camelot flavor - "lattice" for tables with lines, "stream" for tables without lines
        output_path: Optional path for output Excel file (default: same name as PDF with .xlsx)
    
    Returns:
        Tuple of (list of output sheet names, total tables found)
    
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If no tables found in PDF
    """
    pdf_path_obj = Path(pdf_path)
    
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Set default output path
    if output_path is None:
        output_path = str(pdf_path_obj.with_suffix('.xlsx'))
    
    # Convert pages parameter for camelot
    if pages.lower() == "all":
        pages = "all"
    
    # Extract tables using camelot
    tables = camelot.read_pdf(
        str(pdf_path_obj),
        pages=pages,
        flavor=flavor,
    )
    
    if tables.n == 0:
        raise ValueError("No tables found in the PDF. Try using flavor='stream' instead of 'lattice'.")
    
    # Create Excel writer with multiple sheets
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        for i, table in enumerate(tables, 1):
            sheet_name = f"Table_{i}"
            table.df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    sheet_names = [f"Table_{i}" for i in range(1, tables.n + 1)]
    
    return sheet_names, tables.n


def detect_table_flavor(pdf_path: str, pages: str = "1") -> str:
    """
    Detect the best flavor for table extraction.
    
    Args:
        pdf_path: Path to the PDF file
        pages: Sample pages to test
    
    Returns:
        "lattice" or "stream" based on which finds more tables
    """
    try:
        lattice_tables = camelot.read_pdf(pdf_path, pages=pages, flavor="lattice")
    except Exception:
        lattice_tables = None
    
    try:
        stream_tables = camelot.read_pdf(pdf_path, pages=pages, flavor="stream")
    except Exception:
        stream_tables = None
    
    if lattice_tables is None and stream_tables is None:
        return "lattice"  # Default
    
    if lattice_tables is None:
        return "stream"
    
    if stream_tables is None:
        return "lattice"
    
    # Return the flavor that found more tables
    return "lattice" if lattice_tables.n >= stream_tables.n else "stream"


def get_pdf_table_info(pdf_path: str, pages: str = "all") -> dict:
    """
    Get information about tables in a PDF without full conversion.
    
    Args:
        pdf_path: Path to the PDF file
        pages: Pages to analyze
    
    Returns:
        Dictionary with table information
    """
    pdf_path_obj = Path(pdf_path)
    
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    # Try lattice first, then stream if no tables found
    try:
        tables = camelot.read_pdf(str(pdf_path_obj), pages=pages, flavor="lattice")
        flavor_used = "lattice"
    except Exception:
        tables = None
        flavor_used = "lattice"
    
    if tables is None or tables.n == 0:
        try:
            tables = camelot.read_pdf(str(pdf_path_obj), pages=pages, flavor="stream")
            flavor_used = "stream"
        except Exception as e:
            return {
                "error": str(e),
                "table_count": 0,
                "flavor": None
            }
    
    table_info = []
    for i, table in enumerate(tables, 1):
        table_info.append({
            "table_number": i,
            "page": table.page,
            "rows": len(table.df),
            "columns": len(table.df.columns),
            "accuracy": round(table.parsing_report.get('accuracy', 0), 2) if hasattr(table, 'parsing_report') else None
        })
    
    return {
        "table_count": tables.n,
        "flavor": flavor_used,
        "tables": table_info
    }
