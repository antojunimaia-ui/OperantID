import json
from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright_stealth import Stealth
from typing import List, Dict, Any, Optional
from .utils import Logger, setup_colors

setup_colors()

INSPECT_SCRIPT = """
(() => {
    try {
        // Reset existing IDs
        document.querySelectorAll('[data-operant-id]').forEach(el => el.removeAttribute('data-operant-id'));

        const isVisible = (el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width > 0 && rect.height > 0 && 
                   rect.top >= -500 && rect.top <= window.innerHeight + 500 && // Pre-load buffer
                   rect.left >= -500 && rect.left <= window.innerWidth + 500 &&
                   style.visibility !== 'hidden' &&
                   style.display !== 'none' &&
                   style.opacity !== '0';
        };

        const isInteractive = (el) => {
            const tag = el.tagName.toLowerCase();
            const role = el.getAttribute('role');
            const style = window.getComputedStyle(el);
            
            // 1. Basic Interactive Tags
            const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'details', 'summary'];
            if (interactiveTags.includes(tag)) return true;

            // 2. ARIA Roles
            const interactiveRoles = ['button', 'link', 'checkbox', 'menuitem', 'option', 'radio', 'tab', 'textbox', 'combobox', 'searchbox'];
            if (interactiveRoles.includes(role)) return true;

            // 3. JavaScript Handlers & Attributes
            if (el.onclick || el.getAttribute('onclick') || el.hasAttribute('tabindex') || el.contentEditable === 'true') return true;

            // 4. Cursor Style (The "Gold Standard" from Browser Use)
            if (style.cursor === 'pointer') return true;

            // 5. Search Indicators (Heuristic)
            const searchIndicators = ['search', 'find', 'lookup', 'query', 'magnify'];
            const classIdText = (el.className + ' ' + el.id).toLowerCase();
            if (searchIndicators.some(ind => classIdText.includes(ind))) return true;

            // 6. Icon Detection (Small but tagged)
            const rect = el.getBoundingClientRect();
            if (rect.width >= 10 && rect.width <= 60 && rect.height >= 10 && rect.height <= 60) {
                if (el.hasAttribute('aria-label') || el.hasAttribute('title')) return true;
            }

            return false;
        };

        // Efficient DOM traversal
        const allElements = document.querySelectorAll('*');
        const interactiveItems = [];
        let count = 0;

        // Visual Markers Container
        let markerContainer = document.getElementById('operant-marker-container');
        if (markerContainer) markerContainer.remove();
        markerContainer = document.createElement('div');
        markerContainer.id = 'operant-marker-container';
        markerContainer.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 2147483647;
        `;
        document.body.appendChild(markerContainer);

        for (let el of allElements) {
            if (isVisible(el) && isInteractive(el)) {
                count++;
                const id = count;
                el.setAttribute('data-operant-id', id.toString());
                const rect = el.getBoundingClientRect();
                const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
                const scrollY = window.pageYOffset || document.documentElement.scrollTop;

                // Create visual box
                const marker = document.createElement('div');
                marker.style.cssText = `
                    position: absolute;
                    left: ${rect.left + scrollX}px;
                    top: ${rect.top + scrollY}px;
                    width: ${rect.width}px;
                    height: ${rect.height}px;
                    border: 1px solid #38bdf8;
                    background-color: rgba(56, 189, 248, 0.1);
                    pointer-events: none;
                    border-radius: 2px;
                    box-sizing: border-box;
                `;

                // Create numeric label
                const label = document.createElement('div');
                label.innerText = id;
                label.style.cssText = `
                    position: absolute;
                    top: -10px;
                    left: -10px;
                    background: #38bdf8;
                    color: black;
                    font-size: 10px;
                    font-weight: bold;
                    padding: 1px 5px;
                    border-radius: 4px;
                    line-height: 1;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.5);
                `;
                marker.appendChild(label);
                markerContainer.appendChild(marker);

                interactiveItems.push({
                    id: id,
                    tag: el.tagName.toLowerCase(),
                    type: el.type || '',
                    placeholder: el.placeholder || '',
                    role: el.getAttribute('role') || el.tagName.toLowerCase(),
                    text: (el.innerText || el.value || el.placeholder || el.getAttribute('aria-label') || el.getAttribute('title') || '').trim().substring(0, 100),
                    selector: '[data-operant-id="' + id + '"]'
                });

                if (count >= 100) break; // Token optimization limit
            }
        }

        const getSummary = () => {
            return Array.from(document.querySelectorAll('h1, h2, h3'))
                .filter(isVisible)
                .slice(0, 10)
                .map(el => el.innerText.trim().substring(0, 100))
                .join(' | ');
        };

        return {
            url: window.location.href,
            title: document.title,
            summary: getSummary(),
            interactiveElements: interactiveItems,
            viewport: { width: window.innerWidth, height: window.innerHeight }
        };
    } catch (e) { return { error: e.message }; }
})()
"""

