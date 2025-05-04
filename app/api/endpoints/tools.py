from fastapi import APIRouter, Depends
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

