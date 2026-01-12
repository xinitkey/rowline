"""
Модуль для заполнения XML шаблона данными из XLSX.
"""

from pathlib import Path
from typing import Optional, Any
from copy import deepcopy
from datetime import datetime

from lxml import etree
from openpyxl import load_workbook


class XmlFiller:
    """
    Класс для заполнения XML шаблона данными из XLSX.
    
    Логика:
    - XML шаблон содержит структуру с Row elements, каждый имеет атрибут code
    - XLSX содержит данные: столбец F = code, столбцы G-L = значения
    - Заполняем Col code="4"-"9" где isNumerical="true" значениями из XLSX
    """

    def __init__(self, template_path: str | Path):
        """
        Инициализация с загрузкой XML шаблона.

        Args:
            template_path: Путь к XML шаблону.
        """
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"Шаблон не найден: {self.template_path}")
        
        # Парсим XML с сохранением форматирования
        parser = etree.XMLParser(remove_blank_text=False)
        self.template_tree = etree.parse(str(self.template_path), parser)
        self.template_root = self.template_tree.getroot()
        
        # Кешируем сериализованный шаблон для быстрого копирования
        self._template_bytes = etree.tostring(self.template_root, encoding='unicode')
        
        # Строим индекс Row по code для быстрого поиска
        self._build_row_index()

    def _build_row_index(self):
        """Строит индекс Row элементов по атрибуту code."""
        self.row_index: dict[str, etree._Element] = {}
        for row in self.template_root.findall(".//Row"):
            code = row.get("code", "")
            if code:
                self.row_index[code] = row
    
    def _create_template_copy(self) -> tuple[etree._Element, dict[str, etree._Element]]:
        """
        Быстро создаёт копию шаблона из кешированных байтов.
        
        Returns:
            Кортеж (root element, row_index dict)
        """
        # Парсим из строки - быстрее чем deepcopy
        filled_root = etree.fromstring(self._template_bytes)
        
        # Строим индекс для копии
        row_index: dict[str, etree._Element] = {}
        for row in filled_root.iter("Row"):  # iter быстрее чем findall
            code = row.get("code")
            if code:
                row_index[code] = row
        
        return filled_root, row_index

    def fill_from_xlsx(
        self,
        xlsx_path: str | Path,
        output_path: str | Path,
        sheet_name: Optional[str] = None,
        code_column: int = 6,      # F = 6
        data_start_column: int = 7, # G = 7
        data_end_column: int = 12,  # L = 12
        start_row: int = 9
    ) -> Path:
        """
        Заполняет XML шаблон данными из XLSX.

        Args:
            xlsx_path: Путь к XLSX файлу с данными.
            output_path: Путь для сохранения результата.
            sheet_name: Имя листа (по умолчанию - активный).
            code_column: Номер столбца с code (1-based, F=6).
            data_start_column: Начальный столбец данных (1-based, G=7).
            data_end_column: Конечный столбец данных (1-based, L=12).
            start_row: Строка начала данных (1-based).

        Returns:
            Путь к созданному файлу.
        """
        xlsx_path = Path(xlsx_path)
        output_path = Path(output_path)
        
        if not xlsx_path.exists():
            raise FileNotFoundError(f"XLSX файл не найден: {xlsx_path}")

        # Быстро создаём копию шаблона
        filled_root, row_index = self._create_template_copy()

        # Читаем XLSX
        wb = load_workbook(xlsx_path, read_only=True, data_only=True)
        
        if sheet_name:
            sheet = wb[sheet_name]
        else:
            sheet = wb.active

        updates_count = 0
        
        # Обрабатываем каждую строку XLSX
        for row in sheet.iter_rows(min_row=start_row, min_col=1, max_col=data_end_column):
            # Получаем code из столбца F (индекс code_column - 1)
            code_cell = row[code_column - 1]
            code_value = code_cell.value
            
            if code_value is None:
                continue
                
            code_str = self._normalize_code(code_value)
            
            if not code_str or code_str not in row_index:
                continue

            # Получаем значения из столбцов G-L
            data_values = []
            for i in range(data_start_column - 1, data_end_column):
                if i < len(row):
                    data_values.append(row[i].value)
                else:
                    data_values.append(None)

            # Обновляем XML Row
            xml_row = row_index[code_str]
            updated = self._update_row_values(xml_row, data_values)
            if updated:
                updates_count += 1

        wb.close()

        # Сохраняем результат
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        tree = etree.ElementTree(filled_root)
        tree.write(
            str(output_path),
            encoding="UTF-8",
            xml_declaration=True,
            pretty_print=True
        )

        return output_path

    def _normalize_code(self, value: Any) -> str:
        """
        Нормализует значение code.

        Args:
            value: Значение из ячейки.

        Returns:
            Строковое представление code.
        """
        if value is None:
            return ""
        
        # Обработка дат - Excel может интерпретировать "8.1" как дату
        # (8 января = 2026-01-08)
        if isinstance(value, datetime):
            # Конвертируем обратно: день.месяц (8 января -> 8.1)
            return f"{value.day}.{value.month}"
        
        if isinstance(value, float):
            # Убираем .0 для целых чисел
            if value.is_integer():
                return str(int(value))
            return str(value)
        
        return str(value).strip()

    def _update_row_values(
        self,
        xml_row: etree._Element,
        values: list
    ) -> bool:
        """
        Обновляет значения в Row элементе.
        Оптимизировано: строим индекс Col один раз.

        Args:
            xml_row: XML Row элемент.
            values: Список значений из XLSX (для col 4-9).

        Returns:
            True если были обновления.
        """
        # Строим индекс Col элементов по code
        col_index = {col.get("code"): col for col in xml_row.iter("Col")}
        
        updated = False
        col_codes = ("4", "5", "6", "7", "8", "9")
        
        for i, col_code in enumerate(col_codes):
            if i >= len(values):
                break
            
            col_elem = col_index.get(col_code)
            if col_elem is None or col_elem.get("isNumerical") != "true":
                continue
            
            value = values[i]
            if value is not None:
                new_value = self._format_value(value)
                if new_value and col_elem.text != new_value:
                    col_elem.text = new_value
                    updated = True

        return updated

    def _format_value(self, value: Any) -> Optional[str]:
        """
        Форматирует значение для XML.

        Args:
            value: Значение из XLSX.

        Returns:
            Отформатированная строка или None.
        """
        if value is None:
            return None
        
        if isinstance(value, bool):
            return None
        
        if isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            # Округляем до 2 знаков после запятой
            return str(round(value, 2))
        
        if isinstance(value, int):
            return str(value)
        
        # Пробуем преобразовать строку в число
        str_value = str(value).strip()
        if not str_value:
            return None
            
        try:
            num = float(str_value.replace(",", "."))
            if num.is_integer():
                return str(int(num))
            return str(round(num, 2))
        except ValueError:
            return None

    def fill_all_sheets(
        self,
        xlsx_path: str | Path,
        output_dir: str | Path,
        code_column: int = 6,
        data_start_column: int = 7,
        data_end_column: int = 12,
        start_row: int = 9
    ) -> list[Path]:
        """
        Заполняет XML шаблон данными из всех листов XLSX.
        Оптимизировано: открывает workbook один раз.

        Args:
            xlsx_path: Путь к XLSX файлу.
            output_dir: Папка для сохранения результатов.
            code_column: Номер столбца с code.
            data_start_column: Начальный столбец данных.
            data_end_column: Конечный столбец данных.
            start_row: Строка начала данных.

        Returns:
            Список путей к созданным файлам.
        """
        xlsx_path = Path(xlsx_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Открываем workbook один раз для всех листов
        wb = load_workbook(xlsx_path, read_only=True, data_only=True)
        
        result_paths = []
        
        for sheet_name in wb.sheetnames:
            # Создаём безопасное имя файла
            safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in sheet_name)
            output_path = output_dir / f"{safe_name}.xml"
            
            try:
                # Быстро создаём копию шаблона
                filled_root, row_index = self._create_template_copy()
                
                sheet = wb[sheet_name]
                
                # Обрабатываем каждую строку XLSX
                for row in sheet.iter_rows(min_row=start_row, min_col=1, max_col=data_end_column):
                    code_cell = row[code_column - 1]
                    code_value = code_cell.value
                    
                    if code_value is None:
                        continue
                        
                    code_str = self._normalize_code(code_value)
                    
                    if not code_str or code_str not in row_index:
                        continue

                    # Получаем значения из столбцов G-L
                    data_values = [
                        row[i].value if i < len(row) else None
                        for i in range(data_start_column - 1, data_end_column)
                    ]

                    # Обновляем XML Row
                    self._update_row_values(row_index[code_str], data_values)
                
                # Сохраняем результат
                tree = etree.ElementTree(filled_root)
                tree.write(
                    str(output_path),
                    encoding="UTF-8",
                    xml_declaration=True,
                    pretty_print=True
                )
                result_paths.append(output_path)
                
            except Exception:
                # Молча пропускаем ошибочные листы
                pass
        
        wb.close()
        return result_paths
