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
SCHEDULER_MCP_BASE_URL = os.getenv("SCHEDULER_MCP_BASE_URL", "https://genia-mcp-scheduler.onrender.com") # URL base del Scheduler MCP
SCHEDULER_MCP_API_TOKEN = os.getenv("SCHEDULER_MCP_API_TOKEN", "a8a9079d7db52778f5d533e67bec8d2fc32915ade48c9528b16b1c7f85a1493d") # Token del Scheduler MCP

SERVER_URLS = {
    "openai": OPENAI_MCP_URL,
    "stripe": STRIPE_MCP_URL,
    "twilio": TWILIO_MCP_URL,
    "scheduler": SCHEDULER_MCP_BASE_URL # Añadido para el Scheduler
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
            logger.error(f"URL para el servidor MCP \t'{server_name}'\t no configurada o vacía.")
            raise ValueError(f"URL para el servidor MCP \t'{server_name}'\t no configurada.")

        server_url = SERVER_URLS[server_name]
        # Use model_dump instead of model_dump_json for httpx content
        request_data = request_message.model_dump(mode='json')
        # Restaurado log simple para evitar NameError
        logger.info(f"Cliente Simplificado: Enviando POST a {server_url} con datos: {json.dumps(request_data)[:500]}...") # Log truncado para evitar sobrecarga

        try:
            async with self._http_client.stream("POST", server_url, json=request_data, headers={'Accept': 'text/event-stream'}) as response:
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

    async def schedule_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envía una solicitud para crear una nueva tarea programada al MCP de Programación."""
        scheduler_url = SERVER_URLS.get("scheduler")
        if not scheduler_url:
            logger.error("URL para el MCP de Programación (scheduler) no configurada.")
            raise ValueError("URL para el MCP de Programación no configurada.")
        
        if not SCHEDULER_MCP_API_TOKEN:
            logger.error("Token API para el MCP de Programación no configurado.")
            raise ValueError("Token API para el MCP de Programación no configurado.")

        # El endpoint completo para crear tareas en el Scheduler MCP
        # Asumiendo que la URL base ya incluye el /api/v1 o se construye aquí
        # Basado en nuestro test_mcp_scheduler_onrender.py, la URL base es https://genia-mcp-scheduler.onrender.com
        # y el endpoint es /api/v1/tasks
        target_url = f"{scheduler_url}/api/v1/tasks"

        headers = {
            "Authorization": f"Bearer {SCHEDULER_MCP_API_TOKEN}",
            "Content-Type": "application/json"
        }

        logger.info(f"MCPClient: Enviando POST a {target_url} para programar tarea con datos: {json.dumps(task_data)[:500]}...")

        try:
            response = await self._http_client.post(target_url, json=task_data, headers=headers)
            response.raise_for_status()  # Lanza una excepción para errores HTTP (4xx o 5xx)
            response_data = response.json()
            logger.info(f"MCPClient: Tarea programada exitosamente. Respuesta del Scheduler: {response_data}")
            return response_data
        except httpx.HTTPStatusError as http_err:
            logger.error(f"MCPClient: Error HTTP al programar tarea: {http_err.response.status_code} - {http_err.response.text}", exc_info=True)
            # Re-lanzar con más contexto o devolver un diccionario de error estandarizado
            raise ConnectionError(f"Error HTTP {http_err.response.status_code} al programar tarea: {http_err.response.text}") from http_err
        except httpx.RequestError as req_err:
            logger.error(f"MCPClient: Error de red al programar tarea: {req_err}", exc_info=True)
            raise ConnectionError(f"Error de red al programar tarea: {req_err}") from req_err
        except Exception as e:
            logger.exception(f"MCPClient: Error inesperado al programar tarea: {e}")
            raise

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
async def _test_scheduler_client():
    print("Iniciando prueba del cliente MCP para Scheduler...")
    
    # Datos de ejemplo para una tarea de envío de correo
    # Similar a lo que usamos en test_mcp_scheduler_onrender.py
    import datetime
    import uuid
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    scheduled_time_dt = now_utc + datetime.timedelta(minutes=5)
    scheduled_at_utc_iso = scheduled_time_dt.isoformat()

    email_content_details = {
        "to_recipients": [
            {"email": "test_from_backend@example.com", "name": "Test Backend Recipient"}
        ],
        "subject": "Scheduled Email via BackendMPC -> Scheduler -> EmailMCP",
        "body_html": "<h1>Hello from BackendMPC!</h1><p>This email was scheduled via BackendMPC, processed by SchedulerMCP, and sent by EmailMCP.</p>",
        "from_address": "noreply_backend@genia.systems"
    }
    mcp_email_request_body = {
        "role": "user",
        "content": email_content_details,
        "metadata": {}
    }
    test_task_data = {
        "genia_user_id": str(uuid.uuid4()), 
        "platform_identifier": {
            "platform_name": "email",
            "account_id": "backend_user_for_email_task"
        },
        "scheduled_at_utc": scheduled_at_utc_iso,
        "task_payload": {
            "mcp_target_endpoint": "/mcp/send_email", # Endpoint en el EmailMCP
            "mcp_request_body": mcp_email_request_body, # Payload para el EmailMCP
            "user_platform_tokens": { 
                "service_auth_key": "email_mcp_internal_key_placeholder"
            }
        },
        "task_type": "email_send_via_scheduler_from_backend"
    }

    try:
        print(f"Enviando datos de tarea: {json.dumps(test_task_data, indent=2)}")
        response = await mcp_client_instance.schedule_task(test_task_data)
        print(f"---> Respuesta del Scheduler MCP: {response}")
    except Exception as e:
        print(f"Error en la prueba del cliente Scheduler: {e}")
    finally:
        await mcp_client_instance.close()

# Only run the test if the script is executed directly
if __name__ == "__main__":
    import asyncio
    # print("Ejecutando prueba interna del cliente MCP (OpenAI)...")
    # asyncio.run(_test_client()) # Comentado para no ejecutar la prueba de OpenAI por defecto
    
    print("\nEjecutando prueba interna del cliente MCP para Scheduler...")
    # Asegúrate de que SCHEDULER_MCP_BASE_URL y SCHEDULER_MCP_API_TOKEN estén en tu .env o variables de entorno
    # si el Scheduler MCP no está en localhost o requiere un token diferente al de desarrollo.
    asyncio.run(_test_scheduler_client())
