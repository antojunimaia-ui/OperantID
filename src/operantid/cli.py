import sys
import argparse
from operantid.ui import launch_ui

def main():
    parser = argparse.ArgumentParser(description="OperantID CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # "webui" command
    webui_parser = subparsers.add_parser("webui", help="Launch the OperantID WebUI Playground")
    webui_parser.add_argument("--port", type=int, default=5000, help="Port to run the WebUI on (default: 5000)")

    args = parser.parse_args()

    if args.command == "webui":
        launch_ui(port=args.port)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
