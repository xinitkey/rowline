"""
PDF Splitter Module.

Provides functionality to split PDF files into multiple files.
"""

import os
import concurrent.futures
from typing import Optional
from pypdf import PdfReader


def split_pdf(
    input_path: str,
    output_dir: str,
    pages: Optional[list[int]] = None
) -> list[str]:
    """
    Split PDF into multiple files with optimized parallel processing.

    Args:
        input_path: Path to input PDF
        output_dir: Directory to save split files
        pages: List of page numbers to extract (1-based), if None - split all pages individually

    Returns:
        List of output file paths
    """
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    if pages is None:
        # Split each page into separate file - use parallel processing for large PDFs
        if total_pages <= 10:
            return split_pdf_sequential(reader, output_dir, total_pages)
        else:
            return split_pdf_parallel(reader, output_dir, total_pages)
    else:
        # Extract specific pages into one file
        from pypdf import PdfWriter
        
        writer = PdfWriter()
        for page_num in pages:
            if 1 <= page_num <= total_pages:
                writer.add_page(reader.pages[page_num - 1])

        output_path = os.path.join(output_dir, "extracted_pages.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        return [output_path]


def split_pdf_sequential(
    reader: PdfReader,
    output_dir: str,
    total_pages: int
) -> list[str]:
    """Sequential PDF splitting for small number of pages."""
    output_files = []
    for i in range(total_pages):
        from pypdf import PdfWriter
        
        writer = PdfWriter()
        writer.add_page(reader.pages[i])

        output_path = os.path.join(output_dir, f"page_{i+1:03d}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        output_files.append(output_path)
    return output_files


def split_pdf_parallel(
    reader: PdfReader,
    output_dir: str,
    total_pages: int
) -> list[str]:
    """
    Parallel PDF splitting for better performance with many pages.
    Uses thread pool to write multiple PDF files concurrently.
    """
    def write_single_page(page_idx: int) -> str:
        """Write a single page to PDF file."""
        from pypdf import PdfWriter
        
        writer = PdfWriter()
        writer.add_page(reader.pages[page_idx])

        output_path = os.path.join(output_dir, f"page_{page_idx+1:03d}.pdf")
        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path

    # Write all pages in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(total_pages, 8)) as executor:
        # Submit all write tasks
        futures = [executor.submit(write_single_page, i) for i in range(total_pages)]

        # Collect results
        output_files = []
        for future in concurrent.futures.as_completed(futures):
            try:
                output_files.append(future.result())
            except Exception as e:
                print(f"[SPLIT] Error writing page: {e}")
                raise

    return sorted(output_files)  # Return in page order
