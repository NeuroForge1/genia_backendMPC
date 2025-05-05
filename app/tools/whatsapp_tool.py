# /home/ubuntu/genia_backendMPC/app/tools/whatsapp_tool.py

import logging
from app.mcp_client.client import mcp_client_instance, SimpleMessage, SimpleTextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_whatsapp_message(recipient_number: str, message_text: str):
    """Envía un mensaje de WhatsApp al destinatario especificado usando el servidor MCP de Twilio."""
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


