# /home/ubuntu/genia_backendMPC/test_whatsapp_tool_mcp.py
import asyncio
import os
import sys
import uuid

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables (might be needed for other parts of the tool/backend)
from dotenv import load_dotenv
load_dotenv()

# Import the tool
from app.tools.whatsapp_tool import WhatsAppTool

async def run_whatsapp_test():
    """Runs a test for the MCP-integrated WhatsAppTool."""
    print("--- Iniciando Prueba de Integración MCP para WhatsAppTool (send_message) ---")
    print("Asegúrate de que el servidor MCP de Twilio esté corriendo en localhost:8003")

    whatsapp_tool = WhatsAppTool() # Assumes config is loaded via .env
    test_user_id = str(uuid.uuid4()) # Use a pure UUID
    target_number = "+16575272405" # Número proporcionado por el usuario
    message_body = "Hola desde GENIA via MCP! Esta es una prueba de integración."

    # --- Test send_message via MCP ---
    print(f"\n--- Probando WhatsAppTool (send_message) a {target_number} ---")
    try:
        params = {
            "to": target_number,
            "body": message_body
        }
        result = await whatsapp_tool.execute(user_id=test_user_id, capability="send_message", params=params)
        print(f"Resultado send_message: {result}")
        
        if result.get("status") == "success":
            print(f"WhatsAppTool (send_message): OK - Mensaje enviado (SID: {result.get('message_sid')}, Status Twilio: {result.get('twilio_status')})")
        else:
            print(f"WhatsAppTool (send_message): Falló - {result.get('message')}")
            
    except Exception as e:
        print(f"Error en WhatsAppTool (send_message): {e}")

    print("\n--- Prueba de Integración MCP para WhatsAppTool Finalizada ---")

if __name__ == "__main__":
    asyncio.run(run_whatsapp_test())

