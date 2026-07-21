#!/usr/bin/env python3
"""
CLI module for XLSX to XML Converter / Filler.
"""

import argparse
import sys
from pathlib import Path

from src import XlsxToXmlConverter, XmlFiller


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Fill XML template with XLSX data / Convert XLSX to XML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Template fill mode (default):
  %(prog)s data.xlsx -t template.xml -o output_dir   # Fill template with data

Convert mode:
  %(prog)s data.xlsx --convert -o output_dir         # Create XML from XLSX

Examples:
  %(prog)s data.xlsx -t RF-FD-048BL.xml -o results/
  %(prog)s data.xlsx -t template.xml -o result.xml --single -s "Sheet1"
        """
    )

    parser.add_argument("input", type=str, help="Path to input XLSX file")
    parser.add_argument("-t", "--template", type=str, default=None, 
                        help="Path to XML template (for fill mode)")
    parser.add_argument("-o", "--output", type=str, default=None, 
                        help="Path to output directory/file")
    parser.add_argument("-s", "--sheet", type=str, default=None, 
                        help="Sheet name (default: all sheets)")
    parser.add_argument("--single", action="store_true", 
                        help="Process only a single sheet")
    
    # Template fill mode parameters
    parser.add_argument("--code-col", type=int, default=6, 
                        help="Column with code (1-based, default: 6=F)")
    parser.add_argument("--data-start-col", type=int, default=7, 
                        help="Data start column (1-based, default: 7=G)")
    parser.add_argument("--data-end-col", type=int, default=12, 
                        help="Data end column (1-based, default: 12=L)")
    parser.add_argument("--start-row", type=int, default=9, 
                        help="First data row (default: 9)")
    
    # Convert mode
    parser.add_argument("--convert", action="store_true", 
                        help="Convert mode (create new XML)")
    parser.add_argument("--budget-year", type=str, default="", help="Budget year")
    parser.add_argument("--period", type=str, default="", help="Report period")
    parser.add_argument("--org-id", type=str, default="", help="Organization ID")
    parser.add_argument("--date", type=str, default="", help="Report date")
    
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    return parser.parse_args()


def run_fill_mode(args) -> int:
    """Template fill mode."""
    input_path = Path(args.input)
    
    if not args.template:
        print("Error: Specify XML template path with -t/--template", file=sys.stderr)
        return 1
    
    template_path = Path(args.template)
    if not template_path.exists():
        print(f"Error: Template not found: {template_path}", file=sys.stderr)
        return 1

    filler = XmlFiller(template_path)
    
    try:
        if args.single or args.sheet:
            # Single sheet
            output_path = args.output
            if not output_path:
                output_path = input_path.with_suffix(".xml")
            
            result_path = filler.fill_from_xlsx(
                xlsx_path=input_path,
                output_path=output_path,
                sheet_name=args.sheet,
                code_column=args.code_col,
                data_start_column=args.data_start_col,
                data_end_column=args.data_end_col,
                start_row=args.start_row
            )
            print(f"Created: {result_path}")
        else:
            # All sheets
            output_dir = args.output
            if not output_dir:
                output_dir = input_path.parent / f"{input_path.stem}_xml"
            
            result_paths = filler.fill_all_sheets(
                xlsx_path=input_path,
                output_dir=output_dir,
                code_column=args.code_col,
                data_start_column=args.data_start_col,
                data_end_column=args.data_end_col,
                start_row=args.start_row
            )
            print(f"Sheets processed: {len(result_paths)}")
            if args.verbose:
                for path in result_paths:
                    print(f"  \u2192 {path}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_convert_mode(args) -> int:
    """XLSX to XML convert mode."""
    input_path = Path(args.input)
    
    converter = XlsxToXmlConverter(
        budget_year=args.budget_year,
        period=args.period,
        organization_id=args.org_id,
        report_date=args.date
    )

    try:
        if args.single or args.sheet:
            output_path = args.output
            if output_path and not output_path.endswith('.xml'):
                output_path = Path(output_path) / f"{input_path.stem}.xml"
            
            result_path = converter.convert(
                input_path=input_path,
                output_path=output_path,
                sheet_name=args.sheet,
                start_row=args.start_row
            )
            print(f"Created: {result_path}")
        else:
            result_paths = converter.convert_all_sheets(
                input_path=input_path,
                output_path=args.output,
                start_row=args.start_row,
                separate_files=True
            )
            print(f"Sheets converted: {len(result_paths)}")
            if args.verbose:
                for path in result_paths:
                    print(f"  \u2192 {path}")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cli_main() -> int:
    """Main CLI entry point."""
    args = parse_arguments()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    if not input_path.suffix.lower() == ".xlsx":
        print(f"Error: Expected .xlsx file, got: {input_path.suffix}", file=sys.stderr)
        return 1

    if args.convert:
        return run_convert_mode(args)
    else:
        return run_fill_mode(args)
