# /home/ubuntu/genia_backendMPC/test_mcp_integration_full.py
import asyncio
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables before importing tools that might need them
from dotenv import load_dotenv
load_dotenv()

# Import the tools
from app.tools.openai_tool import OpenAITool
from app.tools.funnels_tool import FunnelsTool
from app.tools.seo_analysis_tool import SEOAnalysisTool
from app.tools.whatsapp_analysis_tool import WhatsAppAnalysisTool

async def run_tests():
    """Runs integration tests for all MCP-integrated tools."""
    print("--- Iniciando Pruebas de Integración MCP Completas ---")
    print("Asegúrate de que el servidor MCP de OpenAI esté corriendo en localhost:8001")

    # --- Test OpenAITool --- 
    print("\n--- Probando OpenAITool ---")
    try:
        openai_tool = OpenAITool() # Assumes config is loaded via .env
        params_openai = {
            "prompt": "Explica qué es la computación cuántica en una frase.",
            "model": "gpt-3.5-turbo",
            "max_tokens": 50,
            "temperature": 0.5
        }
        result_openai = await openai_tool.execute(user_id="test_user", capability="generate_text", params=params_openai)
        print(f"Resultado OpenAITool: {result_openai}")
        assert result_openai.get("status") == "success"
        assert isinstance(result_openai.get("text"), str) and len(result_openai.get("text")) > 0
        print("OpenAITool: OK")
    except Exception as e:
        print(f"Error en OpenAITool: {e}")

    # --- Test FunnelsTool --- 
    print("\n--- Probando FunnelsTool (create_sales_funnel) ---")
    try:
        funnels_tool = FunnelsTool()
        params_funnel = {
            "product_name": "Curso de Marketing Digital",
            "target_audience": "Pequeños empresarios",
            "funnel_stages": 2 # Keep it short for testing
        }
        result_funnel = await funnels_tool.execute(user_id="test_user", capability="create_sales_funnel", params=params_funnel)
        print(f"Resultado FunnelsTool (create_sales_funnel): {result_funnel['status']}") # Print only status for brevity
        # print(f"Resultado FunnelsTool (create_sales_funnel): {result_funnel}") # Full result if needed
        assert result_funnel.get("status") == "success"
        assert isinstance(result_funnel.get("funnel_content"), str) and len(result_funnel.get("funnel_content")) > 0
        print("FunnelsTool: OK")
    except Exception as e:
        print(f"Error en FunnelsTool: {e}")

    # --- Test SEOAnalysisTool --- 
    print("\n--- Probando SEOAnalysisTool (keyword_research) ---")
    try:
        seo_tool = SEOAnalysisTool()
        params_seo = {
            "topic": "Inteligencia Artificial",
            "locale": "es-ES",
            "max_results": 3
        }
        result_seo = await seo_tool.execute(user_id="test_user", capability="keyword_research", params=params_seo)
        print(f"Resultado SEOAnalysisTool (keyword_research): {result_seo['status']}") # Print only status for brevity
        # print(f"Resultado SEOAnalysisTool (keyword_research): {result_seo}") # Full result if needed
        assert result_seo.get("status") == "success"
        assert isinstance(result_seo.get("keyword_data"), dict)
        assert len(result_seo.get("keyword_data", {}).get("main_keywords", [])) > 0
        print("SEOAnalysisTool: OK")
    except Exception as e:
        print(f"Error en SEOAnalysisTool: {e}")

    # --- Test WhatsAppAnalysisTool --- 
    print("\n--- Probando WhatsAppAnalysisTool (analyze_sentiment) ---")
    try:
        whatsapp_tool = WhatsAppAnalysisTool()
        params_whatsapp = {
            "chat_id": "simulated_chat_123",
            "time_period": "week"
        }
        # Note: _get_chat_history is simulated and doesn't require real user_id check for this test
        result_whatsapp = await whatsapp_tool.execute(user_id="test_user_no_twilio_needed_for_sim", capability="analyze_sentiment", params=params_whatsapp)
        print(f"Resultado WhatsAppAnalysisTool (analyze_sentiment): {result_whatsapp['status']}") # Print only status for brevity
        # print(f"Resultado WhatsAppAnalysisTool (analyze_sentiment): {result_whatsapp}") # Full result if needed
        assert result_whatsapp.get("status") == "success"
        assert result_whatsapp.get("sentiment") in ["POSITIVO", "NEGATIVO", "NEUTRAL"]
        assert isinstance(result_whatsapp.get("satisfaction_score"), int)
        print("WhatsAppAnalysisTool: OK")
    except Exception as e:
        print(f"Error en WhatsAppAnalysisTool: {e}")

    print("\n--- Pruebas de Integración MCP Completas Finalizadas ---")

if __name__ == "__main__":
    asyncio.run(run_tests())

