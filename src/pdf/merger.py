"""
PDF Merger Module.

Provides functionality to merge multiple PDF files into one.
"""

import os
import concurrent.futures
from pypdf import PdfReader, PdfWriter


def merge_pdf(input_paths: list[str], output_path: str) -> str:
    """
    Merge multiple PDF files into one with optimized parallel processing.

    Args:
        input_paths: List of PDF file paths to merge
        output_path: Path for merged output file

    Returns:
        Output file path
    """
    if len(input_paths) <= 3:
        # For small number of files, use simple sequential merge
        return merge_pdf_sequential(input_paths, output_path)
    else:
        # For larger number of files, use parallel processing
        return merge_pdf_parallel(input_paths, output_path)


def merge_pdf_sequential(input_paths: list[str], output_path: str) -> str:
    """Sequential PDF merging for small number of files."""
    writer = PdfWriter()

    for pdf_path in input_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path


def merge_pdf_parallel(input_paths: list[str], output_path: str) -> str:
    """
    Parallel PDF merging for better performance with many files.
    Uses thread pool to read multiple PDF files concurrently.
    """
    writer = PdfWriter()

    def read_pdf_pages(pdf_path: str) -> list:
        """Read all pages from a PDF file."""
        reader = PdfReader(pdf_path)
        return list(reader.pages)

    # Read all PDF files in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(input_paths), 8)) as executor:
        # Submit all read tasks
        future_to_path = {executor.submit(read_pdf_pages, path): path for path in input_paths}

        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_path):
            try:
                pages = future.result()
                # Add all pages from this PDF to the writer
                for page in pages:
                    writer.add_page(page)
            except Exception as e:
                print(f"[MERGE] Error reading PDF {future_to_path[future]}: {e}")
                raise

    # Write the merged PDF
    with open(output_path, "wb") as f:
        writer.write(f)

    return output_path
