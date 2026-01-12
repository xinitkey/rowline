#!/usr/bin/env python3
"""
Продвинутый пример использования XLSX to XML Converter.

Демонстрирует:
- Низкоуровневый доступ к модулям
- Кастомизацию вывода
- Обработку нескольких файлов
"""

import sys
from pathlib import Path

# Добавляем корневую папку проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import XlsxReader, XmlWriter, XlsxToXmlConverter


def example_custom_reader():
    """Пример использования XlsxReader напрямую."""
    print("=== Пример: Чтение XLSX ===")
    
    # with XlsxReader("data.xlsx") as reader:
    #     # Список листов
    #     print(f"Листы в файле: {reader.sheet_names}")
    #     
    #     # Чтение конкретного листа
    #     sheet = reader.read_sheet("Sheet1")
    #     print(f"Лист: {sheet.name}")
    #     print(f"Заголовки: {sheet.headers}")
    #     print(f"Количество строк: {len(sheet.rows)}")
    #     
    #     # Первые 3 строки
    #     for i, row in enumerate(sheet.rows[:3]):
    #         print(f"  Строка {i+1}: {row}")
    
    print("Раскомментируйте код и укажите путь к файлу.\n")


def example_custom_writer():
    """Пример использования XmlWriter с кастомными настройками."""
    print("=== Пример: Кастомный XML Writer ===")
    
    # Создаём writer с кастомными именами элементов
    writer = XmlWriter(
        root_element="products",
        row_element="product",
        encoding="utf-8",
        pretty_print=True
    )
    
    # with XlsxReader("products.xlsx") as reader:
    #     sheet_data = reader.read_sheet()
    #     
    #     # Записываем в файл
    #     writer.write(sheet_data, "products.xml")
    #     
    #     # Или получаем строку
    #     xml_string = writer.to_string(sheet_data)
    #     print(xml_string)
    
    print("Раскомментируйте код и укажите путь к файлу.\n")


def example_batch_processing():
    """Пример пакетной обработки нескольких файлов."""
    print("=== Пример: Пакетная обработка ===")
    
    converter = XlsxToXmlConverter(
        root_element="data",
        row_element="item"
    )
    
    # Обработка всех xlsx файлов в папке
    # input_folder = Path("./input_files")
    # output_folder = Path("./output_files")
    # output_folder.mkdir(exist_ok=True)
    # 
    # for xlsx_file in input_folder.glob("*.xlsx"):
    #     output_file = output_folder / f"{xlsx_file.stem}.xml"
    #     converter.convert(xlsx_file, output_file)
    #     print(f"Конвертирован: {xlsx_file.name} → {output_file.name}")
    
    print("Раскомментируйте код и укажите пути к папкам.\n")


def example_with_custom_header_row():
    """Пример с нестандартным расположением заголовков."""
    print("=== Пример: Нестандартные заголовки ===")
    
    converter = XlsxToXmlConverter()
    
    # Если заголовки в 3-й строке, а данные начинаются с 5-й
    # converter.convert(
    #     "report.xlsx",
    #     "report.xml",
    #     header_row=3,
    #     start_row=5
    # )
    
    print("Раскомментируйте код и укажите путь к файлу.\n")


def example_multiple_sheets_processing():
    """Пример обработки всех листов с итерацией."""
    print("=== Пример: Итерация по листам ===")
    
    # with XlsxReader("workbook.xlsx") as reader:
    #     writer = XmlWriter()
    #     
    #     for sheet_data in reader.read_all_sheets():
    #         print(f"\nОбработка листа: {sheet_data.name}")
    #         print(f"  Колонок: {len(sheet_data.headers)}")
    #         print(f"  Строк: {len(sheet_data.rows)}")
    #         
    #         # Можно применить фильтрацию или трансформацию
    #         # перед записью
    #         
    #         output_file = f"{sheet_data.name}.xml"
    #         writer.write(sheet_data, output_file)
    #         print(f"  Сохранено в: {output_file}")
    
    print("Раскомментируйте код и укажите путь к файлу.\n")


def main():
    """Запуск всех примеров."""
    print("=" * 60)
    print("XLSX to XML Converter - Продвинутые примеры")
    print("=" * 60)
    print()
    
    example_custom_reader()
    example_custom_writer()
    example_batch_processing()
    example_with_custom_header_row()
    example_multiple_sheets_processing()
    
    print("=" * 60)
    print("Для запуска примеров раскомментируйте нужный код")
    print("и укажите пути к вашим файлам.")
    print("=" * 60)


if __name__ == "__main__":
    main()
