import json
from typing import List, Dict, Any, Optional
from .browser import BrowserManager

class BrowserToolKit:
    def __init__(self, browser_manager: BrowserManager):
        self.browser = browser_manager

    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Returns a list of tool definitions in the common OpenAI/Gemini format.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "navigate",
                    "description": "Navega para uma URL específica no navegador.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "A URL completa (ex: https://google.com)"}
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "click",
                    "description": "Clica em um elemento da página usando um seletor ou texto.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "O seletor CSS do elemento (ex: [data-operant-id='1'])"},
                            "text": {"type": "string", "description": "Opcional: O texto contido no elemento como fallback"}
                        },
                        "required": ["selector"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "type_text",
                    "description": "Digita um texto em um campo de entrada (input/textarea).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string", "description": "O seletor CSS do campo"},
                            "text": {"type": "string", "description": "O texto a ser digitado"}
                        },
                        "required": ["selector", "text"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "scroll",
                    "description": "Rola a página para cima ou para baixo.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "direction": {"type": "string", "enum": ["up", "down"], "description": "A direção da rolagem"}
                        },
                        "required": ["direction"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "press_enter",
                    "description": "Pressiona a tecla Enter no teclado.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "wait",
                    "description": "Aguarda por um período de tempo determinado.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ms": {"type": "integer", "description": "Tempo em milissegundos (padrão: 2000)"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_tab",
                    "description": "Abre uma nova aba no navegador.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "description": "URL opcional para carregar na nova aba"}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "switch_tab",
                    "description": "Alterna para uma aba aberta específica.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tab_id": {"type": "integer", "description": "O ID da aba (id retornado pelo estado do navegador)"}
                        },
                        "required": ["tab_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "close_tab",
                    "description": "Fecha uma aba específica.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "tab_id": {"type": "integer", "description": "ID da aba a ser fechada"}
                        },
                        "required": ["tab_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_state",
                    "description": "Retorna o estado atual da página, incluindo elementos interativos e capturas.",
                    "parameters": {"type": "object", "properties": {}}
                }
            }
        ]

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> Any:
        """
        Executes a tool call and returns the result.
        """
        if name == "navigate":
            await self.browser.navigate(args.get("url"))
            return {"status": "success", "message": f"Navegado para {args.get('url')}"}
        
        elif name == "click":
            success = await self.browser.click(args.get("selector"), args.get("text"))
            return {"status": "success" if success else "error", "element": args.get("selector")}
        
        elif name == "type_text":
            success = await self.browser.type_text(args.get("selector"), args.get("text"))
            return {"status": "success" if success else "error", "element": args.get("selector")}
        
        elif name == "scroll":
            await self.browser.scroll(args.get("direction"))
            return {"status": "success", "direction": args.get("direction")}
        
        elif name == "press_enter":
            await self.browser.press_enter()
            return {"status": "success"}
        
        elif name == "wait":
            await self.browser.wait(args.get("ms", 2000))
            return {"status": "success"}
        
        elif name == "create_tab":
            tab_index = await self.browser.create_tab(args.get("url"))
            return {"status": "success", "tab_index": tab_index}
        
        elif name == "switch_tab":
            success = await self.browser.switch_tab(args.get("tab_id"))
            return {"status": "success" if success else "error"}
        
        elif name == "close_tab":
            success = await self.browser.close_tab(args.get("tab_id"))
            return {"status": "success" if success else "error"}
            
        elif name == "get_state":
            return await self.get_context()
            
        return {"status": "error", "message": f"Tool {name} not found"}

    async def get_context(self) -> Dict[str, Any]:
        """
        Returns the current state of the browser to be used as context in the Prompt.
        """
        page_info = await self.browser.inspect()
        tabs_info = self.browser.get_tabs_info()
        
        # Format elements for easier reading by LLM
        elements_text = "\n".join([
            f"[{el['id']}] <{el['tag']}> text=\"{el['text']}\" role=\"{el['role']}\" selector=\"{el['selector']}\""
            for el in page_info.get('interactiveElements', [])
        ])

        return {
            "url": page_info.get("url"),
            "title": page_info.get("title"),
            "tabs": tabs_info,
            "interactive_elements": elements_text,
            "summary": page_info.get("summary")
        }
