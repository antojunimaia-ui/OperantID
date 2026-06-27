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

class ScriptExporter:
    @staticmethod
    def generate_playwright_code(history: list, config: dict = None) -> str:
        """Transforms agent history into a standalone Playwright Python script."""
        config = config or {}
        browser_type = config.get("browser_type", "chromium")
        
        code = [
            "import asyncio",
            "from playwright.async_api import async_playwright",
            "",
            "async def run_generated_script():",
            "    async with async_playwright() as p:",
            f"        browser = await p.{browser_type}.launch(headless=False)",
            "        context = await browser.new_context(",
            f"            user_agent='{config.get('user_agent', '')}',",
            f"            viewport={config.get('viewport', {'width': 1280, 'height': 720})},",
            f"            locale='{config.get('locale', 'pt-BR')}',",
            f"            timezone_id='{config.get('timezone', 'America/Sao_Paulo')}'",
            "        )",
            "        page = await context.new_page()",
            "        pages = [page]",
            "        ",
            "        print('🚀 Iniciando execução do script exportado...')",
            ""
        ]

        for entry in history:
            action = entry.get("action", {})
            atype = action.get("type", "").lower()
            reasoning = entry.get("reasoning", "").replace("'", "\\'")
            
            code.append(f"        # Reasoning: {reasoning}")
            
            if atype == "navigate":
                code.append(f"        await page.goto('{action.get('url')}', wait_until='domcontentloaded')")
            elif atype == "click":
                selector = action.get("selector")
                text = action.get("text")
                if selector:
                    code.append(f"        await page.locator('{selector}').first.click()")
                elif text:
                    code.append(f"        await page.get_by_text('{text}').first.click()")
            elif atype == "type":
                code.append(f"        await page.locator('{action.get('selector')}').first.fill('{action.get('text')}')")
            elif atype == "scroll":
                dist = 600 if action.get("direction") == "down" else -600
                code.append(f"        await page.evaluate('window.scrollBy(0, {dist})')")
            elif atype == "wait":
                code.append(f"        await page.wait_for_timeout({action.get('ms', 2000)})")
            elif atype == "pressenter":
                code.append("        await page.keyboard.press('Enter')")
            elif atype == "reload":
                code.append("        await page.reload()")
            elif atype == "createtab":
                code.append(f"        page = await context.new_page()")
                if action.get("url"):
                    code.append(f"        await page.goto('{action.get('url')}')")
                code.append("        pages.append(page)")
            elif atype == "switchtab":
                tab_id = action.get("tabId", 0)
                code.append(f"        page = pages[{tab_id}]")
                code.append("        await page.bring_to_front()")
            elif atype == "closetab":
                tab_id = action.get("tabId", 0)
                code.append(f"        await pages[{tab_id}].close()")
            
            code.append("        await asyncio.sleep(1)  # Estabilidade")
            code.append("")

        code.extend([
            "        print('✅ Execução concluída com sucesso!')",
            "        await browser.close()",
            "",
            "if __name__ == '__main__':",
            "    asyncio.run(run_generated_script())"
        ])

        return "\n".join(code)

def setup_colors():
    """Ensure ANSI colors work on Windows."""
    if sys.platform == "win32":
        try:
            import colorama
            colorama.init()
        except ImportError:
            pass
