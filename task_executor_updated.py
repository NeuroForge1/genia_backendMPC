# /home/ubuntu/genia_backendMPC/app/tasks/task_executor.py

from typing import Dict, Any
import logging
import datetime # Added for scheduling
import uuid # Added for genia_user_id

# Importar la clase MCPClient y tipos necesarios
from app.mcp_client.client import MCPClient, SimpleMessage, SimpleTextContent
# Importar la función para enviar mensajes de WhatsApp
from app.tools.whatsapp_tool import send_whatsapp_message
# Importar la herramienta de correo electrónico (anteriormente GmailTool) - No la usaremos directamente para enviar, pero la dejamos por si hay otros usos.
from app.tools.gmail_tool import GmailTool 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskExecutor:
    """Ejecuta la tarea correspondiente basada en el comando interpretado y envía la respuesta."""

    def __init__(self, mcp_client: MCPClient):
        """Inicializa el ejecutor con una instancia del cliente MCP."""
        self.mcp_client = mcp_client
        # Instanciar la herramienta de correo aquí para reutilizarla si fuera necesario para otras cosas, 
        # pero el envío principal ahora pasará por el scheduler.
        self.email_tool = GmailTool()
        logger.info("TaskExecutor inicializado con cliente MCP y EmailTool.")

    async def execute_task_and_respond(self, interpreted_data: Dict[str, Any], sender_number: str):
        """Ejecuta la tarea principal, maneja una posible acción secundaria de envío de correo (ahora vía scheduler),
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
                result_text = f"Comando '{main_command}' no reconocido."
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

        logger.info(f"TaskExecutor: Enviando resultado para comando '{main_command}' a {sender_number}: {result_text[:100]}...")
        formatted_sender = sender_number if sender_number.startswith("whatsapp:") else f"whatsapp:{sender_number}"
        try:
            await send_whatsapp_message(formatted_sender, result_text)
        except Exception as send_err:
            logger.error(f"TaskExecutor: Fallo al enviar respuesta principal a {sender_number}: {send_err}")

        # --- MODIFIED SECTION: Handling secondary_action "send_email" via Scheduler ---
        if execution_successful and secondary_action == "send_email":
            to_address = secondary_parameters.get("to_address")
            # Usar el result_text (contenido generado) como cuerpo del correo.
            # El subject puede venir de secondary_parameters o ser genérico.
            email_subject = secondary_parameters.get("subject", f"Resultado de tu solicitud: {main_command}")
            
            if to_address and result_text:
                logger.info(f"TaskExecutor: Acción secundaria 'send_email' detectada. Preparando para programar envío a {to_address}")
                
                try:
                    now_utc = datetime.datetime.now(datetime.timezone.utc)
                    # Programar para 2 minutos en el futuro (ajustable)
                    scheduled_time_dt = now_utc + datetime.timedelta(minutes=2) 
                    scheduled_at_utc_iso = scheduled_time_dt.isoformat()

                    # El cuerpo del correo será el result_text (contenido generado por el comando principal)
                    # Convertir saltos de línea a <br> para HTML si es necesario, o enviar como texto plano.
                    # CORREGIDO: Realizar el reemplazo fuera del f-string
                    formatted_email_body_content = result_text.replace('\n', '<br>')
                    email_html_body = f"<h1>{email_subject}</h1><p>{formatted_email_body_content}</p><p><br>---<br>Este correo fue generado y programado por GENIA a través de una solicitud de WhatsApp.</p>"

                    # MEJORA: Añadir headers adicionales para mejorar la entregabilidad
                    email_headers = {
                        "X-Priority": "1",
                        "X-MSMail-Priority": "High",
                        "Importance": "High"
                    }

                    email_content_details = {
                        "to_recipients": [
                            {"email": str(to_address), "name": str(to_address)} # Usar to_address como nombre si no hay otro
                        ],
                        "subject": email_subject,
                        "body_html": email_html_body,
                        "from_address": "noreply_whatsapp@genia.systems", # Dirección de remitente genérica
                        "from_name": "GENIA Systems", # MEJORA: Añadir nombre de remitente reconocible
                        "headers": email_headers # MEJORA: Incluir los headers adicionales
                    }
                    mcp_email_request_body = {
                        "role": "user", # O el rol que espere tu MCP de Email
                        "content": email_content_details,
                        "metadata": {"source": "genia_backendMPC_whatsapp_flow"}
                    }
                    
                    task_data_to_schedule = {
                        "genia_user_id": str(uuid.uuid4()), # O podrías usar sender_number si es un identificador único de usuario
                        "platform_identifier": {
                            "platform_name": "email",
                            "account_id": "whatsapp_triggered_email_task" # Identificador de la cuenta/tipo de tarea
                        },
                        "scheduled_at_utc": scheduled_at_utc_iso,
                        "task_payload": {
                            "mcp_target_endpoint": "/mcp/send_email", # Endpoint del MCP de Email
                            "mcp_request_body": mcp_email_request_body,
                            "user_platform_tokens": { "service_auth_key": "email_mcp_internal_key_placeholder"} # Placeholder
                        },
                        "task_type": "whatsapp_generated_content_email_delivery"
                    }

                    logger.info(f"TaskExecutor: Programando tarea de email con payload: {task_data_to_schedule}")
                    scheduler_response = await self.mcp_client.schedule_task(task_data_to_schedule)
                    
                    if scheduler_response.get("success"):
                        logger.info(f"TaskExecutor: Tarea de envío de correo a {to_address} programada exitosamente. Respuesta del Scheduler: {scheduler_response}")
                        await send_whatsapp_message(formatted_sender, f"Además, el resultado ha sido programado para enviarse a {to_address}.")
                    else:
                        logger.error(f"TaskExecutor: Fallo al programar tarea de envío de correo a {to_address}. Respuesta del Scheduler: {scheduler_response}")
                        await send_whatsapp_message(formatted_sender, f"No pude programar el envío del resultado a {to_address} debido a un error con el programador.")
                
                except ConnectionError as ce:
                    logger.error(f"TaskExecutor: Error de conexión con MCP de Programación al intentar programar email: {ce}")
                    await send_whatsapp_message(formatted_sender, f"Error de comunicación al intentar programar el envío a {to_address}.")
                except ValueError as ve: # Por si falla la configuración del Scheduler en MCPClient
                    logger.error(f"TaskExecutor: Error de configuración interna para el MCP de Programación: {ve}")
                    await send_whatsapp_message(formatted_sender, f"Error de configuración interna al intentar programar el envío a {to_address}.")
                except Exception as e_scheduler:
                    logger.exception(f"TaskExecutor: Excepción inesperada al intentar programar correo a {to_address}: {e_scheduler}")
                    await send_whatsapp_message(formatted_sender, f"Ocurrió un error inesperado al intentar programar el envío del resultado a {to_address}.")
            else:
                logger.warning(f"TaskExecutor: No se pudo programar correo. Falta destinatario ('{to_address}') o cuerpo ('{result_text}').")
                if to_address:
                    await send_whatsapp_message(formatted_sender, f"No pude generar el contenido para programar el envío a {to_address}.")
        # --- END OF MODIFIED SECTION ---
