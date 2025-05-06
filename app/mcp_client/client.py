# /home/ubuntu/genia_backendMPC/app/mcp_client/client.py

import os
import asyncio
import json
import httpx
import logging
from typing import Dict, Any, AsyncGenerator, Optional
from pydantic import BaseModel # Usaremos Pydantic si está disponible en el backend
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env file for local development
load_dotenv()

# --- Pydantic Models (deben coincidir con el servidor simplificado) ---
# Replicamos aquí para claridad, idealmente estarían en un módulo compartido
class SimpleTextContent(BaseModel):
    text: str

class SimpleMessage(BaseModel):
    role: str
    content: SimpleTextContent
    metadata: Optional[Dict[str, Any]] = None

# --- Configuración --- 
# Leer URLs de servidores desde variables de entorno
# Usar URLs de localhost como fallback para desarrollo local si no están definidas
OPENAI_MCP_URL = os.getenv("OPENAI_MCP_URL", "http://localhost:8001/mcp")
STRIPE_MCP_URL = os.getenv("STRIPE_MCP_URL", "http://localhost:8002/mcp") # Mantener por si se usa
TWILIO_MCP_URL = os.getenv("TWILIO_MCP_URL", "http://localhost:8003/mcp")

SERVER_URLS = {
    "openai": OPENAI_MCP_URL,
    "stripe": STRIPE_MCP_URL,
    "twilio": TWILIO_MCP_URL
}

logger.info(f"MCP Server URLs configured: {SERVER_URLS}")

# --- Cliente MCP Simplificado ---
class MCPClient:
    def __init__(self, timeout: float = 30.0): # Increased timeout slightly
        self._timeout = httpx.Timeout(timeout, connect=timeout*2) # Timeout para conexión y lectura
        self._http_client = httpx.AsyncClient(timeout=self._timeout)

    async def request_mcp_server(self, server_name: str, request_message: SimpleMessage) -> AsyncGenerator[SimpleMessage, None]:
        """Envía una solicitud a un servidor MCP simplificado vía POST y devuelve un generador asíncrono de mensajes SSE."""
        if server_name not in SERVER_URLS or not SERVER_URLS[server_name]:
            logger.error(f"URL para el servidor MCP 	'{server_name}'	 no configurada o vacía.")
            raise ValueError(f"URL para el servidor MCP 	'{server_name}'	 no configurada.")

        server_url = SERVER_URLS[server_name]
        # Use model_dump instead of model_dump_json for httpx content        request_data = request_message.model_dump(mode=\'json\') 

        # Log detallado del base64 antes de enviar
        if server_name == "openai" and request_data.get("metadata", {}).get("parameters", {}).get("audio_content_base64"):
            b64_content = request_data["metadata"]["parameters"]["audio_content_base64"]
            b64_len = len(b64_content)
            logger.info(f"Cliente Simplificado (DEBUG): Enviando base64 a OpenAI. Longitud: {b64_len}. Inicio: {b64_content[:100]}... Fin: ...{b64_content[-100:]}")
        else:
             logger.info(f"Cliente Simplificado: Enviando POST a {server_url} con datos (sin audio base64 detallado): {json.dumps(request_data)[:500]}...") # Log truncado para otros casos

        # logger.info(f"Cliente Simplificado: Enviando POST a {server_url} con datos: {json.dumps(request_data)}") # Reemplazado por log detallado/truncado

        try:            async with self._http_client.stream("POST", server_url, json=request_data, headers={'Accept': 'text/event-stream'}) as response:
                
                # Verificar si la conexión SSE fue exitosa
                if response.status_code != 200:
                     error_content = await response.aread()
                     logger.error(f"Error al conectar con el servidor SSE {server_name}: {response.status_code} - {error_content.decode()}")
                     raise ConnectionError(f"Error {response.status_code} al conectar con {server_name}: {error_content.decode()}")

                logger.info(f"Cliente Simplificado: Conexión SSE establecida con {server_name}.")
                
                current_event = None # Initialize current_event
                # Procesar el stream SSE
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        current_event = None # Reset event on empty line
                        continue
                        
                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        data_str = line.split(":", 1)[1].strip()
                        # Assume event is 'message' or 'error' if not explicitly set (simple server might omit event line)
                        if current_event is None:
                            try:
                                temp_data = json.loads(data_str)
                                if temp_data.get('role') == 'error':
                                    current_event = 'error'
                                else:
                                    current_event = 'message'
                            except: # If parsing fails, assume it's not a standard message
                                pass 
                                
                        if current_event == "message" or current_event == "error":
                            try:
                                message_data = json.loads(data_str)
                                # Validate with Pydantic model before yielding
                                response_msg = SimpleMessage(**message_data)
                                logger.info(f"Cliente Simplificado: Recibido {current_event} de {server_name}: {response_msg.model_dump_json()}")
                                yield response_msg
                            except (json.JSONDecodeError, Exception) as parse_error:
                                logger.error(f"Cliente Simplificado: Error al parsear mensaje {current_event} de {server_name}: {parse_error} - Data: {data_str}")
                        elif current_event == "end":
                             logger.info(f"Cliente Simplificado: Recibido evento 'end' de {server_name}.")
                             # End event might contain data or just signal completion
                             # break # Don't break here, process potential data first
                        # Reset event only after processing data or on empty line
                        # current_event = None 
                    # else: ignore other lines for now

        except httpx.RequestError as req_err:
            logger.error(f"Cliente Simplificado: Error de red al conectar con {server_name}: {req_err}", exc_info=True)
            raise ConnectionError(f"Error de red al conectar con {server_name}: {req_err}") from req_err
        except Exception as e:
            logger.exception(f"Cliente Simplificado: Error inesperado durante comunicación con {server_name}: {e}")
            raise
        finally:
             logger.info(f"Cliente Simplificado: Finalizada comunicación SSE con {server_name}.")

    async def close(self):
        """Cierra el cliente HTTPX."""
        if hasattr(self, '_http_client') and not self._http_client.is_closed:
             await self._http_client.aclose()
             logger.info("Cliente MCP Simplificado cerrado.")
        else:
             logger.info("Cliente MCP Simplificado ya estaba cerrado o no inicializado.")

# Instancia global (o gestionada por dependencias FastAPI)
mcp_client_instance = MCPClient()

# --- Ejemplo de uso (para pruebas internas si es necesario) ---
async def _test_client():
    print("Iniciando prueba del cliente MCP simplificado...")
    test_message = SimpleMessage(
        role="user",
        content=SimpleTextContent(text="Explica qué es el Protocolo MCP en 3 frases."),
        metadata={"model": "gpt-3.5-turbo"}
    )
    # Use the global instance for testing if run directly
    try:
        async for response in mcp_client_instance.request_mcp_server("openai", test_message):
            print(f"---> Respuesta recibida en test: {response.content.text}")
    except Exception as e:
        print(f"Error en la prueba del cliente: {e}")
    finally:
        await mcp_client_instance.close() # Close the global instance after test

# Only run the test if the script is executed directly
if __name__ == "__main__":
    import asyncio
    print("Ejecutando prueba interna del cliente MCP...")
    # Note: This test will use the URLs defined above (env vars or localhost)
    asyncio.run(_test_client())

