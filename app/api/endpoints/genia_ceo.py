from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from app.core.security import get_current_active_user
from app.services.orchestrator import get_orchestrator
from pydantic import BaseModel

router = APIRouter()

class MCPRequest(BaseModel):
    intent: str
    params: Dict[str, Any]

@router.post("/process", summary="Procesa una solicitud MCP")
async def process_mcp_request(
    request: MCPRequest,
    current_user = Depends(get_current_active_user)
):
    """
    Procesa una solicitud MCP utilizando el orquestador de herramientas.
    
    - **intent**: Intención de la solicitud (ej: "enviar_mensaje", "generar_contenido")
    - **params**: Parámetros específicos para la herramienta
    """
    try:
        orchestrator = get_orchestrator()
        result = await orchestrator.process_request(
            user_id=current_user["id"],
            intent=request.intent,
            params=request.params
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/tools", summary="Obtiene las herramientas disponibles")
async def get_available_tools(current_user = Depends(get_current_active_user)):
    """
    Obtiene las herramientas disponibles para el usuario actual según su plan.
    """
    try:
        orchestrator = get_orchestrator()
        tools = await orchestrator.get_available_tools(current_user["id"])
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
