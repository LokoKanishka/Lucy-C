import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def run_parallel_tools():
    url = "http://127.0.0.1:8000/sse"
    print(f"Connecting to {url}...")
    
    try:
        async with sse_client(url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                
                print("Session initialized. Fetching tools...")
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                print(f"Found {len(tool_names)} tools: {', '.join(tool_names[:5])}...")
                
                # Vamos a probar invocar la misma herramienta (ej. ping) 10 veces en paralelo
                if "ping" in tool_names:
                    print("\n--- INICIANDO TEST DE ESTRÉS (10 Pings Paralelos) ---")
                    
                    async def call_ping(i):
                        try:
                            result = await session.call_tool("ping", {"kwargs": "{}"})
                            print(f"[Req {i}] Éxito: {result.content[0].text[:30]}")
                            return True
                        except Exception as e:
                            print(f"[Req {i}] Fallo: {e}")
                            return False

                    tasks = [call_ping(i) for i in range(10)]
                    results = await asyncio.gather(*tasks)
                    
                    exitos = sum(1 for r in results if r)
                    print(f"\nResultado: {exitos}/10 peticiones exitosas.")
                    if exitos == 10:
                        print("✅ TEST SSE SUPERADO: La concurrencia asincrónica funciona perfectamente.")
                    else:
                        print("❌ TEST FALLIDO: Hubo errores bajo carga concurrente.")
                else:
                    print("Herramienta 'ping' no encontrada para el test.")
    except Exception as e:
        print(f"Error crítico conectando al servidor SSE: {e}")

if __name__ == "__main__":
    asyncio.run(run_parallel_tools())