class BrowserManager:
    def __init__(self, headless: bool = False, config: Optional[Dict[str, Any]] = None):
        self.headless = headless
        self.config = config or {}
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.pages: List[Page] = []

    async def start(self):
        self.playwright = await async_playwright().start()
        
        browser_type = self.config.get("browser_type", "chromium").lower()
        if browser_type == "firefox":
            launcher = self.playwright.firefox
        elif browser_type == "webkit":
            launcher = self.playwright.webkit
        else:
            launcher = self.playwright.chromium

        launch_args = self.config.get("args", ["--disable-blink-features=AutomationControlled"])
        
        self.browser = await launcher.launch(
            headless=self.headless,
            args=launch_args
        )

        user_agent = self.config.get("user_agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        viewport = self.config.get("viewport", {"width": 1280, "height": 720})
        
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport=viewport,
            locale=self.config.get("locale", "pt-BR"),
            timezone_id=self.config.get("timezone", "America/Sao_Paulo")
        )
        self.page = await self.context.new_page()
        await Stealth().apply_stealth_async(self.page)
        self.pages = [self.page]

    async def stop(self):
        try:
            if self.browser:
                await self.browser.close()
        except:
            pass
        try:
            if self.playwright:
                await self.playwright.stop()
        except:
            pass

    async def navigate(self, url: str):
        if not url.startswith('http'):
            url = 'https://' + url
        Logger.action(f"Navegando para: {url}")
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            Logger.warning(f"Timeout na navegação completa, mas a página provavelmente carregou: {e}")

    async def inspect(self) -> Dict[str, Any]:
        result = await self.page.evaluate(INSPECT_SCRIPT)
        Logger.inspect(result)
        return result

    async def click(self, selector: str, text: Optional[str] = None):
        try:
            # Try by selector first
            element = self.page.locator(selector)
            if await element.count() > 0:
                Logger.action(f"Clicando em seletor: {selector}")
                await element.first.click()
                return True
            
            # Fallback to text
            if text:
                text_selector = f"text='{text}'"
                element = self.page.locator(text_selector)
                if await element.count() > 0:
                    Logger.action(f"Clicando via texto: \"{text}\"")
                    await element.first.click()
                    return True
            
            Logger.warning(f"Elemento não encontrado para clicar: {selector} (Texto: {text})")
            return False
        except Exception as e:
            Logger.error(f"Erro ao clicar: {e}")
            return False

    async def type_text(self, selector: str, text: str):
        try:
            Logger.action(f"Digitando \"{text}\" em {selector}")
            element = self.page.locator(selector)
            await element.first.fill(text)
            return True
        except Exception as e:
            Logger.error(f"Erro ao digitar: {e}")
            return False

    async def scroll(self, direction: str):
        distance = 600 if direction == "down" else -600
        await self.page.evaluate(f"window.scrollBy(0, {distance})")

    async def press_enter(self):
        await self.page.keyboard.press("Enter")

    async def wait(self, ms: int):
        await self.page.wait_for_timeout(ms)

    async def mouse_move(self, x: int, y: int):
        await self.page.mouse.move(x, y)

    async def mouse_click(self, x: int, y: int):
        await self.page.mouse.click(x, y)

    async def reload(self):
        await self.page.reload()

    async def back(self):
        await self.page.go_back()

    async def forward(self):
        await self.page.go_forward()

    async def create_tab(self, url: Optional[str] = None):
        new_page = await self.context.new_page()
        await Stealth().apply_stealth_async(new_page)
        if url:
            await new_page.goto(url if url.startswith('http') else 'https://' + url)
        self.pages.append(new_page)
        self.page = new_page
        return len(self.pages) - 1

    async def switch_tab(self, index: int):
        if 0 <= index < len(self.pages):
            self.page = self.pages[index]
            await self.page.bring_to_front()
            return True
        return False

    async def close_tab(self, index: int):
        if 0 <= index < len(self.pages):
            page_to_close = self.pages.pop(index)
            await page_to_close.close()
            if not self.pages:
                self.page = await self.context.new_page()
                self.pages.append(self.page)
            elif self.page == page_to_close:
                self.page = self.pages[-1]
            return True
        return False

    def get_tabs_info(self):
        return [{"id": i, "title": p.url, "active": p == self.page} for i, p in enumerate(self.pages)]

    async def get_screenshot(self) -> str:
        if not self.page:
            return ""
        import base64
        try:
            screenshot_bytes = await self.page.screenshot(type="jpeg", quality=40)
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except:
            return ""

    async def get_screenshot_bytes(self) -> bytes:
        if not self.page:
            return b""
        try:
            return await self.page.screenshot(type="jpeg", quality=40)
        except:
            return b""
