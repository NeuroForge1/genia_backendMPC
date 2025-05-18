# /home/ubuntu/genia_backendMPC/app/tools/whatsapp_tool.py

import logging
import math
from app.mcp_client.client import mcp_client_instance, SimpleMessage, SimpleTextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constante para el límite de caracteres de Twilio para WhatsApp
TWILIO_WHATSAPP_CHAR_LIMIT = 1600

async def send_whatsapp_message(recipient_number: str, message_text: str):
    """Envía un mensaje de WhatsApp al destinatario especificado usando el servidor MCP de Twilio.
    Si el mensaje excede el límite de caracteres de Twilio (1600), lo divide en múltiples mensajes."""
    
    # Verificar si el mensaje excede el límite de caracteres
    if len(message_text) <= TWILIO_WHATSAPP_CHAR_LIMIT:
        # Si no excede el límite, enviar como un solo mensaje
        return await _send_single_whatsapp_message(recipient_number, message_text)
    else:
        # Si excede el límite, dividir en múltiples mensajes
        return await _send_chunked_whatsapp_message(recipient_number, message_text)

async def _send_single_whatsapp_message(recipient_number: str, message_text: str):
    """Envía un único mensaje de WhatsApp."""
    logger.info(f"WhatsappTool: Enviando mensaje a {recipient_number}: 	'{message_text[:50]}...'	")

    mcp_server_name = "twilio"
    # Capability name expected by the Twilio MCP server
    capability_name = "send_whatsapp_message"

    # Content can be descriptive
    request_content_text = f"Enviar WhatsApp a {recipient_number}"
    # Metadata structure expected by the Twilio MCP server
    request_metadata = {
        "capability": capability_name, # Use 'capability' key
        "params": {                   # Use 'params' key
            "to": recipient_number, # Parameter name expected by Twilio API
            "body": message_text     # Parameter name expected by Twilio API
        }
        # Include user_id if available and needed by MCP server
        # "user_id": "some_user_identifier"
    }

    request_message = SimpleMessage(
        role="user",
        content=SimpleTextContent(text=request_content_text),
        metadata=request_metadata
    )

    try:
        # Enviar la solicitud al servidor MCP de Twilio
        async for response in mcp_client_instance.request_mcp_server(mcp_server_name, request_message):
            if response.role == "assistant" and response.content.text:
                # Assuming assistant response indicates success or contains relevant info (like message SID)
                logger.info(f"WhatsappTool: Respuesta del servidor MCP {mcp_server_name}: {response.content.text}")
            elif response.role == "error":
                logger.error(f"WhatsappTool: Error recibido del servidor MCP {mcp_server_name}: {response.content.text}")
                # Propagate the error
                raise Exception(f"Error del MCP Twilio: {response.content.text}")
            # Exit after the first response (or error)
            break
        else:
            # This would happen if the generator finishes without yielding anything
            logger.warning(f"WhatsappTool: No se recibió respuesta del servidor MCP {mcp_server_name}.")
            raise Exception(f"No se recibió respuesta del MCP Twilio.")

    except ConnectionError as e:
        logger.error(f"WhatsappTool: Error de conexión al servidor MCP {mcp_server_name}: {e}")
        raise ConnectionError(f"Error de conexión al MCP Twilio: {e}")
    except Exception as e:
        # Re-raise other exceptions after logging, unless it's the specific MCP error
        if not str(e).startswith("Error del MCP Twilio") and not str(e).startswith("No se recibió respuesta del MCP Twilio"):
             logger.error(f"WhatsappTool: Error inesperado al enviar mensaje: {e}", exc_info=True)
             raise Exception(f"Error inesperado en WhatsappTool: {e}")
        else:
             raise e # Re-raise the specific MCP or no-response exception

async def _send_chunked_whatsapp_message(recipient_number: str, message_text: str):
    """Divide un mensaje largo en múltiples partes y las envía secuencialmente."""
    # Calcular el número de partes necesarias
    num_parts = math.ceil(len(message_text) / TWILIO_WHATSAPP_CHAR_LIMIT)
    logger.info(f"WhatsappTool: Dividiendo mensaje largo en {num_parts} partes para {recipient_number}")
    
    # Dividir el mensaje en partes
    success_count = 0
    for i in range(num_parts):
        start_idx = i * TWILIO_WHATSAPP_CHAR_LIMIT
        end_idx = min((i + 1) * TWILIO_WHATSAPP_CHAR_LIMIT, len(message_text))
        chunk = message_text[start_idx:end_idx]
        
        # Añadir indicador de parte al inicio del mensaje
        part_indicator = f"[Parte {i+1}/{num_parts}] " if num_parts > 1 else ""
        chunk_with_indicator = part_indicator + chunk
        
        try:
            # Enviar cada parte como un mensaje independiente
            await _send_single_whatsapp_message(recipient_number, chunk_with_indicator)
            success_count += 1
        except Exception as e:
            logger.error(f"WhatsappTool: Error al enviar parte {i+1}/{num_parts} a {recipient_number}: {e}")
            # Continuar con las partes restantes incluso si una falla
            continue
    
    # Verificar si todas las partes se enviaron correctamente
    if success_count == num_parts:
        logger.info(f"WhatsappTool: Todas las {num_parts} partes del mensaje enviadas exitosamente a {recipient_number}")
        return True
    else:
        logger.warning(f"WhatsappTool: Solo {success_count} de {num_parts} partes enviadas exitosamente a {recipient_number}")
        if success_count > 0:
            return True  # Consideramos éxito parcial como éxito
        else:
            raise Exception(f"No se pudo enviar ninguna parte del mensaje a {recipient_number}")
