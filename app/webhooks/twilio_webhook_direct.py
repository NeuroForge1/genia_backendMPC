"""
Webhook para recibir mensajes de Twilio/WhatsApp y procesarlos usando el flujo directo de correo.
Esta versión usa task_executor_direct.py para enviar correos directamente sin usar el scheduler.
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
import logging
from typing import Optional
import asyncio

# Importar el intérprete de comandos
from app.nlp.command_interpreter import CommandInterpreter
# Importar el ejecutor de tareas DIRECTO (sin scheduler)
from app.tasks.task_executor_direct import TaskExecutor
# Importar el cliente MCP
from app.mcp_client.client import MCPClient

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter()

# Crear instancias de las dependencias
command_interpreter = CommandInterpreter()
mcp_client = MCPClient()
task_executor = TaskExecutor(mcp_client)

@router.post("/webhook/twilio")
async def twilio_webhook(
    request: Request,
    Body: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    ProfileName: Optional[str] = Form(None)
):
    """
    Webhook para recibir mensajes de Twilio/WhatsApp.
    Esta versión usa el flujo DIRECTO para enviar correos.
    """
    logger.info(f"Webhook recibido de Twilio - From: {From}, To: {To}, ProfileName: {ProfileName}")
    
    if not Body or not From:
        logger.error("Mensaje recibido sin cuerpo o remitente")
        raise HTTPException(status_code=400, detail="Mensaje recibido sin cuerpo o remitente")
    
    try:
        # Interpretar el comando del usuario
        interpreted_data = command_interpreter.interpret_command(Body)
        logger.info(f"Comando interpretado: {interpreted_data}")
        
        # Ejecutar la tarea y responder (usando el flujo DIRECTO)
        await task_executor.execute_task_and_respond(interpreted_data, From)
        
        # Devolver una respuesta vacía a Twilio para evitar mensajes duplicados
        return {}
    
    except Exception as e:
        logger.exception(f"Error al procesar mensaje de WhatsApp: {e}")
        # En caso de error, intentar enviar un mensaje de error al usuario
        try:
            formatted_sender = From if From.startswith("whatsapp:") else f"whatsapp:{From}"
            from app.tools.whatsapp_tool import send_whatsapp_message
            await send_whatsapp_message(
                formatted_sender, 
                "Lo siento, ocurrió un error al procesar tu solicitud. Por favor, intenta de nuevo más tarde."
            )
        except Exception as send_err:
            logger.error(f"No se pudo enviar mensaje de error a {From}: {send_err}")
        
        # Devolver una respuesta vacía a Twilio
        return {}
