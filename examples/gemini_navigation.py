import asyncio
import os
from operantid import Agent
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Certifique-se de configurar GOOGLE_API_KEY no seu arquivo .env
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Por favor, configure a variável de ambiente GOOGLE_API_KEY.")
        return

    # Usando o provider 'gemini' (padrão agora) e o modelo flash
    agent = Agent(api_key=api_key, provider="gemini", model="gemini-1.5-flash", headless=False)
    
    def on_step(data):
        print(f"\n--- Passo {data['step']} ---")
        print(f"Raciocínio: {data['reasoning']}")
        if data['action']:
            action = data['action']
            desc = f"{action['type']}"
            if action.get('url'): desc += f" -> {action['url']}"
            if action.get('selector'): desc += f" em {action['selector']}"
            if action.get('text'): desc += f" (texto: {action['text']})"
            print(f"Ação: {desc}")

    print("🚀 Iniciando Agente Operant com Gemini...")
    result = await agent.execute(
        "Entre no Google, pesquise por 'deepseek r1' e me diga qual o primeiro resultado orgânico.",
        on_step=on_step
    )
    
    print("\n🏁 Resultado Final:")
    print(result.get('message', 'Sem mensagem final.'))
    print(f"Total de passos: {result.get('steps')}")

if __name__ == "__main__":
    asyncio.run(main())
