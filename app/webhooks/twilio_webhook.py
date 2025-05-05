# /home/ubuntu/genia_backendMPC/app/webhooks/twilio_webhook.py

from fastapi import APIRouter, Request, Response, HTTPException, BackgroundTasks
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
import os
import logging

# Import processing functions
from app.processing.message_processor import process_text_message, process_media_message
from app.nlp.command_interpreter import interpret_command
from app.tasks.task_executor import execute_task
# Import sender tool for potential error messages
from app.tools.whatsapp_tool import WhatsAppTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Load Twilio Auth Token from environment variables
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

if not TWILIO_AUTH_TOKEN:
    logger.error("TWILIO_AUTH_TOKEN environment variable not set.")
    # Handle missing token appropriately

validator = RequestValidator(TWILIO_AUTH_TOKEN if TWILIO_AUTH_TOKEN else "")

# Initialize sender tool instance (consider dependency injection later)
wa_sender_tool = WhatsAppTool()

async def process_command_background(sender_number: str, message_content: str, is_audio: bool = False):
    """Processes the command (text or transcribed audio) in the background."""
    logger.info(f"Starting background processing for {sender_number} (Source: {	'Audio' if is_audio else 'Text'}	)")
    try:
        # 1. Interpret the command using OpenAI via MCP
        # message_content is either the original text or the transcribed audio
        interpreted_command = await interpret_command(message_content)
        
        if interpreted_command:
            # 2. Execute the task based on the interpretation
            await execute_task(sender_number, interpreted_command)
        else:
            logger.warning(f"Command interpretation failed for content: 	'{message_content[:100]}...	'")
            # Send a generic failure message back to the user
            formatted_sender = sender_number if sender_number.startswith(	'whatsapp:	') else f"whatsapp:{sender_number}"
            try:
                await wa_sender_tool.run_tool("send_message", {"to": formatted_sender, "body": "Lo siento, no pude entender tu comando."})
            except Exception as send_err:
                 logger.error(f"Failed to send interpretation error message to {sender_number}: {send_err}")
            
    except Exception as e:
        logger.exception(f"Error during background processing for {sender_number}: {e}")
        # Optionally notify user of unexpected error
        formatted_sender = sender_number if sender_number.startswith(	'whatsapp:	') else f"whatsapp:{sender_number}"
        try:
            await wa_sender_tool.run_tool("send_message", {"to": formatted_sender, "body": "Ocurrió un error inesperado al procesar tu solicitud."})
        except Exception as send_err:
             logger.error(f"Failed to send generic error message to {sender_number}: {send_err}")

async def process_audio_message_background(sender_number: str, media_url: str, media_type: str):
    """Handles audio message processing: download, transcribe, and trigger command processing."""
    logger.info(f"Starting background audio processing for {sender_number}")
    processed_data = await process_media_message(sender_number, media_url, media_type)
    
    if processed_data and processed_data.get("type") == "audio_transcribed":
        transcribed_text = processed_data.get("content")
        if transcribed_text is not None: # Check for None, empty string is valid
            logger.info(f"Audio transcribed for {sender_number}, triggering command processing.")
            # Now process the transcribed text like a normal text command
            await process_command_background(sender_number, transcribed_text, is_audio=True)
        else:
            logger.error(f"Audio processing for {sender_number} finished but no transcribed text found.")
            # Notify user about transcription issue
            formatted_sender = sender_number if sender_number.startswith(	'whatsapp:	') else f"whatsapp:{sender_number}"
            try:
                await wa_sender_tool.run_tool("send_message", {"to": formatted_sender, "body": "Lo siento, no pude transcribir tu mensaje de audio."})
            except Exception as send_err:
                 logger.error(f"Failed to send transcription error message to {sender_number}: {send_err}")
    else:
        logger.error(f"Audio processing failed for {sender_number} (download or transcription). No processed data returned.")
        # Notify user about processing issue
        formatted_sender = sender_number if sender_number.startswith(	'whatsapp:	') else f"whatsapp:{sender_number}"
        try:
            await wa_sender_tool.run_tool("send_message", {"to": formatted_sender, "body": "Lo siento, hubo un problema al procesar tu mensaje de audio."})
        except Exception as send_err:
             logger.error(f"Failed to send audio processing error message to {sender_number}: {send_err}")

@router.post("/twilio/whatsapp", status_code=200)
async def receive_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    """Receives incoming WhatsApp messages, validates, acknowledges Twilio, 
       and triggers background processing for text or audio commands."""
    if not TWILIO_AUTH_TOKEN:
        logger.error("Cannot validate Twilio request: TWILIO_AUTH_TOKEN not configured.")
        raise HTTPException(status_code=500, detail="Server configuration error.")

    twilio_signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    post_vars = await request.form()
    post_vars_dict = dict(post_vars)

    logger.info(f"Received request from Twilio. URL: {url}")
    logger.info(f"Form data: {post_vars_dict}")

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
         # background_tasks.add_task(wa_sender_tool.run_tool, "send_message", {"to": sender_number, "body": "Lo siento, solo puedo procesar mensajes de texto y audio por ahora."})

    else:
        logger.warning(f"Received message from {sender_number} with no body or media.")
        # Optionally send a message asking for input
        # background_tasks.add_task(wa_sender_tool.run_tool, "send_message", {"to": sender_number, "body": "Hola, ¿en qué puedo ayudarte?"})

    # Respond immediately to Twilio to acknowledge receipt
    twiml_response = MessagingResponse()
    return Response(content=str(twiml_response), media_type="application/xml")

@router.get("/twilio/health")
async def health_check():
    return {"status": "ok"}



# Trivial change to force update

