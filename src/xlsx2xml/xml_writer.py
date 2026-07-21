from pathlib import Path
from typing import Optional, Any
from datetime import datetime, date

from lxml import etree

from .xlsx_reader import SheetData


class XmlWriter:
    def __init__(
        self,
        encoding: str = "utf-8",
        pretty_print: bool = True,
        budget_year: str = "",
        period: str = "",
        organization_id: str = "",
        report_date: str = ""
    ):
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
        root = etree.Element("Report")

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

        rows = etree.SubElement(root, "Rows")

        for row_data in sheet_data.rows:
            row_element = self._create_row_element(row_data)
            rows.append(row_element)

        return root

    def _create_row_element(self, row_data: list) -> etree._Element:
        row_code = self._convert_value(row_data[2] if len(row_data) > 2 else None) or ""

        row_element = etree.Element("Row")
        row_element.set("isfix", "true")
        row_element.set("code", row_code)

        col2 = etree.SubElement(row_element, "Col")
        col2.set("code", "2")
        col2.set("isNumerical", "false")
        val = self._convert_value(row_data[0] if len(row_data) > 0 else None)
        if val:
            col2.text = val

        col3 = etree.SubElement(row_element, "Col")
        col3.set("code", "3")
        col3.set("isNumerical", "false")
        val = self._convert_value(row_data[1] if len(row_data) > 1 else None)
        if val:
            col3.text = val

        col1 = etree.SubElement(row_element, "Col")
        col1.set("code", "1")
        col1.set("isNumerical", "false")
        if row_code:
            col1.text = row_code

        for i in range(3, 9):
            col = etree.SubElement(row_element, "Col")
            col.set("code", str(i + 1))

            value = row_data[i] if len(row_data) > i else None
            converted = self._convert_value(value)

            if converted is None or converted == "":
                col.set("isNumerical", "false")
            elif self._is_numerical(value):
                col.set("isNumerical", "true")
                col.text = converted
            else:
                col.set("isNumerical", "false")
                col.text = converted

        return row_element

    @staticmethod
    def _is_numerical(value: Any) -> bool:
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
