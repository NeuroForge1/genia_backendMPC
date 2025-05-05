# /home/ubuntu/genia_backendMPC/app/processing/message_processor.py

import os
import requests
import logging
import uuid
from typing import Dict, Any

# Import necessary components
from app.mcp_client.client import MCPClient, SimpleMessage, SimpleTextContent # Import necessary MCP types
from app.core.config import settings
from app.tools.whatsapp_tool import send_whatsapp_message # Import the sender function

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory for temporary audio files
TEMP_AUDIO_DIR = "/tmp/audio_files"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

def download_twilio_media(media_url: str) -> bytes | None:
    """Downloads media from Twilio URL using account credentials."""
    try:
        account_sid = settings.TWILIO_ACCOUNT_SID
        auth_token = settings.TWILIO_AUTH_TOKEN
        if not account_sid or not auth_token:
            logger.error("Twilio credentials (SID or Auth Token) not configured.")
            return None
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

async def process_media_message(media_url: str, from_number: str, mcp_client: MCPClient) -> Dict[str, Any]:
    """Processes an incoming media message (audio): downloads and transcribes.
       Returns a dictionary with status and transcribed text or error.
    """
    logger.info(f"Processing media message from {from_number}: {media_url}")
    temp_audio_path = None
    result = {"status": "error", "text": None, "error": "Unknown processing error"}

    try:
        # 1. Download the audio file
        audio_content = download_twilio_media(media_url)
        if not audio_content:
            result["error"] = "Failed to download audio media"
            logger.error(result["error"])
            return result

        # Save temporarily (use a unique name)
        temp_audio_path = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4()}.ogg") # Assuming ogg format
        with open(temp_audio_path, "wb") as f:
            f.write(audio_content)
        logger.info(f"Audio saved temporarily to {temp_audio_path}")

        # 2. Transcribe the audio using MCP OpenAI server
        logger.info(f"Requesting transcription for {temp_audio_path}")

        # Prepare request for MCP OpenAI transcription capability
        # Assuming the capability expects a file path
        # NOTE: The MCP server needs access to this file path!
        # If MCP runs elsewhere, need to upload the file or send content directly.
        # For local testing, passing the path might work if both run in the same filesystem.
        transcription_request = SimpleMessage(
            role="user",
            content=SimpleTextContent(text=f"Transcribe the audio file at: {temp_audio_path}"), # Or send file content if capability supports it
            metadata={"tool_name": "openai", "capability_name": "transcribe_audio", "parameters": {"file_path": temp_audio_path}}
        )

        transcribed_text = None
        async for response in mcp_client.request_mcp_server("openai", transcription_request):
            if response.role == "assistant" and response.content.text:
                # Assuming the response text *is* the transcription
                transcribed_text = response.content.text.strip()
                logger.info(f"Transcription successful: 	'{transcribed_text}	'")
                result["status"] = "success"
                result["text"] = transcribed_text
                result["error"] = None
                break # Got the transcription
            elif response.role == "error":
                error_message = response.content.text
                logger.error(f"Transcription failed via MCP: {error_message}")
                result["error"] = f"Transcription failed: {error_message}"
                break

        if result["status"] == "error" and result["error"] == "Unknown processing error": # Check if transcription loop finished without success/error
             result["error"] = "No transcription received from MCP server."
             logger.error(result["error"])

    except Exception as e:
        logger.error(f"Error processing media message from {from_number}: {e}", exc_info=True)
        result["error"] = f"Internal error during audio processing: {e}"

    finally:
        # Clean up temporary audio file regardless of outcome
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                logger.info(f"Removed temporary audio file: {temp_audio_path}")
            except OSError as e:
                logger.error(f"Error removing temporary audio file {temp_audio_path}: {e}")

    return result

# Removed process_text_message as interpretation is now handled in twilio_webhook.py
# Removed transcribe_and_process and execute_and_respond as logic is integrated elsewhere

