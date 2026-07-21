#!/usr/bin/env python3
import sys
import argparse


def main():
    if len(sys.argv) > 1 and sys.argv[0] != 'cli' and sys.argv[1] == 'cli':
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from src.cli import cli_main
        return cli_main()

    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if first_arg.endswith('.xlsx'):
            from src.cli import cli_main
            return cli_main()
        if first_arg not in ['--host', '--port', '-h', '--help', '--reload']:
            if not first_arg.startswith('-'):
                print(f"Unknown command: {first_arg}")
                print("Use 'python main.py cli' for command line interface")
                print("Or 'python main.py' to start the web server")
                return 1

    parser = argparse.ArgumentParser(description="Rowline Converter / Filler")
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--workers', type=int, default=0,
                        help='Number of workers (0 = auto)')
    parser.add_argument('--reload', action='store_true')

    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError:
        print("Install uvicorn: pip install uvicorn")
        return 1

    import os
    import platform

    if platform.system() == 'Windows':
        workers = 1
    else:
        cpu_count = os.cpu_count() or 4
        workers = args.workers if args.workers > 0 else min(cpu_count, 8)

    workers = 1 if args.reload else workers

    print(f"  Rowline Server — http://{args.host}:{args.port}")
    print(f"  Workers: {workers}, Platform: {platform.system()}")

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
