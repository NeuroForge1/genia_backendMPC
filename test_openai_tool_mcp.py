import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.tools.openai_tool import OpenAITool

async def run_test():
    print("Iniciando prueba de OpenAITool con MCP...")
    openai_tool = OpenAITool()
    
    test_params = {
        "prompt": "Explica brevemente qué es un microservicio.",
        "model": "gpt-3.5-turbo" # Usar un modelo más rápido/barato para prueba
    }
    
    try:
        result = await openai_tool.execute(user_id="test_user", capability="generate_text", params=test_params)
        print("\n--- Resultado de la prueba ---")
        print(result)
        print("---------------------------")
        
        if result.get("status") == "success":
            print("\nPrueba completada exitosamente.")
        else:
            print("\nPrueba completada con errores.")
            
    except Exception as e:
        print(f"\nError durante la ejecución de la prueba: {e}")

if __name__ == "__main__":
    # Ensure the OpenAI MCP server is running on port 8001 before running this test
    print("Asegúrate de que el servidor MCP de OpenAI esté corriendo en localhost:8001")
    asyncio.run(run_test())

