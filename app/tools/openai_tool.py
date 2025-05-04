import openai
from openai import OpenAI # Import the new client
from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client
import httpx # Ensure httpx is imported for audio download
import tempfile
import os

class OpenAITool(BaseTool):
    """
    Herramienta para interactuar con la API de OpenAI (v1.x.x)
    """
    def __init__(self):
        super().__init__(
            name="openai",
            description="Generación de texto y procesamiento de lenguaje natural con OpenAI"
        )
        
        # Configurar cliente de OpenAI (v1.x.x) - Incluir organization ID
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            organization=settings.OPENAI_ORG_ID # Añadir ID de organización
        )
        
        # Registrar capacidades (schema remains the same)
        self.register_capability(
            name="generate_text",
            description="Genera texto utilizando GPT-4",
            schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "max_tokens": {"type": "integer", "default": 1000},
                    "temperature": {"type": "number", "default": 0.7}
                },
                "required": ["prompt"]
            }
        )
        
        self.register_capability(
            name="transcribe_audio",
            description="Transcribe audio utilizando Whisper",
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
            return await self._generate_text(params)
        elif capability == "transcribe_audio":
            return await self._transcribe_audio(params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")
    
    async def _generate_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera texto utilizando GPT-4 (v1.x.x)
        """
        try:
            # Use the new client and method
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres GENIA, un asistente virtual avanzado."},
                    {"role": "user", "content": params["prompt"]}
                ],
                max_tokens=params.get("max_tokens", 1000),
                temperature=params.get("temperature", 0.7)
            )
            
            return {
                "status": "success",
                "text": response.choices[0].message.content
            }
        # Catch specific exceptions if needed, e.g., openai.AuthenticationError
        except openai.AuthenticationError as e:
             return {"status": "error", "message": f"Error de autenticación OpenAI: {e}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _transcribe_audio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transcribe audio utilizando Whisper (v1.x.x)
        """
        temp_file_path = None
        try:
            # Descargar el audio desde la URL
            async with httpx.AsyncClient() as client:
                response = await client.get(params["audio_url"])
                response.raise_for_status() # Raise exception for bad status codes
                
                # Guardar el audio temporalmente
                # Use context manager for safer file handling
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                    temp_file.write(response.content)
                    temp_file_path = temp_file.name
                
                # Transcribir el audio using the new client
                with open(temp_file_path, "rb") as audio_file:
                    # Use client.audio.transcriptions.create
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1", 
                        file=audio_file
                    )
                
                return {
                    "status": "success",
                    "transcript": transcript.text
                }
        except httpx.HTTPStatusError as e:
             return {"status": "error", "message": f"Error al descargar el audio: {e.response.status_code}"}
        except openai.AuthenticationError as e:
             return {"status": "error", "message": f"Error de autenticación OpenAI: {e}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        finally:
            # Ensure temporary file is deleted
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


