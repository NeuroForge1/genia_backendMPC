"""
Endpoints API para MCP en GENIA

Este módulo proporciona endpoints REST para interactuar con todos los servidores MCP
integrados en GENIA. Permite a los usuarios conectar sus propias cuentas de servicios
externos y ejecutar operaciones a través de una interfaz unificada.

Autor: GENIA Team
Fecha: Mayo 2025
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Importar servicios MCP
from app.services.mcp_service import execute_tool_operation, initialize_mcp
from app.mcp_client.mcp_client_extended import get_mcp_client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_routes")

# Crear router
router = APIRouter(prefix="/api/mcp", tags=["MCP"])

# Modelos de datos
class ConnectionStatus(BaseModel):
    service: str
    connected: bool
    last_connected: Optional[str] = None

class ConnectionResponse(BaseModel):
    connections: Dict[str, bool]
    message: str

class TokenRequest(BaseModel):
    token: str = Field(..., description="Token personal de acceso")

class SlackTokenRequest(BaseModel):
    xoxc_token: str = Field(..., description="Token xoxc de Slack")
    xoxd_token: str = Field(..., description="Token xoxd de Slack")

class GoogleTokenRequest(BaseModel):
    client_id: str = Field(..., description="Client ID de Google")
    client_secret: str = Field(..., description="Client Secret de Google")
    refresh_token: str = Field(..., description="Refresh Token de Google")
    access_token: Optional[str] = Field(None, description="Access Token de Google (opcional)")

class InstagramTokenRequest(BaseModel):
    session_id: str = Field(..., description="Session ID de Instagram")
    csrf_token: str = Field(..., description="CSRF Token de Instagram")
    ds_user_id: str = Field(..., description="DS User ID de Instagram")

class TrelloTokenRequest(BaseModel):
    api_key: str = Field(..., description="API Key de Trello")
    token: str = Field(..., description="Token de Trello")
    board_id: Optional[str] = Field(None, description="ID del tablero principal (opcional)")

class TwitterTokenRequest(BaseModel):
    api_key: str = Field(..., description="API Key de Twitter/X")
    api_secret: str = Field(..., description="API Secret de Twitter/X")
    access_token: str = Field(..., description="Access Token de Twitter/X")
    access_secret: str = Field(..., description="Access Secret de Twitter/X")

class OperationRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Argumentos para la operación")

class ServerStatus(BaseModel):
    name: str
    status: str
    running: bool
    pid: Optional[int] = None
    uptime: Optional[float] = None

# Endpoints de conexión
@router.get("/connections", response_model=ConnectionResponse)
async def get_connections(user_id: str = Depends(get_current_user_id)):
    """
    Obtiene las conexiones activas del usuario.
    """
    try:
        client = await get_mcp_client()
        connections = {}
        
        # Verificar cada servicio
        services = ["github", "notion", "slack", "google_workspace", "instagram", "trello", "twitter_x"]
        for service in services:
            tokens = await client.load_user_tokens(user_id, service)
            connections[service] = tokens is not None and len(tokens) > 0
        
        return {
            "connections": connections,
            "message": "Conexiones obtenidas correctamente"
        }
    except Exception as e:
        logger.error(f"Error al obtener conexiones: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener conexiones: {str(e)}")

@router.post("/connect/github", response_model=dict)
async def connect_github(token_request: TokenRequest, user_id: str = Depends(get_current_user_id)):
    """
    Conecta una cuenta de GitHub.
    """
    try:
        client = await get_mcp_client()
        result = await client.save_user_tokens(
            user_id=user_id,
            service="github",
            tokens={"token": token_request.token}
        )
        
        if result:
            # Verificar token con una operación simple
            try:
                response = await client.execute_github_operation(
                    user_id=user_id,
                    operation="get_me",
                    arguments={}
                )
                return {
                    "status": "success",
                    "message": "Cuenta de GitHub conectada correctamente",
                    "user_info": response.get("response", {}).get("result", {})
                }
            except Exception as e:
                # Si falla la verificación, eliminar el token guardado
                await client.delete_user_tokens(user_id, "github")
                raise HTTPException(status_code=400, detail=f"Token inválido: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error al guardar token")
    except Exception as e:
        logger.error(f"Error al conectar GitHub: {e}")
        raise HTTPException(status_code=500, detail=f"Error al conectar GitHub: {str(e)}")

@router.post("/connect/notion", response_model=dict)
async def connect_notion(token_request: TokenRequest, user_id: str = Depends(get_current_user_id)):
    """
    Conecta una cuenta de Notion.
    """
    try:
        client = await get_mcp_client()
        result = await client.save_user_tokens(
            user_id=user_id,
            service="notion",
            tokens={"token": token_request.token}
        )
        
        if result:
            # Verificar token con una operación simple
            try:
                response = await client.execute_notion_operation(
                    user_id=user_id,
                    operation="search",
                    arguments={"query": ""}
                )
                return {
                    "status": "success",
                    "message": "Cuenta de Notion conectada correctamente",
                    "workspace_info": response.get("response", {}).get("result", {})
                }
            except Exception as e:
                # Si falla la verificación, eliminar el token guardado
                await client.delete_user_tokens(user_id, "notion")
                raise HTTPException(status_code=400, detail=f"Token inválido: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error al guardar token")
    except Exception as e:
        logger.error(f"Error al conectar Notion: {e}")
        raise HTTPException(status_code=500, detail=f"Error al conectar Notion: {str(e)}")

@router.post("/connect/slack", response_model=dict)
async def connect_slack(token_request: SlackTokenRequest, user_id: str = Depends(get_current_user_id)):
    """
    Conecta una cuenta de Slack.
    """
    try:
        client = await get_mcp_client()
        result = await client.save_user_tokens(
            user_id=user_id,
            service="slack",
            tokens={
                "xoxc_token": token_request.xoxc_token,
                "xoxd_token": token_request.xoxd_token
            }
        )
        
        if result:
            # Verificar tokens con una operación simple
            try:
                response = await client.execute_slack_operation(
                    user_id=user_id,
                    operation="get_channels",
                    arguments={}
                )
                return {
                    "status": "success",
                    "message": "Cuenta de Slack conectada correctamente",
                    "channels_info": response.get("response", {}).get("result", {})
                }
            except Exception as e:
                # Si falla la verificación, eliminar los tokens guardados
                await client.delete_user_tokens(user_id, "slack")
                raise HTTPException(status_code=400, detail=f"Tokens inválidos: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error al guardar tokens")
    except Exception as e:
        logger.error(f"Error al conectar Slack: {e}")
        raise HTTPException(status_code=500, detail=f"Error al conectar Slack: {str(e)}")

@router.post("/connect/google_workspace", response_model=dict)
async def connect_google_workspace(token_request: GoogleTokenRequest, user_id: str = Depends(get_current_user_id)):
    """
    Conecta una cuenta de Google Workspace.
    """
    try:
        client = await get_mcp_client()
        tokens = {
            "client_id": token_request.client_id,
            "client_secret": token_request.client_secret,
            "refresh_token": token_request.refresh_token
        }
        
        if token_request.access_token:
            tokens["access_token"] = token_request.access_token
        
        result = await client.save_user_tokens(
            user_id=user_id,
            service="google_workspace",
            tokens=tokens
        )
        
        if result:
            # Verificar tokens con una operación simple
            try:
                response = await client.execute_google_workspace_operation(
                    user_id=user_id,
                    operation="list_files",
                    arguments={"pageSize": 1}
                )
                return {
                    "status": "success",
                    "message": "Cuenta de Google Workspace conectada correctamente",
                    "files_info": response.get("response", {}).get("result", {})
                }
            except Exception as e:
                # Si falla la verificación, eliminar los tokens guardados
                await client.delete_user_tokens(user_id, "google_workspace")
                raise HTTPException(status_code=400, detail=f"Tokens inválidos: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error al guardar tokens")
    except Exception as e:
        logger.error(f"Error al conectar Google Workspace: {e}")
        raise HTTPException(status_code=500, detail=f"Error al conectar Google Workspace: {str(e)}")

@router.post("/connect/instagram", response_model=dict)
async def connect_instagram(token_request: InstagramTokenRequest, user_id: str = Depends(get_current_user_id)):
    """
    Conecta una cuenta de Instagram.
    """
    try:
        client = await get_mcp_client()
        result = await client.save_user_tokens(
            user_id=user_id,
            service="instagram",
            tokens={
                "session_id": token_request.session_id,
                "csrf_token": token_request.csrf_token,
                "ds_user_id": token_request.ds_user_id
            }
        )
        
        if result:
            # Verificar tokens con una operación simple
            try:
                response = await client.execute_instagram_operation(
                    user_id=user_id,
                    operation="get_recent_messages",
                    arguments={"limit": 1}
                )
                return {
                    "status": "success",
                    "message": "Cuenta de Instagram conectada correctamente",
                    "messages_info": response.get("response", {}).get("result", {})
                }
            except Exception as e:
                # Si falla la verificación, eliminar los tokens guardados
                await client.delete_user_tokens(user_id, "instagram")
                raise HTTPException(status_code=400, detail=f"Tokens inválidos: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error al guardar tokens")
    except Exception as e:
        logger.error(f"Error al conectar Instagram: {e}")
        raise HTTPException(status_code=500, detail=f"Error al conectar Instagram: {str(e)}")

@router.post("/connect/trello", response_model=dict)
async def connect_trello(token_request: TrelloTokenRequest, user_id: str = Depends(get_current_user_id)):
    """
    Conecta una cuenta de Trello.
    """
    try:
        client = await get_mcp_client()
        tokens = {
            "api_key": token_request.api_key,
            "token": token_request.token
        }
        
        if token_request.board_id:
            tokens["board_id"] = token_request.board_id
        
        result = await client.save_user_tokens(
            user_id=user_id,
            service="trello",
            tokens=tokens
        )
        
        if result:
            # Verificar tokens con una operación simple
            try:
                response = await client.execute_trello_operation(
                    user_id=user_id,
                    operation="get_boards",
                    arguments={}
                )
                return {
                    "status": "success",
                    "message": "Cuenta de Trello conectada correctamente",
                    "boards_info": response.get("response", {}).get("result", {})
                }
            except Exception as e:
                # Si falla la verificación, eliminar los tokens guardados
                await client.delete_user_tokens(user_id, "trello")
                raise HTTPException(status_code=400, detail=f"Tokens inválidos: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error al guardar tokens")
    except Exception as e:
        logger.error(f"Error al conectar Trello: {e}")
        raise HTTPException(status_code=500, detail=f"Error al conectar Trello: {str(e)}")

@router.post("/connect/twitter_x", response_model=dict)
async def connect_twitter_x(token_request: TwitterTokenRequest, user_id: str = Depends(get_current_user_id)):
    """
    Conecta una cuenta de Twitter/X.
    """
    try:
        client = await get_mcp_client()
        result = await client.save_user_tokens(
            user_id=user_id,
            service="twitter_x",
            tokens={
                "api_key": token_request.api_key,
                "api_secret": token_request.api_secret,
                "access_token": token_request.access_token,
                "access_secret": token_request.access_secret
            }
        )
        
        if result:
            # Verificar tokens con una operación simple
            try:
                response = await client.execute_twitter_x_operation(
                    user_id=user_id,
                    operation="get_home_timeline",
                    arguments={"limit": 1}
                )
                return {
                    "status": "success",
                    "message": "Cuenta de Twitter/X conectada correctamente",
                    "timeline_info": response.get("response", {}).get("result", {})
                }
            except Exception as e:
                # Si falla la verificación, eliminar los tokens guardados
                await client.delete_user_tokens(user_id, "twitter_x")
                raise HTTPException(status_code=400, detail=f"Tokens inválidos: {str(e)}")
        else:
            raise HTTPException(status_code=500, detail="Error al guardar tokens")
    except Exception as e:
        logger.error(f"Error al conectar Twitter/X: {e}")
        raise HTTPException(status_code=500, detail=f"Error al conectar Twitter/X: {str(e)}")

@router.delete("/disconnect/{service}", response_model=dict)
async def disconnect_service(service: str = Path(...), user_id: str = Depends(get_current_user_id)):
    """
    Desconecta una cuenta de servicio externo.
    """
    try:
        client = await get_mcp_client()
        result = await client.delete_user_tokens(user_id, service)
        
        if result:
            return {
                "status": "success",
                "message": f"Cuenta de {service} desconectada correctamente"
            }
        else:
            raise HTTPException(status_code=500, detail=f"Error al desconectar {service}")
    except Exception as e:
        logger.error(f"Error al desconectar {service}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al desconectar {service}: {str(e)}")

# Endpoints de ejecución
@router.post("/execute/{service}/{operation}", response_model=dict)
async def execute_operation(
    service: str = Path(...),
    operation: str = Path(...),
    request: OperationRequest = Body(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Ejecuta una operación en un servicio externo.
    """
    try:
        response = await execute_tool_operation(
            user_id=user_id,
            service=service,
            operation=operation,
            arguments=request.arguments
        )
        
        return {
            "status": "success",
            "result": response.get("response", {}).get("result", {})
        }
    except Exception as e:
        logger.error(f"Error al ejecutar operación {operation} en {service}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al ejecutar operación {operation} en {service}: {str(e)}"
        )

