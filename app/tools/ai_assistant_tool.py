import os
import httpx
from typing import Dict, Any, Optional, List
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

class AIAssistantTool(BaseTool):
    """
    Herramienta para crear y gestionar asistentes de IA personalizados
    """
    def __init__(self):
        super().__init__(
            name="ai_assistant",
            description="Creación y gestión de asistentes de IA personalizados"
        )
        
        # Registrar capacidades
        self.register_capability(
            name="create_assistant",
            description="Crea un asistente de IA personalizado",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "instructions": {"type": "string"},
                    "tools": {"type": "array", "items": {"type": "string"}, "default": ["code_interpreter"]},
                    "model": {"type": "string", "default": "gpt-4"}
                },
                "required": ["name", "instructions"]
            }
        )
        
        self.register_capability(
            name="create_thread",
            description="Crea un hilo de conversación para un asistente",
            schema={
                "type": "object",
                "properties": {
                    "assistant_id": {"type": "string"},
                    "messages": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["assistant_id"]
            }
        )
        
        self.register_capability(
            name="add_message",
            description="Añade un mensaje a un hilo de conversación",
            schema={
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string"},
                    "content": {"type": "string"},
                    "role": {"type": "string", "default": "user"}
                },
                "required": ["thread_id", "content"]
            }
        )
        
        self.register_capability(
            name="run_assistant",
            description="Ejecuta un asistente en un hilo de conversación",
            schema={
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string"},
                    "assistant_id": {"type": "string"},
                    "instructions": {"type": "string"}
                },
                "required": ["thread_id", "assistant_id"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta AIAssistant
        """
        if capability == "create_assistant":
            return await self._create_assistant(user_id, params)
        elif capability == "create_thread":
            return await self._create_thread(user_id, params)
        elif capability == "add_message":
            return await self._add_message(user_id, params)
        elif capability == "run_assistant":
            return await self._run_assistant(user_id, params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")
    
    async def _create_assistant(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un asistente de IA personalizado utilizando la API de OpenAI
        """
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            
            # Crear el asistente
            assistant = await openai.beta.assistants.create(
                name=params["name"],
                description=params.get("description", ""),
                instructions=params["instructions"],
                tools=[{"type": tool} for tool in params.get("tools", ["code_interpreter"])],
                model=params.get("model", "gpt-4")
            )
            
            # Guardar el asistente en Supabase
            supabase = get_supabase_client()
            assistant_data = {
                "user_id": user_id,
                "assistant_id": assistant.id,
                "name": params["name"],
                "description": params.get("description", ""),
                "instructions": params["instructions"],
                "tools": params.get("tools", ["code_interpreter"]),
                "model": params.get("model", "gpt-4"),
                "created_at": "now()"
            }
            
            # Insertar en una tabla de asistentes (que debería existir en Supabase)
            # En una implementación real, esto se haría con una función específica en SupabaseManager
            response = supabase.client.table("asistentes").insert(assistant_data).execute()
            
            return {
                "status": "success",
                "assistant_id": assistant.id,
                "name": assistant.name,
                "model": assistant.model
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _create_thread(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un hilo de conversación para un asistente
        """
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            
            # Verificar que el asistente pertenece al usuario
            supabase = get_supabase_client()
            response = supabase.client.table("asistentes").select("*").eq("user_id", user_id).eq("assistant_id", params["assistant_id"]).execute()
            
            if not response.data:
                return {"status": "error", "message": "Asistente no encontrado o no pertenece al usuario"}
            
            # Crear mensajes iniciales si se proporcionan
            messages = []
            if "messages" in params and params["messages"]:
                for msg in params["messages"]:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg["content"]
                    })
            
            # Crear el hilo
            thread = await openai.beta.threads.create(
                messages=messages if messages else None
            )
            
            # Guardar el hilo en Supabase
            thread_data = {
                "user_id": user_id,
                "thread_id": thread.id,
                "assistant_id": params["assistant_id"],
                "created_at": "now()"
            }
            
            # Insertar en una tabla de hilos (que debería existir en Supabase)
            response = supabase.client.table("hilos_conversacion").insert(thread_data).execute()
            
            return {
                "status": "success",
                "thread_id": thread.id,
                "assistant_id": params["assistant_id"]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _add_message(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Añade un mensaje a un hilo de conversación
        """
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            
            # Verificar que el hilo pertenece al usuario
            supabase = get_supabase_client()
            response = supabase.client.table("hilos_conversacion").select("*").eq("user_id", user_id).eq("thread_id", params["thread_id"]).execute()
            
            if not response.data:
                return {"status": "error", "message": "Hilo no encontrado o no pertenece al usuario"}
            
            # Añadir mensaje al hilo
            message = await openai.beta.threads.messages.create(
                thread_id=params["thread_id"],
                role=params.get("role", "user"),
                content=params["content"]
            )
            
            return {
                "status": "success",
                "message_id": message.id,
                "thread_id": params["thread_id"],
                "content": params["content"]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _run_assistant(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta un asistente en un hilo de conversación
        """
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            
            # Verificar que el hilo y el asistente pertenecen al usuario
            supabase = get_supabase_client()
            thread_response = supabase.client.table("hilos_conversacion").select("*").eq("user_id", user_id).eq("thread_id", params["thread_id"]).execute()
            
            if not thread_response.data:
                return {"status": "error", "message": "Hilo no encontrado o no pertenece al usuario"}
            
            assistant_response = supabase.client.table("asistentes").select("*").eq("user_id", user_id).eq("assistant_id", params["assistant_id"]).execute()
            
            if not assistant_response.data:
                return {"status": "error", "message": "Asistente no encontrado o no pertenece al usuario"}
            
            # Crear y ejecutar el run
            run = await openai.beta.threads.runs.create(
                thread_id=params["thread_id"],
                assistant_id=params["assistant_id"],
                instructions=params.get("instructions", None)
            )
            
            # Esperar a que el run se complete (en una implementación real, esto se haría de forma asíncrona)
            import time
            run_status = "queued"
            max_wait_time = 60  # segundos
            start_time = time.time()
            
            while run_status in ["queued", "in_progress"]:
                if time.time() - start_time > max_wait_time:
                    return {"status": "timeout", "message": "La ejecución del asistente está tomando demasiado tiempo"}
                
                # Esperar un poco antes de verificar el estado
                time.sleep(2)
                
                # Obtener el estado actual
                run = await openai.beta.threads.runs.retrieve(
                    thread_id=params["thread_id"],
                    run_id=run.id
                )
                run_status = run.status
            
            # Obtener los mensajes generados
            messages = await openai.beta.threads.messages.list(
                thread_id=params["thread_id"]
            )
            
            # Filtrar solo los mensajes del asistente y ordenarlos por fecha
            assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
            assistant_messages.sort(key=lambda x: x.created_at, reverse=True)
            
            # Extraer el contenido de los mensajes
            message_contents = []
            for msg in assistant_messages[:5]:  # Obtener los 5 mensajes más recientes
                for content_item in msg.content:
                    if content_item.type == "text":
                        message_contents.append(content_item.text.value)
            
            return {
                "status": "success",
                "run_id": run.id,
                "run_status": run.status,
                "thread_id": params["thread_id"],
                "assistant_id": params["assistant_id"],
                "messages": message_contents
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
