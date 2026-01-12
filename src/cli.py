#!/usr/bin/env python3
"""
CLI модуль для XLSX to XML Converter / Filler.
"""

import argparse
import sys
from pathlib import Path

from src import XlsxToXmlConverter, XmlFiller


def parse_arguments() -> argparse.Namespace:
    """Парсит аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description="Заполнение XML шаблона данными из XLSX / Конвертер XLSX в XML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Режим заполнения шаблона (по умолчанию):
  %(prog)s data.xlsx -t template.xml -o output_dir   # Заполнить шаблон данными

Режим конвертации:
  %(prog)s data.xlsx --convert -o output_dir         # Создать XML из XLSX

Примеры:
  %(prog)s data.xlsx -t RF-FD-048BL.xml -o results/
  %(prog)s data.xlsx -t template.xml -o result.xml --single -s "Sheet1"
        """
    )

    parser.add_argument("input", type=str, help="Путь к входному XLSX файлу")
    parser.add_argument("-t", "--template", type=str, default=None, 
                        help="Путь к XML шаблону (для режима заполнения)")
    parser.add_argument("-o", "--output", type=str, default=None, 
                        help="Путь к выходной папке/файлу")
    parser.add_argument("-s", "--sheet", type=str, default=None, 
                        help="Имя листа (по умолчанию: все листы)")
    parser.add_argument("--single", action="store_true", 
                        help="Обработать только один лист")
    
    # Параметры для режима заполнения
    parser.add_argument("--code-col", type=int, default=6, 
                        help="Столбец с code (1-based, по умолчанию: 6=F)")
    parser.add_argument("--data-start-col", type=int, default=7, 
                        help="Начальный столбец данных (1-based, по умолчанию: 7=G)")
    parser.add_argument("--data-end-col", type=int, default=12, 
                        help="Конечный столбец данных (1-based, по умолчанию: 12=L)")
    parser.add_argument("--start-row", type=int, default=9, 
                        help="Строка начала данных (по умолчанию: 9)")
    
    # Режим конвертации
    parser.add_argument("--convert", action="store_true", 
                        help="Режим конвертации (создание нового XML)")
    parser.add_argument("--budget-year", type=str, default="", help="Бюджетный год")
    parser.add_argument("--period", type=str, default="", help="Период отчёта")
    parser.add_argument("--org-id", type=str, default="", help="ID организации")
    parser.add_argument("--date", type=str, default="", help="Дата отчёта")
    
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный вывод")

    return parser.parse_args()


def run_fill_mode(args) -> int:
    """Режим заполнения XML шаблона."""
    input_path = Path(args.input)
    
    if not args.template:
        print("Ошибка: Укажите путь к XML шаблону с помощью -t/--template", file=sys.stderr)
        return 1
    
    template_path = Path(args.template)
    if not template_path.exists():
        print(f"Ошибка: Шаблон не найден: {template_path}", file=sys.stderr)
        return 1

    filler = XmlFiller(template_path)
    
    try:
        if args.single or args.sheet:
            # Один лист
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
            print(f"Создан: {result_path}")
        else:
            # Все листы
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
            print(f"Обработано листов: {len(result_paths)}")
            if args.verbose:
                for path in result_paths:
                    print(f"  → {path}")
        
        return 0
        
    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_convert_mode(args) -> int:
    """Режим конвертации XLSX в XML."""
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
            print(f"Создан: {result_path}")
        else:
            result_paths = converter.convert_all_sheets(
                input_path=input_path,
                output_path=args.output,
                start_row=args.start_row,
                separate_files=True
            )
            print(f"Конвертировано листов: {len(result_paths)}")
            if args.verbose:
                for path in result_paths:
                    print(f"  → {path}")

        return 0

    except Exception as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def cli_main() -> int:
    """Главная функция CLI."""
    args = parse_arguments()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Ошибка: Файл не найден: {input_path}", file=sys.stderr)
        return 1

    if not input_path.suffix.lower() == ".xlsx":
        print(f"Ошибка: Ожидается файл .xlsx, получен: {input_path.suffix}", file=sys.stderr)
        return 1

    if args.convert:
        return run_convert_mode(args)
    else:
        return run_fill_mode(args)
