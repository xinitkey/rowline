from pathlib import Path
from typing import Optional

from .xlsx_reader import XlsxReader, SheetData
from .xml_writer import XmlWriter


class XlsxToXmlConverter:
    def __init__(
        self,
        encoding: str = "utf-8",
        pretty_print: bool = True,
        budget_year: str = "",
        period: str = "",
        organization_id: str = "",
        report_date: str = "",
    ):
        self.xml_writer = XmlWriter(
            encoding=encoding, pretty_print=pretty_print,
            budget_year=budget_year, period=period,
            organization_id=organization_id, report_date=report_date,
        )

    def convert(
        self,
        input_path: str | Path,
        output_path: Optional[str | Path] = None,
        sheet_name: Optional[str] = None,
        header_row: int = 8,
        start_row: int = 9,
        report_code: Optional[str] = None,
    ) -> Path:
        input_path = Path(input_path)
        output_path = Path(output_path) if output_path else input_path.with_suffix(".xml")

        with XlsxReader(input_path) as reader:
            sheet = reader.read_sheet(sheet_name, header_row, start_row, num_columns=9)
            return self.xml_writer.write(sheet, output_path, report_code)

    def convert_all_sheets(
        self,
        input_path: str | Path,
        output_path: Optional[str | Path] = None,
        header_row: int = 8,
        start_row: int = 9,
        separate_files: bool = False,
    ) -> list[Path]:
        input_path = Path(input_path)
        with XlsxReader(input_path) as reader:
            sheets = list(reader.read_all_sheets(header_row, start_row, num_columns=9))

        if separate_files:
            return self._write_separate_files(input_path, sheets, output_path)

        out = Path(output_path) if output_path else input_path.with_suffix(".xml")
        return [self.xml_writer.write_multiple_sheets(sheets, out)]

    def _write_separate_files(self, input_path: Path, sheets: list[SheetData], output_dir: Optional[str | Path]) -> list[Path]:
        out_dir = Path(output_dir) if output_dir else input_path.parent / f"{input_path.stem}_xml"
        out_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for sheet in sheets:
            safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in sheet.name)
            results.append(self.xml_writer.write(sheet, out_dir / f"{safe}.xml"))
        return results

    def to_xml_string(self, input_path: str | Path, sheet_name: Optional[str] = None, header_row: int = 8, start_row: int = 9, report_code: Optional[str] = None) -> str:
        with XlsxReader(input_path) as reader:
            sheet = reader.read_sheet(sheet_name, header_row, start_row, num_columns=9)
            return self.xml_writer.to_string(sheet, report_code)
