"""
Модуль для записи XML файлов в формате Report.
"""

from pathlib import Path
from typing import Optional, Any
from datetime import datetime, date
import re

from lxml import etree

from .xlsx_reader import SheetData


class XmlWriter:
    """Класс для записи данных в XML формат Report."""

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
        Инициализация писателя XML.

        Args:
            encoding: Кодировка XML файла.
            pretty_print: Форматировать вывод с отступами.
            budget_year: Бюджетный год.
            period: Период отчёта.
            organization_id: ID организации.
            report_date: Дата отчёта.
        """
        self.encoding = encoding
        self.pretty_print = pretty_print
        self.budget_year = budget_year
        self.period = period
        self.organization_id = organization_id
        self.report_date = report_date

    def write(
        self,
        sheet_data: SheetData,
        output_path: str | Path,
        report_code: Optional[str] = None
    ) -> Path:
        """
        Записывает данные листа в XML файл формата Report.

        Args:
            sheet_data: Данные листа для записи.
            output_path: Путь к выходному файлу.
            report_code: Код отчёта (по умолчанию берётся из имени листа).

        Returns:
            Путь к созданному файлу.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        root = self._create_xml_tree(sheet_data, report_code)
        tree = etree.ElementTree(root)

        tree.write(
            str(output_path),
            encoding=self.encoding,
            xml_declaration=True,
            pretty_print=self.pretty_print
        )

        return output_path

    def to_string(self, sheet_data: SheetData, report_code: Optional[str] = None) -> str:
        """
        Преобразует данные листа в XML строку.

        Args:
            sheet_data: Данные листа.
            report_code: Код отчёта.

        Returns:
            XML строка.
        """
        root = self._create_xml_tree(sheet_data, report_code)
        return etree.tostring(
            root,
            encoding="unicode",
            pretty_print=self.pretty_print,
            xml_declaration=False
        )

    def write_multiple_sheets(
        self,
        sheets: list[SheetData],
        output_path: str | Path,
        wrap_element: str = "Reports"
    ) -> Path:
        """
        Записывает несколько листов в один XML файл.

        Args:
            sheets: Список данных листов.
            output_path: Путь к выходному файлу.
            wrap_element: Имя обёртывающего элемента.

        Returns:
            Путь к созданному файлу.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        reports_root = etree.Element(wrap_element)

        for sheet_data in sheets:
            report_element = self._create_xml_tree(sheet_data)
            reports_root.append(report_element)

        tree = etree.ElementTree(reports_root)
        tree.write(
            str(output_path),
            encoding=self.encoding,
            xml_declaration=True,
            pretty_print=self.pretty_print
        )

        return output_path

    def _create_xml_tree(
        self,
        sheet_data: SheetData,
        report_code: Optional[str] = None
    ) -> etree._Element:
        """
        Создаёт XML дерево из данных листа в формате Report.

        Args:
            sheet_data: Данные листа.
            report_code: Код отчёта.

        Returns:
            Корневой элемент XML дерева.
        """
        # Корневой элемент Report
        root = etree.Element("Report")

        # Метаданные отчёта
        org_id = etree.SubElement(root, "OrganizationID")
        org_id.text = self.organization_id

        budget_year = etree.SubElement(root, "BudgetYear")
        budget_year.text = self.budget_year

        period = etree.SubElement(root, "Period")
        period.text = self.period

        code = etree.SubElement(root, "ReportCode")
        code.text = report_code or sheet_data.name

        date_elem = etree.SubElement(root, "Date")
        date_elem.text = self.report_date

        # Контейнер для строк
        rows = etree.SubElement(root, "Rows")

        # Обрабатываем каждую строку данных
        for row_data in sheet_data.rows:
            row_element = self._create_row_element(row_data)
            rows.append(row_element)

        return root

    def _create_row_element(self, row_data: list) -> etree._Element:
        """
        Создаёт элемент Row из данных строки.

        Маппинг колонок Excel → XML:
        - Колонка 0 (A): Col code="2" - Denumirea indicatorului
        - Колонка 1 (B): Col code="3" - codificatorul formularului
        - Колонка 2 (C): Col code="1" - Codul rândului (также атрибут code у Row)
        - Колонки 3-8 (D-I): Col code="4"-"9" - данные

        Args:
            row_data: Данные строки из Excel.

        Returns:
            Элемент Row.
        """
        # Получаем код строки из колонки C (индекс 2)
        row_code = self._convert_value(row_data[2] if len(row_data) > 2 else None) or ""

        row_element = etree.Element("Row")
        row_element.set("isfix", "true")
        row_element.set("code", row_code)

        # Колонка A (индекс 0) → Col code="2" (Denumirea)
        col2 = etree.SubElement(row_element, "Col")
        col2.set("code", "2")
        col2.set("isNumerical", "false")
        val = self._convert_value(row_data[0] if len(row_data) > 0 else None)
        if val:
            col2.text = val
        # Если пустое - text остаётся None, lxml создаст self-closing тег

        # Колонка B (индекс 1) → Col code="3" (codificatorul)
        col3 = etree.SubElement(row_element, "Col")
        col3.set("code", "3")
        col3.set("isNumerical", "false")
        val = self._convert_value(row_data[1] if len(row_data) > 1 else None)
        if val:
            col3.text = val

        # Колонка C (индекс 2) → Col code="1" (Codul rândului)
        col1 = etree.SubElement(row_element, "Col")
        col1.set("code", "1")
        col1.set("isNumerical", "false")
        if row_code:
            col1.text = row_code

        # Колонки D-I (индексы 3-8) → Col code="4"-"9"
        for i in range(3, 9):
            col = etree.SubElement(row_element, "Col")
            col.set("code", str(i + 1))  # 4, 5, 6, 7, 8, 9
            
            value = row_data[i] if len(row_data) > i else None
            converted = self._convert_value(value)
            
            # Определяем isNumerical и значение
            if converted is None or converted == "":
                # Пустое поле - isNumerical="false", self-closing
                col.set("isNumerical", "false")
            elif self._is_numerical(value):
                # Числовое значение
                col.set("isNumerical", "true")
                col.text = converted
            else:
                # Текстовое значение (например "x")
                col.set("isNumerical", "false")
                col.text = converted

        return row_element

    @staticmethod
    def _is_numerical(value: Any) -> bool:
        """
        Проверяет, является ли значение числовым.

        Args:
            value: Значение для проверки.

        Returns:
            True если числовое.
        """
        if value is None:
            return False
        if isinstance(value, bool):
            return False
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value.replace(',', '.'))
                return True
            except (ValueError, AttributeError):
                return False
        return False

    @staticmethod
    def _convert_value(value: Any) -> Optional[str]:
        """
        Конвертирует значение в строку для XML.

        Args:
            value: Исходное значение.

        Returns:
            Строковое представление или None.
        """
        if value is None:
            return None
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            return str(value)
        
        str_value = str(value).strip()
        return str_value if str_value else None
