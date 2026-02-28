"""
Rowline Converter Package

Modules:
    - xlsx2xml: Convert XLSX files to XML format
    - pdf: PDF conversion, splitting, and merging
    - gif: Convert video files to GIF
    - api: FastAPI web server
    - cli: Command-line interface
"""

from .xlsx2xml import XlsxToXmlConverter, XlsxReader, XmlWriter, XmlFiller
from .pdf import (
    # Conversion
    any_to_pdf,
    any_to_pdf_async,
    UnsupportedFormat,
    ConversionProgress,
    # Splitter
    split_pdf,
    split_pdf_sequential,
    split_pdf_parallel,
    # Merger
    merge_pdf,
    merge_pdf_sequential,
    merge_pdf_parallel,
    # PDF to Excel
    convert_pdf_to_excel,
    detect_table_flavor,
    get_pdf_table_info,
)

__version__ = "1.0.0"
__all__ = [
    # XLSX to XML
    "XlsxToXmlConverter",
    "XlsxReader",
    "XmlWriter",
    "XmlFiller",
    # PDF Conversion
    "any_to_pdf",
    "any_to_pdf_async",
    "UnsupportedFormat",
    "ConversionProgress",
    # PDF Splitter
    "split_pdf",
    "split_pdf_sequential",
    "split_pdf_parallel",
    # PDF Merger
    "merge_pdf",
    "merge_pdf_sequential",
    "merge_pdf_parallel",
    # PDF to Excel
    "convert_pdf_to_excel",
    "detect_table_flavor",
    "get_pdf_table_info",
]
