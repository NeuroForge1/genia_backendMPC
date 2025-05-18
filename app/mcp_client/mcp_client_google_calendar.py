"""
Cliente MCP para Google Calendar

Este módulo extiende el cliente MCP para soportar el servidor de Google Calendar,
permitiendo a GENIA interactuar con eventos de calendario de los usuarios.

Autor: GENIA Team
Fecha: Mayo 2025
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

# Importar orquestador de Google Calendar
from app.mcp_client.mcp_orchestrator_google_calendar import MCPOrchestratorGoogleCalendar

# Importar cliente Supabase
from app.services.supabase_service import get_supabase_client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_client_google_calendar")

class GoogleCalendarMCPClient:
    """
    Cliente MCP para Google Calendar.
    
    Esta clase proporciona métodos para interactuar con el servidor MCP de Google Calendar,
    permitiendo a GENIA gestionar eventos de calendario de los usuarios.
    """
    
    def __init__(self, orchestrator: MCPOrchestratorGoogleCalendar = None):
        """
        Inicializa el cliente MCP de Google Calendar.
        
        Args:
            orchestrator: Orquestador MCP de Google Calendar
        """
        self.orchestrator = orchestrator or MCPOrchestratorGoogleCalendar()
        logger.info("Cliente MCP de Google Calendar inicializado")
    
    async def save_user_tokens(self, user_id: str, tokens: Dict[str, Any]) -> bool:
        """
        Guarda los tokens de Google Calendar para un usuario en Supabase.
        
        Args:
            user_id: ID del usuario
            tokens: Tokens de Google Calendar (credentials, refresh_token, etc.)
        
        Returns:
            True si los tokens se guardaron correctamente, False en caso contrario
        """
        try:
            # Obtener cliente Supabase
            supabase = await get_supabase_client()
            
            # Verificar si ya existen tokens para este usuario y servicio
            response = await supabase.table("user_tokens").select("*").eq("user_id", user_id).eq("service", "google_calendar").execute()
            
            # Preparar datos
            token_data = {
                "user_id": user_id,
                "service": "google_calendar",
                "tokens": tokens,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if response.data and len(response.data) > 0:
                # Actualizar tokens existentes
                token_id = response.data[0]["id"]
                await supabase.table("user_tokens").update(token_data).eq("id", token_id).execute()
            else:
                # Insertar nuevos tokens
                token_data["created_at"] = datetime.utcnow().isoformat()
                await supabase.table("user_tokens").insert(token_data).execute()
            
            # También guardar credenciales en el sistema de archivos para el orquestador
            await self.orchestrator.save_user_credentials(user_id, tokens)
            
            logger.info(f"Tokens de Google Calendar guardados para el usuario {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error al guardar tokens de Google Calendar para el usuario {user_id}: {e}")
            return False
    
    async def load_user_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Carga los tokens de Google Calendar para un usuario desde Supabase.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Tokens de Google Calendar o None si no existen
        """
        try:
            # Obtener cliente Supabase
            supabase = await get_supabase_client()
            
            # Buscar tokens para este usuario y servicio
            response = await supabase.table("user_tokens").select("tokens").eq("user_id", user_id).eq("service", "google_calendar").execute()
            
            if not response.data or len(response.data) == 0:
                logger.warning(f"No existen tokens de Google Calendar para el usuario {user_id}")
                return None
            
            tokens = response.data[0]["tokens"]
            
            # Verificar si también existen credenciales en el sistema de archivos
            credentials = await self.orchestrator.load_user_credentials(user_id)
            if not credentials and tokens:
                # Si no existen en el sistema de archivos pero sí en Supabase, guardarlas
                await self.orchestrator.save_user_credentials(user_id, tokens)
            
            logger.info(f"Tokens de Google Calendar cargados para el usuario {user_id}")
            return tokens
        
        except Exception as e:
            logger.error(f"Error al cargar tokens de Google Calendar para el usuario {user_id}: {e}")
            return None
    
    async def delete_user_tokens(self, user_id: str) -> bool:
        """
        Elimina los tokens de Google Calendar para un usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            True si los tokens se eliminaron correctamente, False en caso contrario
        """
        try:
            # Obtener cliente Supabase
            supabase = await get_supabase_client()
            
            # Eliminar tokens de Supabase
            await supabase.table("user_tokens").delete().eq("user_id", user_id).eq("service", "google_calendar").execute()
            
            # Eliminar credenciales del sistema de archivos
            await self.orchestrator.delete_user_credentials(user_id)
            
            logger.info(f"Tokens de Google Calendar eliminados para el usuario {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error al eliminar tokens de Google Calendar para el usuario {user_id}: {e}")
            return False
    
    async def list_events(self, user_id: str, time_min: str = None, time_max: str = None, max_results: int = 10) -> Dict[str, Any]:
        """
        Lista eventos del calendario del usuario.
        
        Args:
            user_id: ID del usuario
            time_min: Fecha y hora mínima (formato ISO)
            time_max: Fecha y hora máxima (formato ISO)
            max_results: Número máximo de resultados
        
        Returns:
            Resultado de la operación con los eventos
        """
        # Verificar si existen tokens para el usuario
        tokens = await self.load_user_tokens(user_id)
        if not tokens:
            return {
                "status": "error",
                "error": "No existen tokens de Google Calendar para el usuario"
            }
        
        # Preparar argumentos
        if not time_min:
            # Por defecto, desde ahora
            time_min = datetime.utcnow().isoformat() + "Z"
        
        if not time_max:
            # Por defecto, una semana desde ahora
            time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        
        arguments = {
            "time_min": time_min,
            "time_max": time_max,
            "max_results": max_results
        }
        
        # Ejecutar operación
        result = await self.orchestrator.execute_operation(user_id, "list_events", arguments)
        return result
    
    async def create_event(self, user_id: str, summary: str, start: Dict[str, Any], end: Dict[str, Any], 
                          description: str = None, location: str = None, attendees: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Crea un nuevo evento en el calendario del usuario.
        
        Args:
            user_id: ID del usuario
            summary: Título del evento
            start: Fecha y hora de inicio (formato {"dateTime": "2025-05-20T10:00:00Z"})
            end: Fecha y hora de fin (formato {"dateTime": "2025-05-20T11:00:00Z"})
            description: Descripción del evento
            location: Ubicación del evento
            attendees: Lista de asistentes (formato [{"email": "ejemplo@gmail.com"}])
        
        Returns:
            Resultado de la operación con el evento creado
        """
        # Verificar si existen tokens para el usuario
        tokens = await self.load_user_tokens(user_id)
        if not tokens:
            return {
                "status": "error",
                "error": "No existen tokens de Google Calendar para el usuario"
            }
        
        # Preparar argumentos
        arguments = {
            "summary": summary,
            "start": start,
            "end": end
        }
        
        if description:
            arguments["description"] = description
        
        if location:
            arguments["location"] = location
        
        if attendees:
            arguments["attendees"] = attendees
        
        # Ejecutar operación
        result = await self.orchestrator.execute_operation(user_id, "create_event", arguments)
        return result
    
    async def update_event(self, user_id: str, event_id: str, summary: str = None, start: Dict[str, Any] = None, 
                          end: Dict[str, Any] = None, description: str = None, location: str = None, 
                          attendees: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Actualiza un evento existente en el calendario del usuario.
        
        Args:
            user_id: ID del usuario
            event_id: ID del evento a actualizar
            summary: Nuevo título del evento
            start: Nueva fecha y hora de inicio
            end: Nueva fecha y hora de fin
            description: Nueva descripción del evento
            location: Nueva ubicación del evento
            attendees: Nueva lista de asistentes
        
        Returns:
            Resultado de la operación con el evento actualizado
        """
        # Verificar si existen tokens para el usuario
        tokens = await self.load_user_tokens(user_id)
        if not tokens:
            return {
                "status": "error",
                "error": "No existen tokens de Google Calendar para el usuario"
            }
        
        # Preparar argumentos
        arguments = {
            "event_id": event_id
        }
        
        if summary:
            arguments["summary"] = summary
        
        if start:
            arguments["start"] = start
        
        if end:
            arguments["end"] = end
        
        if description:
            arguments["description"] = description
        
        if location:
            arguments["location"] = location
        
        if attendees:
            arguments["attendees"] = attendees
        
        # Ejecutar operación
        result = await self.orchestrator.execute_operation(user_id, "update_event", arguments)
        return result
    
    async def delete_event(self, user_id: str, event_id: str) -> Dict[str, Any]:
        """
        Elimina un evento del calendario del usuario.
        
        Args:
            user_id: ID del usuario
            event_id: ID del evento a eliminar
        
        Returns:
            Resultado de la operación
        """
        # Verificar si existen tokens para el usuario
        tokens = await self.load_user_tokens(user_id)
        if not tokens:
            return {
                "status": "error",
                "error": "No existen tokens de Google Calendar para el usuario"
            }
        
        # Preparar argumentos
        arguments = {
            "event_id": event_id
        }
        
        # Ejecutar operación
        result = await self.orchestrator.execute_operation(user_id, "delete_event", arguments)
        return result
    
    async def get_calendars(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene la lista de calendarios del usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Resultado de la operación con los calendarios
        """
        # Verificar si existen tokens para el usuario
        tokens = await self.load_user_tokens(user_id)
        if not tokens:
            return {
                "status": "error",
                "error": "No existen tokens de Google Calendar para el usuario"
            }
        
        # Ejecutar operación
        result = await self.orchestrator.execute_operation(user_id, "get_calendars", {})
        return result
    
    async def get_server_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado del servidor MCP de Google Calendar.
        
        Returns:
            Estado del servidor
        """
        return await self.orchestrator.get_status()
    
    async def start_server(self) -> bool:
        """
        Inicia el servidor MCP de Google Calendar.
        
        Returns:
            True si el servidor se inició correctamente, False en caso contrario
        """
        return await self.orchestrator.start_server()
    
    async def stop_server(self) -> bool:
        """
        Detiene el servidor MCP de Google Calendar.
        
        Returns:
            True si el servidor se detuvo correctamente, False en caso contrario
        """
        return await self.orchestrator.stop_server()
    
    async def restart_server(self) -> bool:
        """
        Reinicia el servidor MCP de Google Calendar.
        
        Returns:
            True si el servidor se reinició correctamente, False en caso contrario
        """
        return await self.orchestrator.restart_server()

# Instancia global del cliente
_google_calendar_client = None

async def get_google_calendar_client() -> GoogleCalendarMCPClient:
    """
    Obtiene una instancia del cliente MCP de Google Calendar.
    
    Returns:
        Cliente MCP de Google Calendar
    """
    global _google_calendar_client
    
    if _google_calendar_client is None:
        orchestrator = MCPOrchestratorGoogleCalendar()
        _google_calendar_client = GoogleCalendarMCPClient(orchestrator)
    
    return _google_calendar_client
