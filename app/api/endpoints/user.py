from fastapi import APIRouter, Depends
from typing import List

# from app.core.security import get_current_active_user # Descomentar si se requiere autenticación

router = APIRouter()

# Datos de ejemplo para las tareas
EXAMPLE_TASKS = [
    {"id": "task1", "name": "Tarea de ejemplo 1", "status": "completada"},
    {"id": "task2", "name": "Tarea de ejemplo 2", "status": "pendiente"}
]

@router.get("/tasks", response_model=List[dict]) # Usamos dict por simplicidad, idealmente un modelo Pydantic
async def get_user_tasks(
    page: int = 1,
    limit: int = 10,
    # current_user: dict = Depends(get_current_active_user) # Descomentar si se requiere autenticación
):
    """Devuelve una lista paginada de tareas del usuario (ejemplo)."""
    # Lógica de paginación simple para el ejemplo
    start = (page - 1) * limit
    end = start + limit
    return EXAMPLE_TASKS[start:end]

