import sys
from datetime import datetime

class Logger:
    """Simple logger with colors for the OperantID library."""
    
    # ANSI Colors
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    END = "\033[0m"

    @staticmethod
    def _log(msg: str, color: str = ""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Logger.BOLD}[{timestamp}]{Logger.END} {color}{msg}{Logger.END}")

    @staticmethod
    def info(msg: str):
        Logger._log(f"ℹ️  {msg}", Logger.CYAN)

    @staticmethod
    def success(msg: str):
        Logger._log(f"✅ {msg}", Logger.GREEN)

    @staticmethod
    def warning(msg: str):
        Logger._log(f"⚠️  {msg}", Logger.YELLOW)

    @staticmethod
    def error(msg: str):
        Logger._log(f"❌ {msg}", Logger.RED)

    @staticmethod
    def action(msg: str):
        Logger._log(f"⚡ {msg}", Logger.MAGENTA)

    @staticmethod
    def inspect(data: dict):
        Logger._log("🔍 [Inspeção de Página]", Logger.BOLD + Logger.YELLOW)
        print(f"   {Logger.YELLOW}URL:{Logger.END} {data.get('url')}")
        print(f"   {Logger.YELLOW}Título:{Logger.END} {data.get('title')}")
        items = data.get('interactiveElements', [])
        print(f"   {Logger.YELLOW}Elementos Interativos ({len(items)}):{Logger.END}")
        for item in items[:15]: # Show first 15
            print(f"     - [{item['id']}] {item['tag']} ({item['role']}): \"{item['text']}\"")
        if len(items) > 15:
            print(f"     ... ({len(items) - 15} mais)")

def setup_colors():
    """Ensure ANSI colors work on Windows."""
    if sys.platform == "win32":
        try:
            import colorama
            colorama.init()
        except ImportError:
            pass