# Endpoints específicos por servicio
@router.get("/github/repos", response_model=dict)
async def get_github_repos(user_id: str = Depends(get_current_user_id)):
    """
    Obtiene los repositorios del usuario en GitHub.
    """
    try:
        response = await execute_tool_operation(
            user_id=user_id,
            service="github",
            operation="get_my_repos",
            arguments={}
        )
        
        return {
            "status": "success",
            "repos": response.get("response", {}).get("result", {})
        }
    except Exception as e:
        logger.error(f"Error al obtener repositorios de GitHub: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener repositorios de GitHub: {str(e)}"
        )

@router.get("/notion/search", response_model=dict)
async def search_notion(
    query: str = Query(""),
    user_id: str = Depends(get_current_user_id)
):
    """
    Busca en Notion del usuario.
    """
    try:
        response = await execute_tool_operation(
            user_id=user_id,
            service="notion",
            operation="search",
            arguments={"query": query}
        )
        
        return {
            "status": "success",
            "results": response.get("response", {}).get("result", {})
        }
    except Exception as e:
        logger.error(f"Error al buscar en Notion: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar en Notion: {str(e)}"
        )

@router.get("/google/files", response_model=dict)
async def list_google_files(
    page_size: int = Query(10),
    query: str = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista archivos en Google Drive del usuario.
    """
    try:
        arguments = {"pageSize": page_size}
        if query:
            arguments["query"] = query
            
        response = await execute_tool_operation(
            user_id=user_id,
            service="google_workspace",
            operation="list_files",
            arguments=arguments
        )
        
        return {
            "status": "success",
            "files": response.get("response", {}).get("result", {})
        }
    except Exception as e:
        logger.error(f"Error al listar archivos de Google Drive: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar archivos de Google Drive: {str(e)}"
        )

@router.get("/instagram/messages", response_model=dict)
async def get_instagram_messages(
    limit: int = Query(10),
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtiene mensajes directos de Instagram del usuario.
    """
    try:
        response = await execute_tool_operation(
            user_id=user_id,
            service="instagram",
            operation="get_recent_messages",
            arguments={"limit": limit}
        )
        
        return {
            "status": "success",
            "messages": response.get("response", {}).get("result", {})
        }
    except Exception as e:
        logger.error(f"Error al obtener mensajes de Instagram: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener mensajes de Instagram: {str(e)}"
        )

@router.get("/trello/lists", response_model=dict)
async def get_trello_lists(
    board_id: str = Query(None),
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtiene las listas del tablero de Trello del usuario.
    """
    try:
        arguments = {}
        if board_id:
            arguments["board_id"] = board_id
            
        response = await execute_tool_operation(
            user_id=user_id,
            service="trello",
            operation="get_lists",
            arguments=arguments
        )
        
        return {
            "status": "success",
            "lists": response.get("response", {}).get("result", {})
        }
    except Exception as e:
        logger.error(f"Error al obtener listas de Trello: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener listas de Trello: {str(e)}"
        )

@router.get("/twitter/timeline", response_model=dict)
async def get_twitter_timeline(
    limit: int = Query(10),
    user_id: str = Depends(get_current_user_id)
):
    """
    Obtiene la línea de tiempo de Twitter/X del usuario.
    """
    try:
        response = await execute_tool_operation(
            user_id=user_id,
            service="twitter_x",
            operation="get_home_timeline",
            arguments={"limit": limit}
        )
        
        return {
            "status": "success",
            "tweets": response.get("response", {}).get("result", {})
        }
    except Exception as e:
        logger.error(f"Error al obtener timeline de Twitter/X: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener timeline de Twitter/X: {str(e)}"
        )

# Endpoints de estado del sistema
@router.get("/status", response_model=List[ServerStatus])
async def get_system_status(user_id: str = Depends(get_current_user_id)):
    """
    Obtiene el estado de los servidores MCP.
    """
    try:
        client = await get_mcp_client()
        status = client.orchestrator.get_server_status()
        
        result = []
        for name, server_status in status.items():
            result.append({
                "name": name,
                "status": server_status.get("status", "unknown"),
                "running": server_status.get("running", False),
                "pid": server_status.get("pid"),
                "uptime": server_status.get("uptime")
            })
        
        return result
    except Exception as e:
        logger.error(f"Error al obtener estado del sistema: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estado del sistema: {str(e)}"
        )

# Función para obtener el ID de usuario actual
async def get_current_user_id():
    """
    Obtiene el ID del usuario actual.
    En una implementación real, esto se obtendría del token JWT.
    """
    # TODO: Implementar autenticación real
    return "test_user_001"
