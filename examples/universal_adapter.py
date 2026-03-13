import asyncio
import os
from operantid import Agent
from dotenv import load_dotenv

load_dotenv()

async def run_with_gemini():
    print("\n--- Testando com Google Gemini ---")
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY não encontrada no seu arquivo .env.")
        return

    agent = Agent(
        api_key=api_key,
        provider="gemini",
        model="gemini-3.1-pro-preview", # Ou gemini-3.1-pro se já estiver disponível para você
        headless=False
    )
    
    print("🚀 Iniciando missão furtiva com Gemini...")
    result = await agent.execute("Entre no duckduckgo.com e pesquise por 'deepseek r1'. Me diga o que o site diz no primeiro resultado.")
    print(f"\n🏁 Resultado: {result.get('message', 'Sem resposta final')}")

async def run_with_openrouter():
    print("\n--- Testando com OpenRouter ---")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY não encontrada.")
        return

    agent = Agent(
        api_key=api_key,
        provider="openai",
        base_url="https://openrouter.ai/api/v1",
        model="openrouter/free",
        headless=False
    )
    
    result = await agent.execute("Vá ao Google e veja o clima em São Paulo.")
    print(f"Resultado: {result['message']}")

if __name__ == "__main__":
    # Agora executando o Gemini por padrão como solicitado
    asyncio.run(run_with_gemini())
