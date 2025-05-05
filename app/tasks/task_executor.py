# /home/ubuntu/genia_backendMPC/app/tasks/task_executor.py

from typing import Dict, Any
import logging

# Importar la clase MCPClient y tipos necesarios
from app.mcp_client.client import MCPClient, SimpleMessage, SimpleTextContent
# Importar la función para enviar mensajes de WhatsApp
from app.tools.whatsapp_tool import send_whatsapp_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskExecutor:
    """Ejecuta la tarea correspondiente basada en el comando interpretado y envía la respuesta."""

    def __init__(self, mcp_client: MCPClient):
        """Inicializa el ejecutor con una instancia del cliente MCP."""
        self.mcp_client = mcp_client
        logger.info("TaskExecutor inicializado con cliente MCP.")

    async def execute_task_and_respond(self, command: str, parameters: Dict[str, Any], sender_number: str):
        """Ejecuta la tarea llamando al servidor MCP apropiado y envía el resultado por WhatsApp."""

        logger.info(f"TaskExecutor: Ejecutando comando: {command} para {sender_number} con parámetros: {parameters}")

        result_text = "Lo siento, no pude ejecutar esa acción."
        mcp_server_name = None
        request_content_text = None
        request_metadata = {}
        execution_successful = False

        try:
            if command == "generate_text":
                mcp_server_name = "openai"
                topic = parameters.get("topic", "algo interesante")
                request_content_text = f"Genera un texto sobre: {topic}"
                request_metadata = {"model": "gpt-3.5-turbo"} # O el modelo preferido

            elif command == "search_keywords":
                mcp_server_name = "openai" # Asumiendo que OpenAI puede hacer esto
                topic = parameters.get("topic", "marketing digital")
                request_content_text = f"Sugiere 5 palabras clave SEO para un artículo sobre: {topic}"
                request_metadata = {"model": "gpt-3.5-turbo"}

            elif command == "send_whatsapp":
                # Este comando es especial, ya que la acción ES enviar un WhatsApp.
                # Podríamos llamar directamente a send_whatsapp_message aquí,
                # o delegar a un MCP de Twilio si queremos más control/logging centralizado.
                # Por simplicidad, llamaremos directamente a la función.
                recipient = parameters.get("recipient_number")
                message = parameters.get("message_text")
                if recipient and message:
                    try:
                        # Asegurarse de que el número del destinatario tenga el prefijo whatsapp:
                        formatted_recipient = recipient if recipient.startswith("whatsapp:") else f"whatsapp:{recipient}"
                        await send_whatsapp_message(formatted_recipient, message)
                        result_text = f"Mensaje enviado a {recipient}."
                        execution_successful = True
                    except Exception as send_err:
                        logger.error(f"TaskExecutor: Error al enviar WhatsApp directamente: {send_err}")
                        result_text = f"Error al intentar enviar mensaje a {recipient}: {send_err}"
                else:
                    result_text = "Faltan parámetros (recipient_number o message_text) para enviar WhatsApp."
                # Como la acción ya se completó (o falló), enviamos el resultado y retornamos.
                formatted_sender = sender_number if sender_number.startswith("whatsapp:") else f"whatsapp:{sender_number}"
                await send_whatsapp_message(formatted_sender, result_text)
                return # Salir temprano para este comando

            # Añadir más comandos aquí (ej. transcribe_audio si se implementa en MCP)

            elif command == "unknown":
                result_text = "Lo siento, no entendí qué acción realizar."
                # No se considera un fallo de ejecución, sino de interpretación previa.
                execution_successful = True # Para que no envíe mensaje de error genérico.

            else:
                result_text = f"Comando 	'{command}' no reconocido."
                execution_successful = True # No es un fallo de ejecución.

            # Si se identificó un servidor MCP y contenido, enviar la solicitud
            if mcp_server_name and request_content_text:
                request_message = SimpleMessage(
                    role="user",
                    content=SimpleTextContent(text=request_content_text),
                    metadata=request_metadata
                )

                response_parts = []
                async for response in self.mcp_client.request_mcp_server(mcp_server_name, request_message):
                    if response.role == "assistant" and response.content.text:
                        response_parts.append(response.content.text)
                    elif response.role == "error":
                        logger.error(f"TaskExecutor: Error recibido del servidor MCP {mcp_server_name}: {response.content.text}")
                        result_text = f"Error al ejecutar {command}: {response.content.text}"
                        execution_successful = False
                        break # Salir si hay error

                if response_parts:
                    result_text = "".join(response_parts)
                    execution_successful = True
                elif execution_successful is not False: # Si no hubo error pero tampoco respuesta
                    result_text = f"No se recibió respuesta del servicio {mcp_server_name} para el comando {command}."
                    execution_successful = False

        except ConnectionError as e:
            logger.error(f"TaskExecutor: Error de conexión al servidor MCP {mcp_server_name}: {e}")
            result_text = f"Error de conexión al intentar ejecutar {command}."
            execution_successful = False
        except Exception as e:
            logger.error(f"TaskExecutor: Error inesperado al ejecutar comando {command}: {e}", exc_info=True)
            result_text = f"Error inesperado al ejecutar {command}."
            execution_successful = False

        # Enviar la respuesta final al usuario original por WhatsApp
        logger.info(f"TaskExecutor: Enviando resultado para comando 	'{command}' a {sender_number}: {result_text[:100]}...")
        formatted_sender = sender_number if sender_number.startswith("whatsapp:") else f"whatsapp:{sender_number}"
        try:
            await send_whatsapp_message(formatted_sender, result_text)
        except Exception as send_err:
             logger.error(f"TaskExecutor: Fallo al enviar respuesta final a {sender_number}: {send_err}")

    # Mantener el método original por si se necesita en otro lugar, pero marcarlo como obsoleto?
    # O eliminarlo si execute_task_and_respond lo reemplaza completamente.
    # Por ahora, lo comentamos para evitar confusión.
    # async def execute_task(self, command_data: Dict[str, Any]) -> str:
    #     ...

