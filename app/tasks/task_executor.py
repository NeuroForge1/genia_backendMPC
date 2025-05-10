# /home/ubuntu/genia_backendMPC/app/tasks/task_executor.py

from typing import Dict, Any
import logging

# Importar la clase MCPClient y tipos necesarios
from app.mcp_client.client import MCPClient, SimpleMessage, SimpleTextContent
# Importar la función para enviar mensajes de WhatsApp
from app.tools.whatsapp_tool import send_whatsapp_message
# Importar la herramienta de correo electrónico (anteriormente GmailTool)
from app.tools.gmail_tool import GmailTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskExecutor:
    """Ejecuta la tarea correspondiente basada en el comando interpretado y envía la respuesta."""

    def __init__(self, mcp_client: MCPClient):
        """Inicializa el ejecutor con una instancia del cliente MCP."""
        self.mcp_client = mcp_client
        # Instanciar la herramienta de correo aquí para reutilizarla
        self.email_tool = GmailTool()
        logger.info("TaskExecutor inicializado con cliente MCP y EmailTool.")

    async def execute_task_and_respond(self, interpreted_data: Dict[str, Any], sender_number: str):
        """Ejecuta la tarea principal, maneja una posible acción secundaria de envío de correo,
           y envía el resultado principal por WhatsApp."""

        main_command = interpreted_data.get("main_command", "unknown")
        main_parameters = interpreted_data.get("main_parameters", {})
        secondary_action = interpreted_data.get("secondary_action")
        secondary_parameters = interpreted_data.get("secondary_parameters", {})

        logger.info(f"TaskExecutor: Ejecutando main_command: {main_command} para {sender_number} con main_parameters: {main_parameters}")
        if secondary_action:
            logger.info(f"TaskExecutor: Acción secundaria detectada: {secondary_action} con parámetros: {secondary_parameters}")

        result_text = "Lo siento, no pude ejecutar esa acción."
        mcp_server_name = None
        request_content_text = None
        request_metadata = {}
        execution_successful = False

        try:
            if main_command == "generate_text":
                mcp_server_name = "openai"
                topic = main_parameters.get("topic", "algo interesante")
                request_content_text = f"Genera un texto sobre: {topic}"
                request_metadata = {"model": interpreted_data.get("metadata", {}).get("model", "gpt-4o")}

            elif main_command == "search_keywords":
                mcp_server_name = "openai"
                topic = main_parameters.get("topic", "marketing digital")
                request_content_text = f"Sugiere 5 palabras clave SEO para un artículo sobre: {topic}"
                request_metadata = {"model": interpreted_data.get("metadata", {}).get("model", "gpt-4o")}

            elif main_command == "send_whatsapp":
                recipient = main_parameters.get("recipient_number")
                message = main_parameters.get("message_text")
                if recipient and message:
                    try:
                        formatted_recipient = recipient if recipient.startswith("whatsapp:") else f"whatsapp:{recipient}"
                        await send_whatsapp_message(formatted_recipient, message)
                        result_text = f"Mensaje enviado a {recipient}."
                        execution_successful = True
                    except Exception as send_err:
                        logger.error(f"TaskExecutor: Error al enviar WhatsApp directamente: {send_err}")
                        result_text = f"Error al intentar enviar mensaje a {recipient}: {send_err}"
                else:
                    result_text = "Faltan parámetros (recipient_number o message_text) para enviar WhatsApp."
                formatted_sender = sender_number if sender_number.startswith("whatsapp:") else f"whatsapp:{sender_number}"
                await send_whatsapp_message(formatted_sender, result_text)
                return

            elif main_command == "unknown":
                result_text = "Lo siento, no entendí qué acción realizar."
                execution_successful = True

            else:
                result_text = f"Comando 	Ó{main_command}	 no reconocido."
                execution_successful = True

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
                        result_text = f"Error al ejecutar {main_command}: {response.content.text}"
                        execution_successful = False
                        break
                if response_parts:
                    result_text = "".join(response_parts)
                    execution_successful = True
                elif not execution_successful:
                    result_text = f"No se recibió respuesta del servicio {mcp_server_name} para el comando {main_command}."
                    execution_successful = False

        except ConnectionError as e:
            logger.error(f"TaskExecutor: Error de conexión al servidor MCP {mcp_server_name}: {e}")
            result_text = f"Error de conexión al intentar ejecutar {main_command}."
            execution_successful = False
        except Exception as e:
            logger.error(f"TaskExecutor: Error inesperado al ejecutar comando {main_command}: {e}", exc_info=True)
            result_text = f"Error inesperado al ejecutar {main_command}."
            execution_successful = False

        logger.info(f"TaskExecutor: Enviando resultado para comando 	Ó{main_command}	 a {sender_number}: {result_text[:100]}...")
        formatted_sender = sender_number if sender_number.startswith("whatsapp:") else f"whatsapp:{sender_number}"
        try:
            await send_whatsapp_message(formatted_sender, result_text)
        except Exception as send_err:
            logger.error(f"TaskExecutor: Fallo al enviar respuesta principal a {sender_number}: {send_err}")

        if execution_successful and secondary_action == "send_email":
            to_address = secondary_parameters.get("to_address")
            email_subject = secondary_parameters.get("subject", f"Resultado de tu solicitud: {main_command}")
            
            if to_address and result_text:
                logger.info(f"TaskExecutor: Intentando acción secundaria: enviar correo a {to_address}")
                email_params = {
                    "to_address": to_address,
                    "subject": email_subject,
                    "body_text": result_text
                }
                try:
                    email_response = await self.email_tool.execute(user_id=sender_number, capability="send_email", params=email_params)
                    if email_response.get("status") == "success":
                        logger.info(f"TaskExecutor: Correo enviado exitosamente a {to_address}. Respuesta: {email_response}")
                        await send_whatsapp_message(formatted_sender, f"Además, el resultado ha sido enviado a {to_address}.")
                    else:
                        logger.error(f"TaskExecutor: Fallo al enviar correo a {to_address}. Error: {email_response.get("message")}")
                        await send_whatsapp_message(formatted_sender, f"No pude enviar el resultado a {to_address} debido a un error.")
                except Exception as email_err:
                    logger.exception(f"TaskExecutor: Excepción al intentar enviar correo a {to_address}: {email_err}")
                    await send_whatsapp_message(formatted_sender, f"Ocurrió un error inesperado al intentar enviar el resultado a {to_address}.")
            else:
                logger.warning(f"TaskExecutor: No se pudo enviar correo. Falta destinatario (	Ó{to_address}	) o cuerpo (	Ó{result_text}	).")
                if to_address:
                    await send_whatsapp_message(formatted_sender, f"No pude generar el contenido para enviar a {to_address}.")

