import os
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from mistralai import Mistral
import google.generativeai as genai
from openai import AsyncOpenAI
from .browser import BrowserManager
from .utils import Logger

class AgentAction(BaseModel):
    type: str = Field(description="Action type: navigate, click, type, scroll, wait, pressEnter, createTab, switchTab, closeTab, completed, talk")
    url: Optional[str] = None
    query: Optional[str] = None
    selector: Optional[str] = None
    text: Optional[str] = None
    direction: Optional[str] = None
    ms: Optional[int] = None
    tab_id: Optional[int] = Field(None, alias="tabId")
    message: Optional[str] = None

class AIResponse(BaseModel):
    status: str
    action: Optional[AgentAction] = None
    reasoning: str
    message: Optional[str] = None

class Agent:
    def __init__(self, api_key: str, model: str = None, provider: str = "openai", base_url: str = None, headless: bool = False, email: Optional[str] = None, password: Optional[str] = None, browser_config: Optional[Dict[str, Any]] = None):
        """
        Initializes the Operant Agent.
        
        Args:
            api_key: The API key for the provider.
            model: Model name (e.g., 'gpt-4o', 'gemini-1.5-pro', 'mistral-large-latest').
            provider: 'openai' (covers OpenRouter, Groq, Ollama, DeepSeek), 'gemini', or 'mistral'.
            base_url: Custom API base URL for OpenAI-compatible providers.
            headless: Whether to run the browser in headless mode.
            email/password: Optional credentials for the agent to use for logins.
            browser_config: Optional dictionary with browser settings (user_agent, viewport, etc.)
        """
        self.api_key = api_key
        self.provider = provider.lower()
        self.base_url = base_url
        
        if self.provider == "mistral":
            self.model = model or "mistral-large-latest"
            self.client = Mistral(api_key=api_key)
        elif self.provider == "gemini":
            self.model = model or "gemini-1.5-flash"
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == "openai":
            self.model = model or "gpt-4o"
            self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            raise ValueError(f"Provider {provider} not supported. Use 'openai', 'gemini', or 'mistral'.")

        self.email = email
        self.password = password
        self.browser = BrowserManager(headless=headless, config=browser_config)
        self.history = []
        self.max_steps = 25
        self.is_running = False

    async def execute(self, command: str, on_step: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.is_running = True
        self.history = []
        Logger.info(f"Iniciando missão: \"{command}\"")
        await self.browser.start()
        
        step_count = 0
        try:
            while self.is_running and step_count < self.max_steps:
                step_count += 1
                Logger.info(f"--- PASSO {step_count} ---")
                
                # 1. Inspect
                page_info = await self.browser.inspect()
                
                # 2. Ask AI
                ai_response = await self._ask_ai(command, page_info)
                Logger.info(f"🤔 Raciocínio: {ai_response.reasoning}")
                
                if on_step:
                    payload = {
                        "step": step_count,
                        "reasoning": ai_response.reasoning,
                        "action": ai_response.action.model_dump() if ai_response.action else None,
                        "message": ai_response.message
                    }
                    if asyncio.iscoroutinefunction(on_step):
                        await on_step(payload)
                    else:
                        on_step(payload)

                # 3. Handle Completion
                if ai_response.status == "completed":
                    self.is_running = False
                    Logger.success(f"Missão concluída: {ai_response.message}")
                    return {"success": True, "message": ai_response.message, "steps": step_count}

                # 4. Execute Action
                if ai_response.action:
                    result = await self._execute_action(ai_response.action)
                    
                    self.history.append({
                        "step": step_count,
                        "action": ai_response.action.model_dump(),
                        "result": result,
                        "reasoning": ai_response.reasoning
                    })
                    
                    # Se a ação pode desencadear navegação, espera um pouco para estabilizar
                    if ai_response.action.type in ["click", "type", "pressEnter"]:
                        await asyncio.sleep(2)
                    
                    if ai_response.action.type == "talk":
                        self.is_running = False
                        Logger.info(f"Agente falou: {ai_response.action.message}")
                        return {"success": True, "message": ai_response.action.message, "steps": step_count}

                await asyncio.sleep(1) # Small delay between steps
                
            if step_count >= self.max_steps:
                Logger.warning("Número máximo de passos atingido.")
            return {"success": False, "error": "Max steps reached", "steps": step_count}
        finally:
            await self.browser.stop()

    async def _ask_ai(self, command: str, page_info: Dict[str, Any]) -> AIResponse:
        history_text = "\n".join([
            f"Passo {h['step']}: {h['action']['type']} ({'✅' if h['result'] else '❌'}) - {h['reasoning']}"
            for h in self.history
        ])

        credentials = f"\n🔐 CREDENCIAIS PARA LOGIN (USE SEMPRE QUE NECESSÁRIO SEM PERGUNTAR):\n- E-mail/Usuário: {self.email or 'Não disponível'}\n- Senha: {self.password or 'Não disponível'}\n"

        prompt = f"""Você é o Operant Agent, um agente de elite com AUTONOMIA TOTAL sobre o navegador. 
Sua missão: "{command}"
{credentials}
🌐 ESTADO ATUAL:
- URL: {page_info.get('url', 'N/A')}
- TÍTULO: {page_info.get('title', 'N/A')}
- ABAS ABERTAS: {self.browser.get_tabs_info()}

🔍 ELEMENTOS INTERATIVOS NA PÁGINA ATIVA:
{self._format_elements(page_info.get('interactiveElements', []))}

📜 HISTÓRICO DE EXECUÇÃO:
{history_text or 'Iniciando agora.'}

Responda APENAS com um JSON conforme o schema:
{{
  "status": "continue" | "completed",
  "action": {{ 
    "type": "navigate" | "click" | "type" | "scroll" | "pressEnter" | "wait" | "reload" | "back" | "forward" | "createTab" | "switchTab" | "closeTab" | "talk", 
    "url": "URL para navigate ou createTab", 
    "selector": "Seletor CSS", 
    "text": "Texto para digitar OU texto do botão para fallback", 
    "direction": "up"|"down",
    "ms": 2000,
    "tabId": 0,
    "message": "Mensagem para o usuário (apenas em 'talk' ou 'completed')"
  }},
  "reasoning": "Sua lógica interna",
  "message": "Mensagem final se concluído"
}}
"""

        if self.provider == "mistral":
            response = await self.client.chat.complete_async(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
        elif self.provider == "gemini":
            response = await self.client.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            content = response.text
        else: # openai compatible
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content

        return AIResponse.model_validate_json(content)

    def _format_elements(self, elements: List[Dict[str, Any]]) -> str:
        return "\n".join([
            f"[{el['id']}] <{el['tag']}> text=\"{el['text']}\" role=\"{el['role']}\" type=\"{el['type']}\" placeholder=\"{el['placeholder']}\" selector=\"{el['selector']}\""
            for el in elements
        ])

    async def _execute_action(self, action: AgentAction) -> bool:
        t = action.type.lower()
        if t == "navigate":
            await self.browser.navigate(action.url)
            return True
        elif t == "click":
            return await self.browser.click(action.selector, action.text)
        elif t == "type":
            return await self.browser.type_text(action.selector, action.text)
        elif t == "scroll":
            await self.browser.scroll(action.direction)
            return True
        elif t == "pressenter":
            await self.browser.press_enter()
            return True
        elif t == "wait":
            await self.browser.wait(action.ms or 2000)
            return True
        elif t == "reload":
            await self.browser.reload()
            return True
        elif t == "back":
            await self.browser.back()
            return True
        elif t == "forward":
            await self.browser.forward()
            return True
        elif t == "createtab":
            await self.browser.create_tab(action.url)
            return True
        elif t == "switchtab":
            return await self.browser.switch_tab(action.tab_id)
        elif t == "closetab":
            return await self.browser.close_tab(action.tab_id)
        return False
