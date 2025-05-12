from fastapi import APIRouter, Depends, HTTPException
import uuid
import datetime
import json # Para logs o debugging si es necesario

# Importar la instancia global del MCPClient
from app.mcp_client.client import mcp_client_instance

from typing import List
from app.models.tool import Tool  # Asumiendo que existe un modelo Pydantic Tool
from app.core.security import get_current_active_user # Asumiendo dependencia de usuario

router = APIRouter()

# Datos de ejemplo para las herramientas
# En una implementación real, esto vendría de una base de datos o configuración
EXAMPLE_TOOLS = [
    {
        "id": "openai_chat",
        "name": "Chat con OpenAI",
        "description": "Genera texto y responde preguntas usando modelos de OpenAI.",
        "icon": "🤖", # Placeholder icon
        "category": "Generación de Texto",
        "endpoint": "/api/v1/genia/openai/chat" # Endpoint de ejemplo
    },
    {
        "id": "stripe_payment",
        "name": "Procesador de Pagos Stripe",
        "description": "Gestiona suscripciones y pagos.",
        "icon": "💳", # Placeholder icon
        "category": "Utilidades",
        "endpoint": None # No es una herramienta de acción directa para el usuario final
    },
    {
        "id": "whatsapp_messaging",
        "name": "Mensajería WhatsApp",
        "description": "Envía mensajes a través de WhatsApp.",
        "icon": "💬", # Placeholder icon
        "category": "Comunicación",
        "endpoint": None # Endpoint podría ser interno o no expuesto directamente
    }
]

@router.get("/", response_model=List[Tool])
async def get_available_tools(
    # current_user: dict = Depends(get_current_active_user) # Descomentar si se requiere autenticación
):
    """Devuelve la lista de herramientas disponibles para el usuario."""
    # Aquí se podría añadir lógica para filtrar herramientas según el plan del usuario, etc.
    # Por ahora, devolvemos la lista de ejemplo.
    # Convertir los diccionarios a instancias del modelo Tool si es necesario
    # Esto depende de cómo esté definido el modelo Tool
    # return [Tool(**tool_data) for tool_data in EXAMPLE_TOOLS]
    # Por simplicidad, devolvemos los diccionarios directamente si el frontend puede manejarlos
    return EXAMPLE_TOOLS

@router.post("/test-schedule-email", summary="Test scheduling an email via MCP Scheduler")
async def test_schedule_email_via_mcp():
    """
    Endpoint de prueba para verificar que genia_backendMPC puede programar una tarea
    de envío de correo a través del MCP de Programación.
    """
    try:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        # Programar para 2 minutos en el futuro para tener tiempo de revisar logs
        scheduled_time_dt = now_utc + datetime.timedelta(minutes=2)
        scheduled_at_utc_iso = scheduled_time_dt.isoformat()

        email_content_details = {
            "to_recipients": [
                {"email": "test_from_backend_endpoint@example.com", "name": "Backend Test Recipient"}
            ],
            "subject": "TEST: Scheduled Email via BackendMPC -> Scheduler -> EmailMCP",
            "body_html": "<h1>Hello from BackendMPC Endpoint!</h1><p>This email was scheduled via a test endpoint in BackendMPC, processed by SchedulerMCP, and (hopefully) sent by EmailMCP.</p>",
            "from_address": "noreply_backend_test@genia.systems"
        }
        mcp_email_request_body = {
            "role": "user",
            "content": email_content_details,
            "metadata": {"source": "genia_backendMPC_test_endpoint"}
        }
        
        task_data_to_schedule = {
            "genia_user_id": str(uuid.uuid4()), 
            "platform_identifier": {
                "platform_name": "email",
                "account_id": "backend_user_for_email_task_via_endpoint"
            },
            "scheduled_at_utc": scheduled_at_utc_iso,
            "task_payload": {
                "mcp_target_endpoint": "/mcp/send_email", # Endpoint en el EmailMCP
                "mcp_request_body": mcp_email_request_body, # Payload para el EmailMCP
                "user_platform_tokens": { 
                    "service_auth_key": "email_mcp_internal_key_placeholder"
                }
            },
            "task_type": "email_test_from_backend_endpoint"
        }

        # Usar la instancia mcp_client_instance para llamar al método schedule_task
        # El método schedule_task ya está en el client.py que subiste.
        scheduler_response = await mcp_client_instance.schedule_task(task_data_to_schedule)
        
        return {
            "message": "Solicitud de programación de tarea enviada al MCP de Programación.",
            "scheduled_task_details_from_backend": task_data_to_schedule,
            "scheduler_mcp_response": scheduler_response
        }

    except ConnectionError as ce:
        # Errores de conexión o HTTP del MCPClient
        raise HTTPException(status_code=503, detail=f"Error de comunicación con el MCP de Programación: {str(ce)}")
    except ValueError as ve:
        # Errores de configuración (ej. URL o Token no encontrados)
        raise HTTPException(status_code=500, detail=f"Error de configuración interna para el MCP de Programación: {str(ve)}")
    except Exception as e:
        # Otros errores inesperados
        # Loggear el error real en un sistema de producción
        # logger.exception("Error inesperado al intentar programar la tarea de prueba") 
        raise HTTPException(status_code=500, detail=f"Error interno inesperado en genia_backendMPC: {str(e)}")

