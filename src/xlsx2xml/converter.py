"""
Основной модуль конвертера XLSX в XML.
"""

from pathlib import Path
from typing import Optional

from .xlsx_reader import XlsxReader, SheetData
from .xml_writer import XmlWriter


class XlsxToXmlConverter:
    """Главный класс конвертера XLSX в XML формат Report."""

    def __init__(
        self,
        encoding: str = "utf-8",
        pretty_print: bool = True,
        budget_year: str = "",
        period: str = "",
        organization_id: str = "",
        report_date: str = ""
    ):
        """
        Инициализация конвертера.

        Args:
            encoding: Кодировка выходного XML файла.
            pretty_print: Форматировать XML с отступами.
            budget_year: Бюджетный год для отчёта.
            period: Период отчёта.
            organization_id: ID организации.
            report_date: Дата отчёта.
        """
        self.xml_writer = XmlWriter(
            encoding=encoding,
            pretty_print=pretty_print,
            budget_year=budget_year,
            period=period,
            organization_id=organization_id,
            report_date=report_date
        )

    def convert(
        self,
        input_path: str | Path,
        output_path: Optional[str | Path] = None,
        sheet_name: Optional[str] = None,
        header_row: int = 8,
        start_row: int = 9,
        report_code: Optional[str] = None
    ) -> Path:
        """
        Конвертирует XLSX файл в XML формат Report.

        Args:
            input_path: Путь к входному XLSX файлу.
            output_path: Путь к выходному XML файлу.
            sheet_name: Имя листа для конвертации.
            header_row: Номер строки с заголовками (по умолчанию 8).
            start_row: Номер строки начала данных (по умолчанию 9).
            report_code: Код отчёта.

        Returns:
            Путь к созданному XML файлу.
        """
        input_path = Path(input_path)

        if output_path is None:
            output_path = input_path.with_suffix(".xml")
        else:
            output_path = Path(output_path)

        with XlsxReader(input_path) as reader:
            sheet_data = reader.read_sheet(
                sheet_name=sheet_name,
                header_row=header_row,
                start_row=start_row,
                num_columns=9
            )
            return self.xml_writer.write(sheet_data, output_path, report_code)

    def convert_all_sheets(
        self,
        input_path: str | Path,
        output_path: Optional[str | Path] = None,
        header_row: int = 8,
        start_row: int = 9,
        separate_files: bool = False
    ) -> list[Path]:
        """
        Конвертирует все листы XLSX файла в XML.
        """
        input_path = Path(input_path)

        with XlsxReader(input_path) as reader:
            sheets = list(reader.read_all_sheets(header_row, start_row, num_columns=9))

            if separate_files:
                return self._write_separate_files(input_path, sheets, output_path)
            else:
                if output_path is None:
                    output_path = input_path.with_suffix(".xml")
                result_path = self.xml_writer.write_multiple_sheets(sheets, output_path)
                return [result_path]

    def _write_separate_files(
        self,
        input_path: Path,
        sheets: list[SheetData],
        output_dir: Optional[str | Path]
    ) -> list[Path]:
        """Записывает каждый лист в отдельный файл."""
        if output_dir is None:
            output_dir = input_path.parent / f"{input_path.stem}_xml"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        result_paths = []
        for sheet in sheets:
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in sheet.name)
            output_path = output_dir / f"{safe_name}.xml"
            self.xml_writer.write(sheet, output_path)
            result_paths.append(output_path)

        return result_paths

    def to_xml_string(
        self,
        input_path: str | Path,
        sheet_name: Optional[str] = None,
        header_row: int = 8,
        start_row: int = 9,
        report_code: Optional[str] = None
    ) -> str:
        """Конвертирует XLSX в XML строку."""
        with XlsxReader(input_path) as reader:
            sheet_data = reader.read_sheet(
                sheet_name=sheet_name,
                header_row=header_row,
                start_row=start_row,
                num_columns=9
            )
            return self.xml_writer.to_string(sheet_data, report_code)
