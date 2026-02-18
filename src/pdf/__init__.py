"""
PDF Converter Package

Modules:
    - any_to_pdf: Convert various file formats to PDF
    - splitter: Split PDF files into multiple files
    - merger: Merge multiple PDF files into one
"""

from .any_to_pdf import (
    any_to_pdf,
    any_to_pdf_async,
    UnsupportedFormat,
    ConversionProgress,
    excel_to_pdf_large_file,
    excel_to_pdf_alternative,
)
from .splitter import split_pdf, split_pdf_sequential, split_pdf_parallel
from .merger import merge_pdf, merge_pdf_sequential, merge_pdf_parallel

__all__ = [
    # Conversion functions
    "any_to_pdf",
    "any_to_pdf_async",
    "UnsupportedFormat",
    "ConversionProgress",
    # Splitter functions
    "split_pdf",
    "split_pdf_sequential",
    "split_pdf_parallel",
    # Merger functions
    "merge_pdf",
    "merge_pdf_sequential",
    "merge_pdf_parallel",
    # Excel helpers
    "excel_to_pdf_large_file",
    "excel_to_pdf_alternative",
]
