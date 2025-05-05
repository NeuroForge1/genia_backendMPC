# /home/ubuntu/genia_backendMPC/app/processing/message_processor.py

import os
import requests
import logging
import uuid
from fastapi import BackgroundTasks

# Import MCP Client, Interpreter, Executor, and WhatsApp Tool
# Assuming these are initialized and available, e.g., via dependency injection or global instances
# For now, let's assume they are imported from their respective modules
from app.mcp_client.client import MCPClient
from app.nlp.command_interpreter import CommandInterpreter
from app.tasks.task_executor import TaskExecutor
from app.tools.whatsapp_tool import send_whatsapp_message # Assuming a direct function for simplicity
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components (In a real app, use dependency injection)
mcp_client = MCPClient()
command_interpreter = CommandInterpreter(mcp_client)
task_executor = TaskExecutor(mcp_client)

# Directory for temporary audio files
TEMP_AUDIO_DIR = "/tmp/audio_files"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

def process_text_message(message_body: str, from_number: str, background_tasks: BackgroundTasks):
    """Processes an incoming text message."""
    logger.info(f"Processing text message from {from_number}: {message_body}")
    try:
        # 1. Interpret the command
        intent, entities = command_interpreter.interpret_command(message_body)
        logger.info(f"Interpreted intent: {intent}, entities: {entities}")

        # 2. Execute the task (add to background)
        background_tasks.add_task(execute_and_respond, intent, entities, from_number)

    except Exception as e:
        logger.error(f"Error processing text message from {from_number}: {e}", exc_info=True)
        # Send error message back to user (add to background)
        background_tasks.add_task(send_whatsapp_message, from_number, f"Lo siento, ocurrió un error al procesar tu mensaje: {e}")

def process_media_message(media_url: str, from_number: str, background_tasks: BackgroundTasks):
    """Processes an incoming media message (audio)."""
    logger.info(f"Processing media message from {from_number}: {media_url}")
    try:
        # 1. Download the audio file
        audio_content = download_twilio_media(media_url)
        if not audio_content:
            raise ValueError("Failed to download audio media")

        # Save temporarily
        temp_audio_path = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4()}.ogg") # Assuming ogg format from Twilio WhatsApp
        with open(temp_audio_path, "wb") as f:
            f.write(audio_content)
        logger.info(f"Audio saved temporarily to {temp_audio_path}")

        # 2. Transcribe the audio using MCP OpenAI server
        # Add transcription task to background
        background_tasks.add_task(transcribe_and_process, temp_audio_path, from_number)

    except Exception as e:
        logger.error(f"Error processing media message from {from_number}: {e}", exc_info=True)
        # Send error message back to user (add to background)
        background_tasks.add_task(send_whatsapp_message, from_number, f"Lo siento, ocurrió un error al procesar tu mensaje de audio: {e}")

def download_twilio_media(media_url: str) -> bytes | None:
    """Downloads media from Twilio URL using account credentials."""
    try:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        response = requests.get(media_url, auth=(account_sid, auth_token))
        response.raise_for_status() # Raise an exception for bad status codes
        logger.info(f"Successfully downloaded media from {media_url}")
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download media from {media_url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading media from {media_url}: {e}")
        return None

async def transcribe_and_process(audio_path: str, from_number: str):
    """Background task to transcribe audio and then process the text."""
    transcribed_text = None
    try:
        logger.info(f"Requesting transcription for {audio_path}")
        # Use MCP client to call the transcribe_audio capability
        transcription_result = await mcp_client.execute_tool_capability(
            tool_name="openai",
            capability_name="transcribe_audio",
            parameters={"file_path": audio_path} # Pass file path to MCP server
        )

        if transcription_result and transcription_result.get("status") == "success":
            transcribed_text = transcription_result.get("result", {}).get("text")
            logger.info(f"Transcription successful: {transcribed_text}")
        else:
            error_message = transcription_result.get("error", "Unknown transcription error")
            logger.error(f"Transcription failed: {error_message}")
            await send_whatsapp_message(from_number, f"Lo siento, no pude transcribir tu mensaje de audio: {error_message}")
            return # Stop processing if transcription failed

    except Exception as e:
        logger.error(f"Error during transcription request for {audio_path}: {e}", exc_info=True)
        await send_whatsapp_message(from_number, f"Lo siento, ocurrió un error interno durante la transcripción: {e}")
        return # Stop processing on error
    finally:
        # Clean up temporary audio file
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
                logger.info(f"Removed temporary audio file: {audio_path}")
            except OSError as e:
                logger.error(f"Error removing temporary audio file {audio_path}: {e}")

    # If transcription was successful, process the text
    if transcribed_text:
        logger.info(f"Processing transcribed text from {from_number}: {transcribed_text}")
        try:
            # 1. Interpret the command
            intent, entities = command_interpreter.interpret_command(transcribed_text)
            logger.info(f"Interpreted intent from audio: {intent}, entities: {entities}")

            # 2. Execute the task (already in background)
            await execute_and_respond(intent, entities, from_number)

        except Exception as e:
            logger.error(f"Error processing transcribed text from {from_number}: {e}", exc_info=True)
            await send_whatsapp_message(from_number, f"Lo siento, ocurrió un error al procesar tu comando de voz: {e}")

async def execute_and_respond(intent: str, entities: dict, from_number: str):
    """Executes the task based on intent and sends response via WhatsApp."""
    try:
        # Execute the task using TaskExecutor
        execution_result = await task_executor.execute_task(intent, entities)

        if execution_result and execution_result.get("status") == "success":
            response_message = execution_result.get("result", "Tarea completada.")
            logger.info(f"Task execution successful for {from_number}. Result: {response_message}")
            await send_whatsapp_message(from_number, response_message)
        else:
            error_message = execution_result.get("error", "Error desconocido durante la ejecución.")
            logger.error(f"Task execution failed for {from_number}: {error_message}")
            await send_whatsapp_message(from_number, f"Lo siento, no pude completar tu solicitud: {error_message}")

    except Exception as e:
        logger.error(f"Error during task execution or response for {from_number}: {e}", exc_info=True)
        await send_whatsapp_message(from_number, f"Lo siento, ocurrió un error interno al ejecutar tu comando: {e}")


