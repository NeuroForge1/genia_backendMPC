# /home/ubuntu/genia_backendMPC/app/webhooks/twilio_webhook.py

from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging

# Import processing functions and necessary classes
from app.processing.message_processor import process_media_message # Keep this for audio
from app.mcp_client.client import MCPClient
from app.nlp.command_interpreter import CommandInterpreter
from app.tasks.task_executor import TaskExecutor
from app.tools.whatsapp_tool import send_whatsapp_message # Use the direct function for sending
from app.core.config import settings # Import settings for credentials

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Load Twilio Auth Token from environment variables
TWILIO_AUTH_TOKEN = settings.TWILIO_AUTH_TOKEN

if not TWILIO_AUTH_TOKEN:
    logger.error("TWILIO_AUTH_TOKEN environment variable not set.")
    # Handle missing token appropriately

validator = RequestValidator(TWILIO_AUTH_TOKEN if TWILIO_AUTH_TOKEN else "")

# Initialize components (In a real app, use dependency injection)
# Ensure MCPClient, CommandInterpreter, TaskExecutor are initialized correctly
# Assuming MCPClient can be instantiated directly for now
mcp_client = MCPClient()
command_interpreter = CommandInterpreter(mcp_client)
task_executor = TaskExecutor(mcp_client)

async def process_command_background(sender_number: str, message_content: str, is_audio: bool = False):
    """Processes the command (text or transcribed audio) in the background."""
    logger.info(f"Starting background processing for {sender_number} (Source: {'Audio' if is_audio else 'Text'})")
    try:
        # 1. Interpret the command using the CommandInterpreter instance
        # message_content is either the original text or the transcribed audio
        # Use await since interpret_command is async
        interpreted_data = await command_interpreter.interpret_command(message_content)
        command = interpreted_data.get("command", "unknown")
        parameters = interpreted_data.get("parameters", {})
        
        # Extraer secondary_action y secondary_parameters si existen
        secondary_action = interpreted_data.get("secondary_action")
        secondary_parameters = interpreted_data.get("secondary_parameters", {})
        
        # Si hay una acción secundaria de envío de correo, añadir to_address a parameters
        # para mantener compatibilidad con la versión anterior de TaskExecutor
        if secondary_action == "send_email" and "to_address" in secondary_parameters:
            parameters["to_address"] = secondary_parameters["to_address"]
            if "subject" in secondary_parameters:
                parameters["subject"] = secondary_parameters["subject"]
            logger.info(f"Detected email action, added to_address '{secondary_parameters['to_address']}' to parameters")

        if command != "unknown":
            logger.info(f"Interpreted command: {command}, parameters: {parameters}")
            # 2. Execute the task based on the interpretation (using TaskExecutor instance)
            # Pass command and parameters to the executor's method
            # Assuming execute_task is now part of the TaskExecutor class and accepts command/params
            await task_executor.execute_task_and_respond(command, parameters, sender_number)
        else:
            logger.warning(f"Command interpretation failed or returned 'unknown' for content: '{message_content[:100]}...'")
            # Send a generic failure message back to the user
            formatted_sender = sender_number if sender_number.startswith('whatsapp:') else f"whatsapp:{sender_number}"
            try:
                # Use the imported send_whatsapp_message function
                await send_whatsapp_message(formatted_sender, "Lo siento, no pude entender tu comando.")
            except Exception as send_err:
                 logger.error(f"Failed to send interpretation error message to {sender_number}: {send_err}")

    except Exception as e:
        logger.exception(f"Error during background processing for {sender_number}: {e}")
        # Optionally notify user of unexpected error
        formatted_sender = sender_number if sender_number.startswith('whatsapp:') else f"whatsapp:{sender_number}"
        try:
            await send_whatsapp_message(formatted_sender, "Ocurrió un error inesperado al procesar tu solicitud.")
        except Exception as send_err:
             logger.error(f"Failed to send generic error message to {sender_number}: {send_err}")

