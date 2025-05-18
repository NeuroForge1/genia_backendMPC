"""
Servicio de Supabase para GENIA

Este módulo proporciona funciones para interactuar con Supabase,
permitiendo la gestión segura de tokens y credenciales de usuario.

Autor: GENIA Team
Fecha: Mayo 2025
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

# Importar cliente Supabase
try:
    from supabase import create_client, Client
except ImportError:
    logging.warning("Supabase Python SDK no instalado. Instalando...")
    import subprocess
    subprocess.check_call(["pip", "install", "supabase"])
    from supabase import create_client, Client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("supabase_service")

# Cliente global de Supabase
_supabase_client = None

async def get_supabase_client() -> Client:
    """
    Obtiene una instancia del cliente de Supabase.
    
    Returns:
        Cliente de Supabase
    """
    global _supabase_client
    
    if _supabase_client is None:
        # Obtener URL y clave de Supabase
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.error("Variables de entorno SUPABASE_URL y SUPABASE_KEY no configuradas")
            raise ValueError("Variables de entorno SUPABASE_URL y SUPABASE_KEY no configuradas")
        
        # Crear cliente
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info(f"Cliente Supabase inicializado para {supabase_url}")
    
    return _supabase_client

async def save_user_tokens(user_id: str, service: str, tokens: Dict[str, Any]) -> bool:
    """
    Guarda los tokens de un servicio para un usuario en Supabase.
    
    Args:
        user_id: ID del usuario
        service: Nombre del servicio (github, notion, slack, etc.)
        tokens: Tokens del servicio
    
    Returns:
        True si los tokens se guardaron correctamente, False en caso contrario
    """
    try:
        # Obtener cliente Supabase
        supabase = await get_supabase_client()
        
        # Verificar si ya existen tokens para este usuario y servicio
        response = await supabase.table("user_tokens").select("*").eq("user_id", user_id).eq("service", service).execute()
        
        # Preparar datos
        token_data = {
            "user_id": user_id,
            "service": service,
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
        
        logger.info(f"Tokens de {service} guardados para el usuario {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error al guardar tokens de {service} para el usuario {user_id}: {e}")
        return False

async def load_user_tokens(user_id: str, service: str) -> Optional[Dict[str, Any]]:
    """
    Carga los tokens de un servicio para un usuario desde Supabase.
    
    Args:
        user_id: ID del usuario
        service: Nombre del servicio (github, notion, slack, etc.)
    
    Returns:
        Tokens del servicio o None si no existen
    """
    try:
        # Obtener cliente Supabase
        supabase = await get_supabase_client()
        
        # Buscar tokens para este usuario y servicio
        response = await supabase.table("user_tokens").select("tokens").eq("user_id", user_id).eq("service", service).execute()
        
        if not response.data or len(response.data) == 0:
            logger.warning(f"No existen tokens de {service} para el usuario {user_id}")
            return None
        
        tokens = response.data[0]["tokens"]
        logger.info(f"Tokens de {service} cargados para el usuario {user_id}")
        return tokens
    
    except Exception as e:
        logger.error(f"Error al cargar tokens de {service} para el usuario {user_id}: {e}")
        return None

async def delete_user_tokens(user_id: str, service: str) -> bool:
    """
    Elimina los tokens de un servicio para un usuario.
    
    Args:
        user_id: ID del usuario
        service: Nombre del servicio (github, notion, slack, etc.)
    
    Returns:
        True si los tokens se eliminaron correctamente, False en caso contrario
    """
    try:
        # Obtener cliente Supabase
        supabase = await get_supabase_client()
        
        # Eliminar tokens
        await supabase.table("user_tokens").delete().eq("user_id", user_id).eq("service", service).execute()
        
        logger.info(f"Tokens de {service} eliminados para el usuario {user_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error al eliminar tokens de {service} para el usuario {user_id}: {e}")
        return False

async def get_user_services(user_id: str) -> List[str]:
    """
    Obtiene la lista de servicios conectados por un usuario.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Lista de servicios conectados
    """
    try:
        # Obtener cliente Supabase
        supabase = await get_supabase_client()
        
        # Buscar servicios para este usuario
        response = await supabase.table("user_tokens").select("service").eq("user_id", user_id).execute()
        
        if not response.data:
            return []
        
        services = [item["service"] for item in response.data]
        logger.info(f"Servicios conectados para el usuario {user_id}: {services}")
        return services
    
    except Exception as e:
        logger.error(f"Error al obtener servicios para el usuario {user_id}: {e}")
        return []

async def create_tables_if_not_exist() -> bool:
    """
    Crea las tablas necesarias en Supabase si no existen.
    
    Returns:
        True si las tablas se crearon correctamente, False en caso contrario
    """
    try:
        # Obtener cliente Supabase
        supabase = await get_supabase_client()
        
        # Verificar si la tabla user_tokens existe
        try:
            await supabase.table("user_tokens").select("count").limit(1).execute()
            logger.info("Tabla user_tokens ya existe")
        except Exception:
            # Crear tabla user_tokens
            # Nota: En realidad, la creación de tablas se hace desde la interfaz de Supabase
            # o mediante migraciones SQL. Aquí solo simulamos la verificación.
            logger.warning("Tabla user_tokens no existe. Debe crearla manualmente en Supabase")
            logger.info("SQL para crear tabla: CREATE TABLE user_tokens (id uuid PRIMARY KEY DEFAULT uuid_generate_v4(), user_id text NOT NULL, service text NOT NULL, tokens jsonb NOT NULL, created_at timestamp with time zone DEFAULT now(), updated_at timestamp with time zone DEFAULT now());")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error al verificar/crear tablas en Supabase: {e}")
        return False

# Función para simular el funcionamiento en entornos de prueba
async def setup_mock_supabase():
    """
    Configura un entorno simulado de Supabase para pruebas.
    
    Esta función permite ejecutar pruebas sin una conexión real a Supabase.
    """
    global _supabase_client
    
    class MockSupabaseTable:
        def __init__(self, name):
            self.name = name
            self.data = []
        
        def select(self, *fields):
            self.fields = fields
            return self
        
        def eq(self, field, value):
            self.filter_field = field
            self.filter_value = value
            return self
        
        def limit(self, limit):
            self.limit_value = limit
            return self
        
        def insert(self, data):
            return self
        
        def update(self, data):
            return self
        
        def delete(self):
            return self
        
        async def execute(self):
            # Simular respuesta
            if hasattr(self, 'filter_field') and self.filter_field == "user_id":
                if self.name == "user_tokens":
                    return type('obj', (object,), {
                        'data': [
                            {
                                "id": "mock-id",
                                "user_id": self.filter_value,
                                "service": "google_calendar",
                                "tokens": {
                                    "access_token": "mock-access-token",
                                    "refresh_token": "mock-refresh-token"
                                }
                            }
                        ]
                    })
            
            return type('obj', (object,), {'data': []})
    
    class MockSupabaseClient:
        def table(self, name):
            return MockSupabaseTable(name)
    
    _supabase_client = MockSupabaseClient()
    logger.info("Cliente Supabase simulado configurado para pruebas")

# Inicialización
async def init_supabase():
    """
    Inicializa el servicio de Supabase.
    
    Esta función debe llamarse al inicio de la aplicación.
    """
    try:
        # Verificar variables de entorno
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("Variables de entorno SUPABASE_URL y SUPABASE_KEY no configuradas")
            logger.warning("Configurando cliente Supabase simulado para pruebas")
            await setup_mock_supabase()
            return False
        
        # Obtener cliente
        await get_supabase_client()
        
        # Verificar/crear tablas
        tables_ok = await create_tables_if_not_exist()
        
        return tables_ok
    
    except Exception as e:
        logger.error(f"Error al inicializar servicio Supabase: {e}")
        logger.warning("Configurando cliente Supabase simulado para pruebas")
        await setup_mock_supabase()
        return False
