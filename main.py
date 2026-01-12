#!/usr/bin/env python3
"""
XLSX to XML Converter / Filler - Главный файл запуска.

Запуск веб-сервера:
    python main.py                  # Запустить FastAPI сервер
    python main.py --host 0.0.0.0   # Доступ из сети
    python main.py --port 8080      # Другой порт

Запуск CLI:
    python main.py cli data.xlsx -t template.xml -o output/
    python main.py cli data.xlsx --convert -o output/
"""

import sys
import argparse


def main():
    """Главная функция - роутер между веб-сервером и CLI."""
    
    # Если первый аргумент 'cli' - запускаем CLI режим
    if len(sys.argv) > 1 and sys.argv[0] != 'cli' and sys.argv[1] == 'cli':
        # Убираем 'cli' из аргументов и запускаем CLI
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from src.cli import cli_main
        return cli_main()
    
    # Проверяем, есть ли аргументы похожие на CLI
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        # Если это файл .xlsx - запускаем CLI
        if first_arg.endswith('.xlsx'):
            from src.cli import cli_main
            return cli_main()
        # Если это не флаг сервера - показываем help
        if first_arg not in ['--host', '--port', '-h', '--help', '--reload']:
            if not first_arg.startswith('-'):
                print(f"Неизвестная команда: {first_arg}")
                print("Используйте 'python main.py cli' для командной строки")
                print("Или 'python main.py' для запуска веб-сервера")
                return 1
    
    # Парсим аргументы для веб-сервера
    parser = argparse.ArgumentParser(
        description="XLSX to XML Converter - Web Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры запуска:
  python main.py                  # Запуск на http://127.0.0.1:8000
  python main.py --host 0.0.0.0   # Доступ из сети
  python main.py --port 8080      # Другой порт
  python main.py --reload         # Авто-перезагрузка при изменениях

CLI режим:
  python main.py cli data.xlsx -t template.xml -o output/
  python main.py cli data.xlsx --convert -o output/
        """
    )
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Хост для сервера (по умолчанию: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000,
                        help='Порт для сервера (по умолчанию: 8000)')
    parser.add_argument('--workers', type=int, default=4,
                        help='Количество воркеров (по умолчанию: 4)')
    parser.add_argument('--reload', action='store_true',
                        help='Авто-перезагрузка при изменениях кода')
    
    args = parser.parse_args()
    
    # Запускаем FastAPI сервер
    try:
        import uvicorn
    except ImportError:
        print("Для запуска веб-сервера установите uvicorn:")
        print("  pip install uvicorn")
        print("\nИли используйте CLI режим:")
        print("  python main.py cli data.xlsx -t template.xml -o output/")
        return 1
    
    # Определяем количество воркеров
    import os
    import platform
    
    # На Windows многопроцессный режим uvicorn работает нестабильно
    # Используем 1 воркер, но с большим пулом потоков в api.py
    if platform.system() == 'Windows':
        workers = 1
        if args.workers > 1:
            print("  ⚠️  На Windows используется 1 воркер (ограничение uvicorn)")
            print("      Параллельность обеспечивается пулом потоков")
    else:
        workers = args.workers if not args.reload else 1
    
    print("=" * 50)
    print("  XLSX to XML Converter - Web Server")
    print("=" * 50)
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"  API: http://{args.host}:{args.port}/api/health")
    print(f"  Docs: http://{args.host}:{args.port}/docs")
    print(f"  Workers: {workers}")
    print("=" * 50)
    print("  Нажмите Ctrl+C для остановки")
    print("=" * 50)
    
    uvicorn.run(
        "src.api:app",
        host=args.host,
        port=args.port,
        workers=workers,
        reload=args.reload
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
