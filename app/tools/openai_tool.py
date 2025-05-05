import openai # Keep for exception handling
# from openai import OpenAI # Removed direct client import
from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.core.config import settings
# from app.db.supabase_manager import get_supabase_client # Not used in this file
import httpx # Ensure httpx is imported for audio download
import tempfile
import os

# Import the simplified MCP client instance and message structure
from app.mcp_client.client import mcp_client_instance, SimpleMessage, SimpleTextContent

class OpenAITool(BaseTool):
    """
    Herramienta para interactuar con la API de OpenAI (v1.x.x) a través de MCP
    """
    def __init__(self):
        super().__init__(
            name="openai",
            description="Generación de texto y procesamiento de lenguaje natural con OpenAI"
        )
        
        # Removed direct OpenAI client initialization
        
        # Registrar capacidades (schema remains the same)
        self.register_capability(
            name="generate_text",
            description="Genera texto utilizando GPT-4 (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "max_tokens": {"type": "integer", "default": 1000},
                    "temperature": {"type": "number", "default": 0.7},
                    "model": {"type": "string", "default": "gpt-4"} # Allow specifying model
                },
                "required": ["prompt"]
            }
        )
        
        self.register_capability(
            name="transcribe_audio",
            description="Transcribe audio utilizando Whisper (NOTA: Aún no integrado con MCP)",
            schema={
                "type": "object",
                "properties": {
                    "audio_url": {"type": "string"}
                },
                "required": ["audio_url"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta OpenAI
        """
        if capability == "generate_text":
            return await self._generate_text_mcp(params)
        elif capability == "transcribe_audio":
            # TODO: Integrate transcribe_audio with MCP (requires file handling support)
            # For now, keep the old implementation or return an error/not implemented message
            # return await self._transcribe_audio(params) # Old implementation
            return {"status": "error", "message": "La transcripción de audio vía MCP aún no está implementada."}
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")
    
    async def _generate_text_mcp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera texto utilizando un modelo de OpenAI a través del servidor MCP.
        """
        try:
            # Construct the MCP message payload
            mcp_message = SimpleMessage(
                role="user",
                content=SimpleTextContent(text=params["prompt"]),
                metadata={
                    "model": params.get("model", "gpt-4"), # Pass model from params
                    "max_tokens": params.get("max_tokens", 1000),
                    "temperature": params.get("temperature", 0.7)
                    # Add other OpenAI parameters if needed by the server
                }
            )
            
            # Use the global MCP client instance
            response_text = None
            # Consume the async generator to get the response
            # Since the simplified server sends only one message, we get the first one
            async for response_msg in mcp_client_instance.request_mcp_server("openai", mcp_message):
                if response_msg.role == "assistant" and isinstance(response_msg.content, SimpleTextContent):
                    response_text = response_msg.content.text
                    break # Stop after getting the first valid message
                elif response_msg.role == "error": # Handle potential errors from server
                     return {"status": "error", "message": f"Error recibido del servidor MCP: {response_msg.content.text}"}

            if response_text:
                return {
                    "status": "success",
                    "text": response_text
                }
            else:
                return {"status": "error", "message": "No se recibió una respuesta válida del servidor MCP de OpenAI."}

        except ConnectionError as conn_err:
             return {"status": "error", "message": f"Error de conexión con el servidor MCP de OpenAI: {conn_err}"}
        except Exception as e:
            # Consider more specific exception handling for MCP communication errors
            return {"status": "error", "message": f"Error inesperado al comunicarse con el servidor MCP de OpenAI: {e}"}

    # --- Old methods using direct OpenAI client (kept for reference/future use if needed) ---
    # ... (resto del código sin cambios) ...


