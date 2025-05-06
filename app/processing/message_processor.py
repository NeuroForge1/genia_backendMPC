# /home/ubuntu/genia_backendMPC/app/processing/message_processor.py

import os
import requests
import logging
import uuid
import base64 # Import base64 encoding
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
        logger.info(f"Attempting to download media from: {media_url}")
        response = requests.get(media_url, auth=(account_sid, auth_token))
        logger.info(f"Download response status code: {response.status_code}")
        response.raise_for_status() # Raise an exception for bad status codes
        logger.info(f"Successfully downloaded media from {media_url}")
        return response.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download media from {media_url}: {e}")
        # Log response content if download failed but got a response
        if hasattr(e, "response") and e.response is not None:
            logger.error(f"Download error response content: {e.response.content}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading media from {media_url}: {e}")
        return None

async def process_media_message(media_url: str, from_number: str, mcp_client: MCPClient) -> Dict[str, Any]:
    """Processes an incoming media message (audio): downloads, logs info, encodes, and transcribes.
       Returns a dictionary with status and transcribed text or error.
    """
    logger.info(f"Processing media message from {from_number}: {media_url}")
    temp_audio_path = None # Keep for potential debugging/local saving if needed
    result = {"status": "error", "text": None, "error": "Unknown processing error"}

    try:
        # 1. Download the audio file content
        audio_content = download_twilio_media(media_url)
        if not audio_content:
            result["error"] = "Failed to download audio media"
            logger.error(result["error"])
            return result

        # --- ADDED LOGGING FOR DOWNLOADED CONTENT --- 
        logger.info(f"Downloaded audio content size: {len(audio_content)} bytes")
        logger.info(f"Downloaded audio content (first 50 bytes): {audio_content[:50]}")
        # --- END ADDED LOGGING ---

        # Save temporarily to verify content before sending to Whisper
        temp_audio_path = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4()}.ogg")
        try:
            with open(temp_audio_path, "wb") as f:
                f.write(audio_content)
            logger.info(f"Audio saved temporarily to {temp_audio_path} for inspection.")
            # Basic check: if size is suspiciously small, log a warning
            if len(audio_content) < 100: # Arbitrary small size threshold
                logger.warning(f"Downloaded audio content size ({len(audio_content)} bytes) is very small, may indicate an issue.")
        except Exception as save_err:
            logger.error(f"Error saving temporary audio file {temp_audio_path}: {save_err}")
            # Continue processing, but log the save error

        # 2. Encode audio content to Base64
        audio_content_b64 = base64.b64encode(audio_content).decode("utf-8")
        logger.info(f"Audio content encoded to base64 (length: {len(audio_content_b64)})")

        # 3. Transcribe the audio using MCP OpenAI server, sending content
        logger.info(f"Requesting transcription by sending audio content.")

        # Prepare request for MCP OpenAI transcription capability
        transcription_request = SimpleMessage(
            role="user",
            content=SimpleTextContent(text="Transcribe the provided audio content."), 
            metadata={
                "tool_name": "openai", 
                "capability_name": "transcribe_audio", 
                "parameters": {
                    "audio_content_base64": audio_content_b64
                }
            }
        )

        transcribed_text = None
        async for response in mcp_client.request_mcp_server("openai", transcription_request):
            if response.role == "assistant" and response.content.text:
                transcribed_text = response.content.text.strip()
                if "cannot transcribe audio" not in transcribed_text.lower() and "unable to transcribe" not in transcribed_text.lower():
                    logger.info(f"Transcription successful: 	\'{transcribed_text}\t'")
                    result["status"] = "success"
                    result["text"] = transcribed_text
                    result["error"] = None
                    break 
                else:
                    logger.error(f"MCP OpenAI server responded it cannot transcribe: {transcribed_text}")
                    result["error"] = f"Transcription failed: Server reported inability to process audio."
                    break
            elif response.role == "error":
                error_message = response.content.text
                logger.error(f"Transcription failed via MCP: {error_message}")
                result["error"] = f"Transcription failed: {error_message}"
                break

        if result["status"] == "error" and result["error"] == "Unknown processing error":
             result["error"] = "No valid transcription received from MCP server."
             logger.error(result["error"])

    except Exception as e:
        logger.error(f"Error processing media message from {from_number}: {e}", exc_info=True)
        result["error"] = f"Internal error during audio processing: {e}"

    finally:
        # Clean up the temporary audio file if it was saved
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                logger.info(f"Removed temporary audio file: {temp_audio_path}")
            except OSError as e:
                logger.error(f"Error removing temporary audio file {temp_audio_path}: {e}")

    return result

