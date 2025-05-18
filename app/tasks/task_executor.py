# /home/ubuntu/genia_backendMPC/app/tasks/task_executor.py

from typing import Dict, Any
import logging
import datetime
import uuid
import requests
import json
import os
from dotenv import load_dotenv

# Importar la clase MCPClient y tipos necesarios
from app.mcp_client.client import MCPClient, SimpleMessage, SimpleTextContent
# Importar la función para enviar mensajes de WhatsApp
from app.tools.whatsapp_tool import send_whatsapp_message
# Importar la herramienta de correo electrónico
from app.tools.gmail_tool import GmailTool 

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()
EMAIL_MCP_URL = os.getenv("EMAIL_MCP_URL", "https://genia-mcp-server-email.onrender.com")

class TaskExecutor:
    """Ejecuta la tarea correspondiente basada en el comando interpretado y envía la respuesta."""

    def __init__(self, mcp_client: MCPClient):
        """Inicializa el ejecutor con una instancia del cliente MCP."""
        self.mcp_client = mcp_client
        self.email_tool = GmailTool()
        logger.info("TaskExecutor inicializado con cliente MCP y EmailTool.")

    async def execute_task_and_respond(self, command: str, parameters: Dict[str, Any], sender_number: str):
        """Ejecuta la tarea principal, maneja una posible acción secundaria de envío de correo (ahora directo),
           y envía el resultado principal por WhatsApp."""

        logger.info(f"TaskExecutor: Ejecutando command: {command} para {sender_number} con parameters: {parameters}")
        
        # Construir un objeto interpreted_data compatible con la lógica existente
        interpreted_data = {
            "main_command": command,
            "main_parameters": parameters,
            "secondary_action": None,
            "secondary_parameters": {}
        }
        
        # Detectar si hay una acción secundaria de envío de correo
        if "to_address" in parameters:
            interpreted_data["secondary_action"] = "send_email"
            interpreted_data["secondary_parameters"] = {
                "to_address": parameters["to_address"],
                "subject": parameters.get("subject", f"Resultado de tu solicitud: {command}")
            }
            logger.info(f"TaskExecutor: Acción secundaria detectada: send_email con parámetros: {interpreted_data['secondary_parameters']}")

        main_command = interpreted_data["main_command"]
        main_parameters = interpreted_data["main_parameters"]
        secondary_action = interpreted_data["secondary_action"]
        secondary_parameters = interpreted_data["secondary_parameters"]

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

        # --- MODIFIED SECTION: Handling secondary_action "send_email" DIRECTLY via Email MCP ---
        if execution_successful and secondary_action == "send_email":
            to_address = secondary_parameters.get("to_address")
            email_subject = secondary_parameters.get("subject", f"Resultado de tu solicitud: {main_command}")
            
            if to_address and result_text:
                logger.info(f"TaskExecutor: Acción secundaria 'send_email' detectada. Enviando directamente a {to_address}")
                
                try:
                    # Convertir saltos de línea a <br> para HTML
                    formatted_email_body_content = result_text.replace('\n', '<br>')
                    email_html_body = f"<h1>{email_subject}</h1><p>{formatted_email_body_content}</p><p><br>---<br>Este correo fue generado por GENIA a través de una solicitud de WhatsApp.</p>"

                    # Añadir headers adicionales para mejorar la entregabilidad
                    email_headers = {
                        "X-Priority": "1",
                        "X-MSMail-Priority": "High",
                        "Importance": "High"
                    }

                    # Preparar el payload para el MCP de Email (método directo)
                    email_content_details = {
                        "to_recipients": [
                            {"email": str(to_address), "name": str(to_address)}
                        ],
                        "subject": email_subject,
                        "body_html": email_html_body,
                        "from_address": "noreply_whatsapp@genia.systems",
                        "from_name": "GENIA Systems",
                        "headers": email_headers
                    }
                    
                    mcp_email_request_body = {
                        "role": "user",
                        "content": email_content_details,
                        "metadata": {"source": "genia_backendMPC_whatsapp_flow"}
                    }
                    
                    # Enviar directamente al MCP de Email sin pasar por el scheduler
                    logger.info(f"TaskExecutor: Enviando correo directamente al MCP de Email: {EMAIL_MCP_URL}/mcp/send_email")
                    
                    response = requests.post(
                        f"{EMAIL_MCP_URL}/mcp/send_email",
                        json=mcp_email_request_body,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"TaskExecutor: Correo enviado exitosamente a {to_address}. Respuesta: {response.text}")
                        await send_whatsapp_message(formatted_sender, f"Además, el resultado ha sido enviado a {to_address}.")
                    else:
                        logger.error(f"TaskExecutor: Fallo al enviar correo a {to_address}. Status: {response.status_code}, Respuesta: {response.text}")
                        await send_whatsapp_message(formatted_sender, f"No pude enviar el resultado a {to_address} debido a un error con el servicio de correo.")
                
                except Exception as e_email:
                    logger.exception(f"TaskExecutor: Excepción inesperada al intentar enviar correo a {to_address}: {e_email}")
                    await send_whatsapp_message(formatted_sender, f"Ocurrió un error inesperado al intentar enviar el resultado a {to_address}.")
            else:
                logger.warning(f"TaskExecutor: No se pudo enviar correo. Falta destinatario ('{to_address}') o cuerpo ('{result_text}').")
                if to_address:
                    await send_whatsapp_message(formatted_sender, f"No pude generar el contenido para enviar a {to_address}.")
        # --- END OF MODIFIED SECTION ---
