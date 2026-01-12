#!/usr/bin/env python3
"""
Базовый пример использования XLSX to XML Converter.
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import XlsxToXmlConverter


def main():
    """Демонстрация базового использования."""
    
    # Создаём конвертер с настройками по умолчанию
    converter = XlsxToXmlConverter()
    
    # Пример 1: Простая конвертация
    # converter.convert("input.xlsx", "output.xml")
    
    # Пример 2: С указанием листа
    # converter.convert("input.xlsx", "output.xml", sheet_name="Данные")
    
    # Пример 3: Все листы в один файл
    # converter.convert_all_sheets("input.xlsx", "all_sheets.xml")
    
    # Пример 4: Каждый лист в отдельный файл
    # converter.convert_all_sheets("input.xlsx", separate_files=True)
    
    # Пример 5: Получить XML как строку
    # xml_str = converter.to_xml_string("input.xlsx")
    # print(xml_str)
    
    print("Раскомментируйте примеры и укажите путь к вашему XLSX файлу.")


if __name__ == "__main__":
    main()
