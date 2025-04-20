from supabase import create_client, Client
from typing import Dict, List, Optional, Any
from app.core.config import settings
import asyncio
import httpx

class SupabaseManager:
    """
    Clase para gestionar la conexión y operaciones con Supabase
    """
    def __init__(self):
        self.client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        self.service_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su ID
        """
        try:
            response = self.client.table("usuarios").select("*").eq("id", user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error al obtener usuario: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo usuario en la base de datos
        """
        try:
            response = self.client.table("usuarios").insert(user_data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise Exception("Error al crear usuario")
        except Exception as e:
            print(f"Error al crear usuario: {e}")
            raise
    
    async def update_user(self, user_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza los datos de un usuario
        """
        try:
            response = self.client.table("usuarios").update(user_data).eq("id", user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise Exception("Error al actualizar usuario")
        except Exception as e:
            print(f"Error al actualizar usuario: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un usuario por su email
        """
        try:
            response = self.client.table("usuarios").select("*").eq("email", email).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error al obtener usuario por email: {e}")
            return None
    
    async def register_task(self, user_id: str, tool: str, capability: str, params: Dict[str, Any], result: Dict[str, Any], credits_used: int) -> Dict[str, Any]:
        """
        Registra una tarea ejecutada por un usuario
        """
        task_data = {
            "user_id": user_id,
            "herramienta": tool,
            "capability": capability,
            "params": params,
            "resultado": result,
            "creditos_consumidos": credits_used,
            "fecha": "now()"
        }
        
        try:
            response = self.client.table("tareas_generadas").insert(task_data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            raise Exception("Error al registrar tarea")
        except Exception as e:
            print(f"Error al registrar tarea: {e}")
            raise
    
    async def deduct_credits(self, user_id: str, credits: int) -> bool:
        """
        Descuenta créditos a un usuario
        """
        try:
            # Primero obtenemos el usuario para verificar sus créditos actuales
            user = await self.get_user(user_id)
            if not user:
                raise Exception("Usuario no encontrado")
            
            current_credits = user.get("creditos", 0)
            if current_credits < credits:
                raise Exception("Créditos insuficientes")
            
            # Actualizamos los créditos
            new_credits = current_credits - credits
            await self.update_user(user_id, {"creditos": new_credits})
            return True
        except Exception as e:
            print(f"Error al descontar créditos: {e}")
            raise
    
    async def get_available_tools(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene las herramientas disponibles para un usuario según su plan
        """
        try:
            # Obtenemos el usuario para verificar su plan
            user = await self.get_user(user_id)
            if not user:
                raise Exception("Usuario no encontrado")
            
            plan = user.get("plan", "free")
            
            # Obtenemos las herramientas disponibles para el plan
            response = self.client.table("herramientas_disponibles").select("*").eq("plan_minimo", plan).execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"Error al obtener herramientas disponibles: {e}")
            return []
    
    async def store_oauth_tokens(self, user_id: str, service: str, tokens: Dict[str, Any]) -> Dict[str, Any]:
        """
        Almacena tokens de OAuth para un servicio
        """
        token_data = {
            "user_id": user_id,
            "servicio": service,
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token", ""),
            "expiracion": tokens.get("expires_at", ""),
            "estado": True
        }
        
        try:
            # Verificamos si ya existe un registro para este usuario y servicio
            response = self.client.table("herramientas_conectadas").select("*").eq("user_id", user_id).eq("servicio", service).execute()
            
            if response.data and len(response.data) > 0:
                # Actualizamos el registro existente
                token_id = response.data[0]["id"]
                update_response = self.client.table("herramientas_conectadas").update(token_data).eq("id", token_id).execute()
                if update_response.data and len(update_response.data) > 0:
                    return update_response.data[0]
            else:
                # Creamos un nuevo registro
                insert_response = self.client.table("herramientas_conectadas").insert(token_data).execute()
                if insert_response.data and len(insert_response.data) > 0:
                    return insert_response.data[0]
            
            raise Exception("Error al almacenar tokens")
        except Exception as e:
            print(f"Error al almacenar tokens: {e}")
            raise
    
    async def get_oauth_tokens(self, user_id: str, service: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene tokens de OAuth para un servicio
        """
        try:
            response = self.client.table("herramientas_conectadas").select("*").eq("user_id", user_id).eq("servicio", service).eq("estado", True).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error al obtener tokens: {e}")
            return None

# Singleton para el cliente de Supabase
_supabase_client = None

def get_supabase_client() -> SupabaseManager:
    """
    Devuelve una instancia del cliente de Supabase
    """
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseManager()
    return _supabase_client
