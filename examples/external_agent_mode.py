import asyncio
import os
from operantid import BrowserManager, BrowserToolKit
from dotenv import load_dotenv

load_dotenv()

async def main():
    # 1. Inicializa o Browser e o ToolKit
    # Note que o desenvolvedor tem total controle sobre o ciclo de vida do navegador
    browser = BrowserManager(headless=False)
    toolkit = BrowserToolKit(browser)
    
    await browser.start()
    
    try:
        # 2. O desenvolvedor pode pegar as definições de tools para passar pro seu LLM
        tool_definitions = toolkit.get_tools()
        print(f"DEBUG: {len(tool_definitions)} ferramentas disponíveis para o seu agente.")
        
        # 3. Exemplo de como o desenvolvedor pegaria o contexto (State)
        await browser.navigate("https://news.ycombinator.com")
        context = await toolkit.get_context()
        
        print("\n--- CONTEXTO PARA O SEU AGENTE ---")
        print(f"URL: {context['url']}")
        print(f"Elementos encontrados: {len(context['interactive_elements'].splitlines())}")
        
        # 4. Exemplo de execução manual de uma tool (o que o seu agente faria)
        print("\nSimulando agente escolhendo uma ação...")
        result = await toolkit.execute_tool("click", {"selector": "[data-operant-id='1']"})
        print(f"Resultado da ação: {result}")
        
        await asyncio.sleep(2)
        
    finally:
        await browser.stop()

if __name__ == "__main__":
    asyncio.run(main())
