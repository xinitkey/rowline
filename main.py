#!/usr/bin/env python3
"""
Rowline Converter / Filler - Main start file.

Starting the web server:
    python main.py                  # Start FastAPI server
    python main.py --host 0.0.0.0   # Network access
    python main.py --port 8080      # Different port

Starting CLI:
    python main.py cli data.xlsx -t template.xml -o output/
    python main.py cli data.xlsx --convert -o output/
"""

import sys
import argparse


def main():
    """Main function - router between web server and CLI."""
    
    # If the first argument is 'cli' - start CLI mode
    if len(sys.argv) > 1 and sys.argv[0] != 'cli' and sys.argv[1] == 'cli':
        # Remove 'cli' from arguments and start CLI
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        from src.cli import cli_main
        return cli_main()
    
    # Check if there are arguments resembling CLI
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        # If it's a .xlsx file - start CLI
        if first_arg.endswith('.xlsx'):
            from src.cli import cli_main
            return cli_main()
        # If it's not a server flag - show help
        if first_arg not in ['--host', '--port', '-h', '--help', '--reload']:
            if not first_arg.startswith('-'):
                print(f"Unknown command: {first_arg}")
                print("Use 'python main.py cli' for command line interface")
                print("Or 'python main.py' to start the web server")
                return 1
    
    # Parse arguments for web server    
    parser = argparse.ArgumentParser(
        description="Rowline Converter / Filler - Web Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples of starting the web server:
  python main.py                  # Start at http://127.0.0.1:8000
  python main.py --host 0.0.0.0   # Network access
  python main.py --port 8080      # Different port
  python main.py --reload         # Auto-reload on code changes
CLI mode examples:
  python main.py cli data.xlsx -t template.xml -o output/
  python main.py cli data.xlsx --convert -o output/
        """
    )
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='Host for the server (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8000,
                        help='Port for the server (default: 8000)')
    parser.add_argument('--workers', type=int, default=4,
                        help='Number of workers (default: 4)')
    parser.add_argument('--reload', action='store_true',
                        help='Auto-reload on code changes')
    
    args = parser.parse_args()
    
    # Start the web server
    try:
        import uvicorn
    except ImportError:
        print("To run the web server, install uvicorn:")
        print("  pip install uvicorn")
        print("\nOr use CLI mode:")
        print("  python main.py cli data.xlsx -t template.xml -o output/")
        return 1
    
    # Determine number of workers
    import os
    import platform
    from src.api import MAX_WORKERS, MAX_CONCURRENT_OPERATIONS, USE_MULTIPROCESSING, PROCESS_POOL_SIZE
    
    # On Windows, uvicorn's multiprocessing mode is unstable
    # Use 1 worker, but with a large thread pool in api.py
    if platform.system() == 'Windows':
        workers = 1
        if args.workers > 1:
            print("  [WARNING] On Windows using 1 worker (uvicorn limitation)")
            print("      Parallelism is provided by the thread pool")
    else:
        # On Linux/Unix systems use full power
        cpu_count = os.cpu_count()
        default_workers = int(os.getenv('UVICORN_WORKERS', min(cpu_count, 8)))  # Allow env override
        
        if args.workers == 4:  # default
            # Automatically calculate the optimal number of workers
            workers = default_workers
        else:
            workers = args.workers
        
        if not args.reload and workers > 1:
            print(f"  [INFO] On {platform.system()} using {workers} uvicorn workers")
            print("      Full multiprocess architecture")
    
    workers = workers if not args.reload else 1
    
    print("=" * 50)
    print("  Rowline Converter / Filler - Web Server")
    print("=" * 50)
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"  API: http://{args.host}:{args.port}/api/health")
    print(f"  Docs: http://{args.host}:{args.port}/docs")
    print(f"  Workers: {workers}")
    print(f"  Thread Pool: {MAX_WORKERS} threads")
    print(f"  Max Concurrent Ops: {MAX_CONCURRENT_OPERATIONS}")
    if USE_MULTIPROCESSING:
        print(f"  Process Pool: {PROCESS_POOL_SIZE} processes")
    else:
        print("  Process Pool: Disabled")
    print(f"  Platform: {platform.system()} (optimized configuration)")
    print("=" * 50)
    print("=" * 50)
    print("  Press Ctrl+C to stop")
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
