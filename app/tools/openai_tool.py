import openai
from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

class OpenAITool(BaseTool):
    """
    Herramienta para interactuar con la API de OpenAI
    """
    def __init__(self):
        super().__init__(
            name="openai",
            description="Generación de texto y procesamiento de lenguaje natural con OpenAI"
        )
        
        # Configurar cliente de OpenAI
        openai.api_key = settings.OPENAI_API_KEY
        
        # Registrar capacidades
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
        Genera texto utilizando GPT-4
        """
        try:
            response = await openai.ChatCompletion.create(
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
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _transcribe_audio(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transcribe audio utilizando Whisper
        """
        try:
            # Descargar el audio desde la URL
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(params["audio_url"])
                if response.status_code != 200:
                    raise ValueError(f"Error al descargar el audio: {response.status_code}")
                
                # Guardar el audio temporalmente
                import tempfile
                import os
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                temp_file.write(response.content)
                temp_file.close()
                
                # Transcribir el audio
                with open(temp_file.name, "rb") as audio_file:
                    transcript = await openai.Audio.transcribe("whisper-1", audio_file)
                
                # Eliminar el archivo temporal
                os.unlink(temp_file.name)
                
                return {
                    "status": "success",
                    "transcript": transcript.text
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