async def process_audio_message_background(sender_number: str, media_url: str, media_type: str):
    """Handles audio message processing: download, transcribe, and trigger command processing."""
    logger.info(f"Starting background audio processing for {sender_number}")
    # Use the process_media_message function from the processor module
    # This function should handle download, transcription (via MCP), and then call process_command_background
    # We need to pass the necessary components or ensure they are accessible within process_media_message
    # For now, assuming process_media_message is correctly implemented in its module
    # It might need access to mcp_client and command_interpreter, task_executor implicitly via process_command_background

    # Let's refine this: process_media_message should ideally return the transcribed text
    # or handle the error reporting itself.

    transcribed_text = None
    try:
        # Call the function from message_processor to handle download and transcription
        # This function now needs mcp_client passed or accessible
        processed_data = await process_media_message(media_url, sender_number, mcp_client)

        if processed_data and processed_data.get("status") == "success":
            transcribed_text = processed_data.get("text")
            if transcribed_text is not None:
                logger.info(f"Audio transcribed for {sender_number}, triggering command processing.")
                # Now process the transcribed text like a normal text command
                await process_command_background(sender_number, transcribed_text, is_audio=True)
            else:
                 # This case should ideally be handled within process_media_message
                 logger.error(f"Audio processing for {sender_number} finished but no transcribed text found.")
                 formatted_sender = sender_number if sender_number.startswith('whatsapp:') else f"whatsapp:{sender_number}"
                 await send_whatsapp_message(formatted_sender, "Lo siento, no pude transcribir tu mensaje de audio.")
        else:
            # Error handled and logged within process_media_message, maybe send message too
            error_msg = processed_data.get("error", "Hubo un problema al procesar tu mensaje de audio.")
            logger.error(f"Audio processing failed for {sender_number}: {error_msg}")
            formatted_sender = sender_number if sender_number.startswith('whatsapp:') else f"whatsapp:{sender_number}"
            await send_whatsapp_message(formatted_sender, f"Lo siento, {error_msg}")

    except Exception as e:
        logger.exception(f"Unexpected error in process_audio_message_background for {sender_number}: {e}")
        formatted_sender = sender_number if sender_number.startswith('whatsapp:') else f"whatsapp:{sender_number}"
        await send_whatsapp_message(formatted_sender, "Lo siento, ocurrió un error inesperado al procesar tu audio.")


@router.post("/twilio/whatsapp", status_code=200)
async def receive_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    """Receives incoming WhatsApp messages, validates, acknowledges Twilio,
       and triggers background processing for text or audio commands."""
    if not TWILIO_AUTH_TOKEN:
        logger.error("Cannot validate Twilio request: TWILIO_AUTH_TOKEN not configured.")
        raise HTTPException(status_code=500, detail="Server configuration error.")

    twilio_signature = request.headers.get("X-Twilio-Signature", "")
    # Use request.url_for or build URL carefully if behind proxy
    # For Render/proxies, request.url might not be the original URL Twilio used.
    # A safer approach might be to reconstruct it or get it from headers if available.
    # For now, using str(request.url) might work if Render forwards headers correctly.
    url = str(request.url)
    post_vars = await request.form()
    post_vars_dict = dict(post_vars)

    logger.info(f"Received request from Twilio. URL: {url}")
    logger.info(f"Form data: {post_vars_dict}")

    # Validate the request using the Twilio helper library
    # NOTE: The URL passed to validate MUST be the URL Twilio used to call your webhook,
    # including any query parameters. If using a proxy, ensure the original URL is used.
    # If validation fails repeatedly, double-check the URL construction and Auth Token.
    if not validator.validate(url, post_vars_dict, twilio_signature):
        logger.warning("Twilio request validation failed.")
        raise HTTPException(status_code=403, detail="Twilio request validation failed")

    logger.info("Twilio request validated successfully.")

    sender_number = post_vars_dict.get("From")
    message_body = post_vars_dict.get("Body")
    num_media = int(post_vars_dict.get("NumMedia", 0))
    media_url = post_vars_dict.get("MediaUrl0") if num_media > 0 else None
    media_content_type = post_vars_dict.get("MediaContentType0") if num_media > 0 else None

    if not sender_number:
         logger.error("Received message without sender number (From field missing).")
         # Still return 200 OK to Twilio
         twiml_response = MessagingResponse()
         return Response(content=str(twiml_response), media_type="application/xml")

    logger.info(f"Received message from {sender_number}.")

    if message_body:
        logger.info(f"Message Body: {message_body}")
        # Trigger background processing for text messages
        background_tasks.add_task(process_command_background, sender_number, message_body, is_audio=False)
        logger.info(f"Added text command processing to background tasks for {sender_number}.")

    elif media_url and media_content_type and media_content_type.startswith("audio/"):
        logger.info(f"Media URL: {media_url} (Type: {media_content_type})")
        # Trigger background processing specific to audio messages
        background_tasks.add_task(process_audio_message_background, sender_number, media_url, media_content_type)
        logger.info(f"Added audio message processing to background tasks for {sender_number}.")

    elif media_url: # Handle non-audio media if needed in the future
         logger.warning(f"Received non-audio media message from {sender_number} (Type: {media_content_type}). Ignoring.")
         # Optionally send a message indicating non-audio media is not supported
         # formatted_sender = sender_number if sender_number.startswith('whatsapp:') else f"whatsapp:{sender_number}"
         # background_tasks.add_task(send_whatsapp_message, formatted_sender, "Lo siento, solo puedo procesar mensajes de texto y audio por ahora.")

    else:
        logger.warning(f"Received message from {sender_number} with no body or media.")
        # Optionally send a message asking for input
        # formatted_sender = sender_number if sender_number.startswith('whatsapp:') else f"whatsapp:{sender_number}"
        # background_tasks.add_task(send_whatsapp_message, formatted_sender, "Hola, ¿en qué puedo ayudarte?")

    # Respond immediately to Twilio to acknowledge receipt
    twiml_response = MessagingResponse()
    return Response(content=str(twiml_response), media_type="application/xml")

# Keep the health check endpoint
@router.get("/health") # Changed path to be relative to prefix
async def health_check():
    return {"status": "ok"}
