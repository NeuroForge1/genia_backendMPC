# /home/ubuntu/genia_backendMPC/app/mcp_client/client.py

import asyncio
import json
import httpx
from typing import Dict, Any, AsyncGenerator, Optional
from pydantic import BaseModel # Usaremos Pydantic si está disponible en el backend

# --- Pydantic Models (deben coincidir con el servidor simplificado) ---
# Replicamos aquí para claridad, idealmente estarían en un módulo compartido
class SimpleTextContent(BaseModel):
    text: str

class SimpleMessage(BaseModel):
    role: str
    content: SimpleTextContent
    metadata: Optional[Dict[str, Any]] = None

# --- Configuración ---
# TODO: Cargar URLs de servidores desde configuración (variables de entorno)
SERVER_URLS = {
    "openai": "http://localhost:8001/mcp", # URL del servidor MCP simplificado para OpenAI
    "stripe": "http://localhost:8002/mcp", # URL del servidor MCP simplificado para Stripe
    # Añadir URLs para otros servidores MCP (Twilio, etc.)
}

# --- Cliente MCP Simplificado ---
class GeniaMCPClient:
    def __init__(self, timeout: float = 30.0): # Increased timeout slightly
        self._timeout = httpx.Timeout(timeout, connect=timeout*2) # Timeout para conexión y lectura
        self._http_client = httpx.AsyncClient(timeout=self._timeout)

    async def request_mcp_server(self, server_name: str, request_message: SimpleMessage) -> AsyncGenerator[SimpleMessage, None]:
        """Envía una solicitud a un servidor MCP simplificado vía POST y devuelve un generador asíncrono de mensajes SSE."""
        if server_name not in SERVER_URLS:
            raise ValueError(f"URL para el servidor MCP 	'{server_name}'	 no configurada.")

        server_url = SERVER_URLS[server_name]
        # Use model_dump instead of model_dump_json for httpx content
        request_data = request_message.model_dump(mode='json') 

        print(f"Cliente Simplificado: Enviando POST a {server_url} con datos: {json.dumps(request_data)}")

        try:
            async with self._http_client.stream("POST", server_url, json=request_data, headers={'Accept': 'text/event-stream'}) as response:
                
                # Verificar si la conexión SSE fue exitosa
                if response.status_code != 200:
                     error_content = await response.aread()
                     print(f"Error al conectar con el servidor SSE {server_name}: {response.status_code} - {error_content.decode()}")
                     raise ConnectionError(f"Error {response.status_code} al conectar con {server_name}: {error_content.decode()}")

                print(f"Cliente Simplificado: Conexión SSE establecida con {server_name}.")
                
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
                                print(f"Cliente Simplificado: Recibido {current_event} de {server_name}: {response_msg.model_dump_json()}")
                                yield response_msg
                            except (json.JSONDecodeError, Exception) as parse_error:
                                print(f"Cliente Simplificado: Error al parsear mensaje {current_event} de {server_name}: {parse_error} - Data: {data_str}")
                        elif current_event == "end":
                             print(f"Cliente Simplificado: Recibido evento 'end' de {server_name}.")
                             # End event might contain data or just signal completion
                             # break # Don't break here, process potential data first
                        # Reset event only after processing data or on empty line
                        # current_event = None 
                    # else: ignore other lines for now

        except httpx.RequestError as req_err:
            print(f"Cliente Simplificado: Error de red al conectar con {server_name}: {req_err}")
            raise ConnectionError(f"Error de red al conectar con {server_name}: {req_err}") from req_err
        except Exception as e:
            print(f"Cliente Simplificado: Error inesperado durante comunicación con {server_name}: {e}")
            raise
        finally:
             print(f"Cliente Simplificado: Finalizada comunicación SSE con {server_name}.")

    async def close(self):
        """Cierra el cliente HTTPX."""
        if not self._http_client.is_closed:
             await self._http_client.aclose()
             print("Cliente MCP Simplificado cerrado.")
        else:
             print("Cliente MCP Simplificado ya estaba cerrado.")

# Instancia global (o gestionada por dependencias FastAPI)
mcp_client_instance = GeniaMCPClient()

# --- Ejemplo de uso (para pruebas internas si es necesario) ---
async def _test_client():
    print("Iniciando prueba del cliente MCP simplificado...")
    test_message = SimpleMessage(
        role="user",
        content=SimpleTextContent(text="Explica qué es el Protocolo MCP en 3 frases."),
        metadata={"model": "gpt-3.5-turbo"}
    )
    temp_client = GeniaMCPClient() # Use a temporary client for the test
    try:
        async for response in temp_client.request_mcp_server("openai", test_message):
            print(f"---> Respuesta recibida en test: {response.content.text}")
    except Exception as e:
        print(f"Error en la prueba del cliente: {e}")
    finally:
        await temp_client.close() # Close the temporary client

# Only run the test if the script is executed directly
if __name__ == "__main__":
    import asyncio
    print("Ejecutando prueba interna del cliente MCP...")
    asyncio.run(_test_client())

