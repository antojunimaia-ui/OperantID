import asyncio
import time
import os
from dotenv import load_dotenv
from operantid import Agent

load_dotenv()

TASKS = [
    {
        "name": "Navigation & Fact Check",
        "command": "Vá ao site 'en.wikipedia.org/wiki/Artificial_intelligence' e encontre quem é citado como o 'pai da Inteligência Artificial'."
    },
    {
        "name": "Direct Info Extraction",
        "command": "Vá ao site 'quotes.toscrape.com' e me diga quem é o autor da primeira citação da página."
    },
    {
        "name": "Search & Navigate",
        "command": "Pesquise por 'preço da soja hoje' no Google e me dê o valor atual do primeiro resultado de notícia ou mercado que aparecer."
    }
]

MODELS = ["gemini-2.0-flash", "gemini-2.5-flash"]

async def run_benchmark():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Erro: GOOGLE_API_KEY não encontrada no .env")
        return

    all_results = {}

    for model_name in MODELS:
        print(f"\n{'='*50}")
        print(f"BENCHMARKING MODEL: {model_name}")
        print(f"{'='*50}\n")
        
        agent = Agent(
            api_key=api_key,
            provider="gemini",
            model=model_name,
            headless=True
        )
        agent.max_steps = 15 # Reduzindo para ser mais rápido e focado
        
        model_results = []
        for task in TASKS:
            print(f"Running Task: {task['name']}...")
            start_time = time.time()
            try:
                res = await agent.execute(task["command"])
                duration = time.time() - start_time
                success = res.get("success", False)
                steps = res.get("steps", 0)
                
                model_results.append({
                    "task": task["name"],
                    "success": success,
                    "steps": steps,
                    "time": duration
                })
                print(f"  {'✅' if success else '❌'} | {steps} steps | {duration:.2f}s")
            except Exception as e:
                print(f"  Error: {e}")
            await asyncio.sleep(2) # Cooldown
            
        all_results[model_name] = model_results

    print("\n" + "="*80)
    print("FINAL COMPARISON TABLE (FOR README)")
    print("="*80)
    header = "| Task | " + " | ".join([f"**{m}**" for m in MODELS]) + " |"
    separator = "| :--- | " + " | ".join([":---:" for _ in MODELS]) + " |"
    print(header)
    print(separator)
    
    for i, task in enumerate(TASKS):
        row = f"| {task['name']} | "
        for m in MODELS:
            res = all_results[m][i]
            status = "✅" if res["success"] else "❌"
            row += f"{status} {res['time']:.1f}s ({res['steps']} step) | "
        print(row)

if __name__ == "__main__":
    asyncio.run(run_benchmark())
