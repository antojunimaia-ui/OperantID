import asyncio
import os
from operantid import Agent
from dotenv import load_dotenv

load_dotenv()

async def main():
    # Make sure to set MISTRAL_API_KEY in your .env file
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("Please set MISTRAL_API_KEY environment variable.")
        return

    agent = Agent(api_key=api_key, headless=False)
    
    def on_step(data):
        print(f"--- Passo {data['step']} ---")
        print(f"Raciocínio: {data['reasoning']}")
        if data['action']:
            print(f"Ação: {data['action']['type']} {data['action'].get('url') or data['action'].get('selector') or ''}")

    result = await agent.execute(
        "Vá para o Google, pesquise por 'operantid python library' e veja os resultados.",
        on_step=on_step
    )
    
    print("\\nResultado Final:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
