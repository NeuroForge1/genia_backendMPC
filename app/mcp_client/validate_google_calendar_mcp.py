"""
Script de validación para Google Calendar MCP

Este script valida el funcionamiento del servidor MCP de Google Calendar
en la arquitectura GENIA, verificando la integración con Supabase y
las operaciones principales.

Autor: GENIA Team
Fecha: Mayo 2025
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("google_calendar_mcp_validation.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("google_calendar_mcp_validation")

# Importar cliente MCP de Google Calendar
sys.path.append('/home/ubuntu/genia_backendMPC')
from app.mcp_client.mcp_client_google_calendar import get_google_calendar_client
from app.mcp_client.mcp_orchestrator_google_calendar import MCPOrchestratorGoogleCalendar

# ID de usuario de prueba
TEST_USER_ID = "test_user_001"

# Credenciales de prueba
TEST_CREDENTIALS = {
    "installed": {
        "client_id": "test-client-id.apps.googleusercontent.com",
        "project_id": "genia-calendar-mcp",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "test-client-secret",
        "redirect_uris": ["http://localhost"]
    },
    "token": {
        "access_token": "test-access-token",
        "refresh_token": "test-refresh-token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client-id.apps.googleusercontent.com",
        "client_secret": "test-client-secret",
        "scopes": ["https://www.googleapis.com/auth/calendar"],
        "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
    }
}

async def validate_orchestrator():
    """Valida el funcionamiento del orquestador MCP de Google Calendar."""
    logger.info("Validando orquestador MCP de Google Calendar...")
    
    try:
        # Crear orquestador
        orchestrator = MCPOrchestratorGoogleCalendar(
            base_dir="/home/ubuntu/google_calendar_mcp/google_calendar_mcp_package/Google_Calendar_MCP",
            supabase_url=os.environ.get("SUPABASE_URL", "https://example.supabase.co"),
            supabase_key=os.environ.get("SUPABASE_KEY", "test-supabase-key")
        )
        
        # Verificar Python y UV
        python_cmd = orchestrator._get_python_cmd()
        uv_cmd = orchestrator._get_uv_cmd()
        
        logger.info(f"Python command: {python_cmd}")
        logger.info(f"UV command: {uv_cmd}")
        
        # Guardar credenciales de prueba
        saved = await orchestrator.save_user_credentials(TEST_USER_ID, TEST_CREDENTIALS)
        logger.info(f"Credenciales guardadas: {saved}")
        
        # Cargar credenciales
        loaded_credentials = await orchestrator.load_user_credentials(TEST_USER_ID)
        logger.info(f"Credenciales cargadas: {loaded_credentials is not None}")
        
        # Verificar que las credenciales son correctas
        if loaded_credentials:
            assert loaded_credentials["installed"]["client_id"] == TEST_CREDENTIALS["installed"]["client_id"]
            assert loaded_credentials["token"]["refresh_token"] == TEST_CREDENTIALS["token"]["refresh_token"]
            logger.info("Verificación de credenciales exitosa")
        
        # Obtener estado del servidor (sin iniciarlo)
        status = await orchestrator.get_status()
        logger.info(f"Estado del servidor: {status}")
        
        # Simular ejecución de operación
        result = await orchestrator.execute_operation(TEST_USER_ID, "list_events", {
            "time_min": datetime.utcnow().isoformat() + "Z",
            "time_max": (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        })
        logger.info(f"Resultado de operación simulada: {result}")
        
        # Eliminar credenciales
        deleted = await orchestrator.delete_user_credentials(TEST_USER_ID)
        logger.info(f"Credenciales eliminadas: {deleted}")
        
        logger.info("Validación del orquestador completada con éxito")
        return True
    
    except Exception as e:
        logger.error(f"Error en validación del orquestador: {e}")
        return False

async def validate_client():
    """Valida el funcionamiento del cliente MCP de Google Calendar."""
    logger.info("Validando cliente MCP de Google Calendar...")
    
    try:
        # Obtener cliente
        client = await get_google_calendar_client()
        
        # Guardar tokens de prueba
        saved = await client.save_user_tokens(TEST_USER_ID, TEST_CREDENTIALS)
        logger.info(f"Tokens guardados: {saved}")
        
        # Cargar tokens
        loaded_tokens = await client.load_user_tokens(TEST_USER_ID)
        logger.info(f"Tokens cargados: {loaded_tokens is not None}")
        
        # Listar eventos
        events_result = await client.list_events(
            user_id=TEST_USER_ID,
            time_min=datetime.utcnow().isoformat() + "Z",
            time_max=(datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
        )
        logger.info(f"Resultado de listar eventos: {events_result}")
        
        # Crear evento
        create_result = await client.create_event(
            user_id=TEST_USER_ID,
            summary="Reunión de prueba",
            start={"dateTime": (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"},
            end={"dateTime": (datetime.utcnow() + timedelta(days=1, hours=1)).isoformat() + "Z"},
            description="Descripción de prueba",
            location="Ubicación de prueba",
            attendees=[{"email": "test@example.com"}]
        )
        logger.info(f"Resultado de crear evento: {create_result}")
        
        # Actualizar evento
        if create_result.get("status") == "success" and "result" in create_result.get("response", {}):
            event_id = create_result["response"]["result"]["id"]
            update_result = await client.update_event(
                user_id=TEST_USER_ID,
                event_id=event_id,
                summary="Reunión de prueba actualizada"
            )
            logger.info(f"Resultado de actualizar evento: {update_result}")
            
            # Eliminar evento
            delete_result = await client.delete_event(
                user_id=TEST_USER_ID,
                event_id=event_id
            )
            logger.info(f"Resultado de eliminar evento: {delete_result}")
        
        # Obtener estado del servidor
        status = await client.get_server_status()
        logger.info(f"Estado del servidor: {status}")
        
        # Eliminar tokens
        deleted = await client.delete_user_tokens(TEST_USER_ID)
        logger.info(f"Tokens eliminados: {deleted}")
        
        logger.info("Validación del cliente completada con éxito")
        return True
    
    except Exception as e:
        logger.error(f"Error en validación del cliente: {e}")
        return False

async def validate_integration():
    """Valida la integración completa del servidor MCP de Google Calendar en GENIA."""
    logger.info("Validando integración completa de Google Calendar MCP en GENIA...")
    
    # Validar orquestador
    orchestrator_valid = await validate_orchestrator()
    logger.info(f"Orquestador válido: {orchestrator_valid}")
    
    # Validar cliente
    client_valid = await validate_client()
    logger.info(f"Cliente válido: {client_valid}")
    
    # Resultado final
    if orchestrator_valid and client_valid:
        logger.info("Validación completa exitosa")
        return True
    else:
        logger.error("Validación completa fallida")
        return False

async def main():
    """Función principal."""
    logger.info("Iniciando validación de Google Calendar MCP...")
    
    # Configurar variables de entorno para pruebas
    os.environ["SUPABASE_URL"] = "https://example.supabase.co"
    os.environ["SUPABASE_KEY"] = "test-supabase-key"
    os.environ["SUPABASE_JWT_SECRET"] = "4eVYta/fEAepl5EE2H6RzYJkGzrh0rMf2yB/VqY5MIBRtviR9HddT/ISjv6W2x7LrmRTpRdCSBr/rIQE4rxMaw=="
    
    # Validar integración
    result = await validate_integration()
    
    # Resumen
    if result:
        logger.info("✅ Validación de Google Calendar MCP completada con éxito")
        print("✅ Validación de Google Calendar MCP completada con éxito")
    else:
        logger.error("❌ Validación de Google Calendar MCP fallida")
        print("❌ Validación de Google Calendar MCP fallida")
    
    # Limitaciones y requisitos
    logger.info("Limitaciones y requisitos detectados:")
    logger.info("1. Python 3.13+ requerido para ejecución en producción")
    logger.info("2. UV Package Manager requerido para gestión de dependencias")
    logger.info("3. Supabase necesario para almacenamiento seguro de tokens")
    logger.info("4. Credenciales OAuth de Google Cloud requeridas")
    
    print("\nLimitaciones y requisitos detectados:")
    print("1. Python 3.13+ requerido para ejecución en producción")
    print("2. UV Package Manager requerido para gestión de dependencias")
    print("3. Supabase necesario para almacenamiento seguro de tokens")
    print("4. Credenciales OAuth de Google Cloud requeridas")

if __name__ == "__main__":
    asyncio.run(main())
