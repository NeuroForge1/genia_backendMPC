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

# Directory for temporary audio files (still useful for download verification)
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
    """Processes an incoming media message (audio): downloads, encodes, and transcribes.
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

        # Optional: Save temporarily for debugging if needed
        # temp_audio_path = os.path.join(TEMP_AUDIO_DIR, f"{uuid.uuid4()}.ogg")
        # with open(temp_audio_path, "wb") as f:
        #     f.write(audio_content)
        # logger.info(f"Audio saved temporarily to {temp_audio_path}")

        # 2. Encode audio content to Base64
        audio_content_b64 = base64.b64encode(audio_content).decode("utf-8")
        logger.info(f"Audio content encoded to base64 (length: {len(audio_content_b64)})")

        # 3. Transcribe the audio using MCP OpenAI server, sending content
        logger.info(f"Requesting transcription by sending audio content.")

        # Prepare request for MCP OpenAI transcription capability
        # Send the base64 encoded content instead of the file path
        transcription_request = SimpleMessage(
            role="user",
            # Content text can be minimal as the main info is in metadata
            content=SimpleTextContent(text="Transcribe the provided audio content."), 
            metadata={
                "tool_name": "openai", 
                "capability_name": "transcribe_audio", 
                "parameters": {
                    # Remove file_path
                    # "file_path": temp_audio_path, 
                    "audio_content_base64": audio_content_b64
                    # Optionally add language hint if known
                    # "language": "es" 
                }
            }
        )

        transcribed_text = None
        async for response in mcp_client.request_mcp_server("openai", transcription_request):
            if response.role == "assistant" and response.content.text:
                # Assuming the response text *is* the transcription
                transcribed_text = response.content.text.strip()
                # Check if the transcription is not the error message we saw before
                if "cannot transcribe audio files" not in transcribed_text.lower() and "unable to transcribe" not in transcribed_text.lower():
                    logger.info(f"Transcription successful: 	\'{transcribed_text}\t'")
                    result["status"] = "success"
                    result["text"] = transcribed_text
                    result["error"] = None
                    break # Got the transcription
                else:
                    # The MCP server still responded it cannot transcribe
                    logger.error(f"MCP OpenAI server responded it cannot transcribe, even with base64 content: {transcribed_text}")
                    result["error"] = f"Transcription failed: Server reported inability to process audio."
                    break
            elif response.role == "error":
                error_message = response.content.text
                logger.error(f"Transcription failed via MCP: {error_message}")
                result["error"] = f"Transcription failed: {error_message}"
                break

        if result["status"] == "error" and result["error"] == "Unknown processing error": # Check if transcription loop finished without success/error
             result["error"] = "No valid transcription received from MCP server."
             logger.error(result["error"])

    except Exception as e:
        logger.error(f"Error processing media message from {from_number}: {e}", exc_info=True)
        result["error"] = f"Internal error during audio processing: {e}"

    # No temporary file to clean up if we don't save it
    # finally:
    #     if temp_audio_path and os.path.exists(temp_audio_path):
    #         try:
    #             os.remove(temp_audio_path)
    #             logger.info(f"Removed temporary audio file: {temp_audio_path}")
    #         except OSError as e:
    #             logger.error(f"Error removing temporary audio file {temp_audio_path}: {e}")

    return result

# Removed process_text_message as interpretation is now handled in twilio_webhook.py
# Removed transcribe_and_process and execute_and_respond as logic is integrated elsewhere

