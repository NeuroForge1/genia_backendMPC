"""
MCP Client Extendido para GENIA

Este módulo implementa un cliente para interactuar con el orquestador MCP extendido,
proporcionando una interfaz simplificada para todos los servicios de GENIA.

Autor: GENIA Team
Fecha: Mayo 2025
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from .mcp_orchestrator_extended import MCPOrchestrator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_client")

class MCPClient:
    """
    Cliente para interactuar con el orquestador MCP.
    
    Esta clase proporciona una interfaz simplificada para que los servicios
    de GENIA interactúen con las herramientas externas a través del orquestador MCP.
    """
    
    def __init__(self):
        """Inicializa el cliente MCP."""
        self.orchestrator = MCPOrchestrator()
        self.initialized = False
    
    async def initialize(self) -> bool:
        """
        Inicializa el cliente MCP y registra los servidores predefinidos.
        
        Returns:
            True si la inicialización fue exitosa, False en caso contrario
        """
        if self.initialized:
            logger.info("Cliente MCP ya está inicializado")
            return True
        
        try:
            # Registrar servidores predefinidos (sin tokens)
            # Los tokens se proporcionarán al ejecutar las operaciones
            
            # Servidores originales
            self.orchestrator.register_server(
                name="github",
                command=["docker", "run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
                env_vars={}
            )
            
            self.orchestrator.register_server(
                name="notion",
                command=["docker", "run", "-i", "--rm", "-e", "OPENAPI_MCP_HEADERS", "mcp/notion"],
                env_vars={}
            )
            
            self.orchestrator.register_server(
                name="slack",
                command=["npx", "-y", "slack-mcp-server@latest", "--transport", "stdio"],
                env_vars={}
            )
            
            # Servidores adicionales
            self.orchestrator.register_server(
                name="google_workspace",
                command=["mcp-google", "drive", "--access-token", "placeholder"],
                env_vars={}
            )
            
            self.orchestrator.register_server(
                name="google_sheets",
                command=["mcp-google", "sheets", "--access-token", "placeholder"],
                env_vars={}
            )
            
            self.orchestrator.register_server(
                name="instagram",
                command=["npx", "-y", "instagram-dm-mcp", "start"],
                env_vars={}
            )
            
            self.orchestrator.register_server(
                name="trello",
                command=["npx", "-y", "@delorenj/mcp-server-trello"],
                env_vars={}
            )
            
            self.orchestrator.register_server(
                name="twitter_x",
                command=["node", "x-mcp-server/build/index.js"],
                env_vars={}
            )
            
            self.initialized = True
            logger.info("Cliente MCP inicializado correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al inicializar cliente MCP: {e}")
            return False
    
    async def execute_github_operation(self, 
                                      user_id: str, 
                                      operation: str, 
                                      arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta una operación en GitHub.
        
        Args:
            user_id: ID único del usuario
            operation: Nombre de la operación a ejecutar
            arguments: Argumentos para la operación
            
        Returns:
            Respuesta de la operación
        """
        if not self.initialized:
            await self.initialize()
        
        # Cargar tokens del usuario
        tokens = self.orchestrator.load_user_tokens(user_id)
        if not tokens or "github" not in tokens:
            raise ValueError(f"No se encontró token de GitHub para usuario {user_id}")
        
        # Configurar servidor con token del usuario
        github_server = self.orchestrator.servers["github"]
        github_server.env_vars = {
            "GITHUB_PERSONAL_ACCESS_TOKEN": tokens["github"]
        }
        
        # Iniciar servidor si no está en ejecución
        if not github_server.running:
            await self.orchestrator.start_server("github")
        
        # Preparar solicitud MCP
        request = {
            "type": "function",
            "function": {
                "name": operation,
                "arguments": json.dumps(arguments or {})
            }
        }
        
        # Enviar solicitud y devolver respuesta
        return await self.orchestrator.send_request("github", request)
    
    async def execute_notion_operation(self, 
                                      user_id: str, 
                                      operation: str, 
                                      arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta una operación en Notion.
        
        Args:
            user_id: ID único del usuario
            operation: Nombre de la operación a ejecutar
            arguments: Argumentos para la operación
            
        Returns:
            Respuesta de la operación
        """
        if not self.initialized:
            await self.initialize()
        
        # Cargar tokens del usuario
        tokens = self.orchestrator.load_user_tokens(user_id)
        if not tokens or "notion" not in tokens:
            raise ValueError(f"No se encontró token de Notion para usuario {user_id}")
        
        # Configurar servidor con token del usuario
        notion_server = self.orchestrator.servers["notion"]
        notion_server.env_vars = {
            "OPENAPI_MCP_HEADERS": f'{{"Authorization": "Bearer {tokens["notion"]}", "Notion-Version": "2022-06-28" }}'
        }
        
        # Iniciar servidor si no está en ejecución
        if not notion_server.running:
            await self.orchestrator.start_server("notion")
        
        # Preparar solicitud MCP
        request = {
            "type": "function",
            "function": {
                "name": operation,
                "arguments": json.dumps(arguments or {})
            }
        }
        
        # Enviar solicitud y devolver respuesta
        return await self.orchestrator.send_request("notion", request)
    
    async def execute_slack_operation(self, 
                                     user_id: str, 
                                     operation: str, 
                                     arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta una operación en Slack.
        
        Args:
            user_id: ID único del usuario
            operation: Nombre de la operación a ejecutar
            arguments: Argumentos para la operación
            
        Returns:
            Respuesta de la operación
        """
        if not self.initialized:
            await self.initialize()
        
        # Cargar tokens del usuario
        tokens = self.orchestrator.load_user_tokens(user_id)
        if not tokens or "slack_xoxc" not in tokens or "slack_xoxd" not in tokens:
            raise ValueError(f"No se encontraron tokens de Slack para usuario {user_id}")
        
        # Configurar servidor con tokens del usuario
        slack_server = self.orchestrator.servers["slack"]
        slack_server.env_vars = {
            "SLACK_MCP_XOXC_TOKEN": tokens["slack_xoxc"],
            "SLACK_MCP_XOXD_TOKEN": tokens["slack_xoxd"]
        }
        
        # Iniciar servidor si no está en ejecución
        if not slack_server.running:
            await self.orchestrator.start_server("slack")
        
        # Preparar solicitud MCP
        request = {
            "type": "function",
            "function": {
                "name": operation,
                "arguments": json.dumps(arguments or {})
            }
        }
        
        # Enviar solicitud y devolver respuesta
        return await self.orchestrator.send_request("slack", request)
    
    # Nuevos métodos para servidores MCP adicionales
    
    async def execute_google_workspace_operation(self, 
                                               user_id: str, 
                                               operation: str, 
                                               arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta una operación en Google Workspace (Drive).
        
        Args:
            user_id: ID único del usuario
            operation: Nombre de la operación a ejecutar
            arguments: Argumentos para la operación
            
        Returns:
            Respuesta de la operación
        """
        if not self.initialized:
            await self.initialize()
        
        # Cargar tokens del usuario
        tokens = self.orchestrator.load_user_tokens(user_id)
        if not tokens or "google_access_token" not in tokens:
            raise ValueError(f"No se encontró token de Google Workspace para usuario {user_id}")
        
        # Configurar servidor con tokens del usuario
        google_workspace_server = self.orchestrator.servers["google_workspace"]
        google_workspace_server.env_vars = {
            "GOOGLE_ACCESS_TOKEN": tokens["google_access_token"],
            "GOOGLE_CLIENT_ID": tokens.get("google_client_id", ""),
            "GOOGLE_CLIENT_SECRET": tokens.get("google_client_secret", ""),
            "GOOGLE_REFRESH_TOKEN": tokens.get("google_refresh_token", "")
        }
        
        # Actualizar comando con token de acceso
        google_workspace_server.command = [
            "mcp-google", "drive", "--access-token", tokens["google_access_token"]
        ]
        
        # Iniciar servidor si no está en ejecución
        if not google_workspace_server.running:
            await self.orchestrator.start_server("google_workspace")
        
        # Preparar solicitud MCP
        request = {
            "type": "function",
            "function": {
                "name": operation,
                "arguments": json.dumps(arguments or {})
            }
        }
        
        # Enviar solicitud y devolver respuesta
        return await self.orchestrator.send_request("google_workspace", request)
    
    async def execute_google_sheets_operation(self, 
                                            user_id: str, 
                                            operation: str, 
                                            arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta una operación en Google Sheets.
        
        Args:
            user_id: ID único del usuario
            operation: Nombre de la operación a ejecutar
            arguments: Argumentos para la operación
            
        Returns:
            Respuesta de la operación
        """
        if not self.initialized:
            await self.initialize()
        
        # Cargar tokens del usuario
        tokens = self.orchestrator.load_user_tokens(user_id)
        if not tokens or "google_access_token" not in tokens:
            raise ValueError(f"No se encontró token de Google Sheets para usuario {user_id}")
        
        # Configurar servidor con tokens del usuario
        google_sheets_server = self.orchestrator.servers["google_sheets"]
        google_sheets_server.env_vars = {
            "GOOGLE_ACCESS_TOKEN": tokens["google_access_token"],
            "GOOGLE_CLIENT_ID": tokens.get("google_client_id", ""),
            "GOOGLE_CLIENT_SECRET": tokens.get("google_client_secret", ""),
            "GOOGLE_REFRESH_TOKEN": tokens.get("google_refresh_token", "")
        }
        
        # Actualizar comando con token de acceso
        google_sheets_server.command = [
            "mcp-google", "sheets", "--access-token", tokens["google_access_token"]
        ]
        
        # Iniciar servidor si no está en ejecución
        if not google_sheets_server.running:
            await self.orchestrator.start_server("google_sheets")
        
        # Preparar solicitud MCP
        request = {
            "type": "function",
            "function": {
                "name": operation,
                "arguments": json.dumps(arguments or {})
            }
        }
        
        # Enviar solicitud y devolver respuesta
        return await self.orchestrator.send_request("google_sheets", request)
    
    async def execute_instagram_operation(self, 
                                         user_id: str, 
                                         operation: str, 
                                         arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta una operación en Instagram.
        
        Args:
            user_id: ID único del usuario
            operation: Nombre de la operación a ejecutar
            arguments: Argumentos para la operación
            
        Returns:
            Respuesta de la operación
        """
        if not self.initialized:
            await self.initialize()
        
        # Cargar tokens del usuario
        tokens = self.orchestrator.load_user_tokens(user_id)
        if not tokens or "instagram_session_id" not in tokens:
            raise ValueError(f"No se encontraron credenciales de Instagram para usuario {user_id}")
        
        # Configurar servidor con tokens del usuario
        instagram_server = self.orchestrator.servers["instagram"]
        instagram_server.env_vars = {
            "INSTAGRAM_SESSION_ID": tokens["instagram_session_id"],
            "INSTAGRAM_CSRF_TOKEN": tokens["instagram_csrf_token"],
            "INSTAGRAM_DS_USER_ID": tokens["instagram_ds_user_id"]
        }
        
        # Iniciar servidor si no está en ejecución
        if not instagram_server.running:
            await self.orchestrator.start_server("instagram")
        
        # Preparar solicitud MCP
        request = {
            "type": "function",
            "function": {
                "name": operation,
                "arguments": json.dumps(arguments or {})
            }
        }
        
        # Enviar solicitud y devolver respuesta
        return await self.orchestrator.send_request("instagram", request)
    
    async def execute_trello_operation(self, 
                                      user_id: str, 
                                      operation: str, 
                                      arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta una operación en Trello.
        
        Args:
            user_id: ID único del usuario
            operation: Nombre de la operación a ejecutar
            arguments: Argumentos para la operación
            
        Returns:
            Respuesta de la operación
        """
        if not self.initialized:
            await self.initialize()
        
        # Cargar tokens del usuario
        tokens = self.orchestrator.load_user_tokens(user_id)
        if not tokens or "trello_api_key" not in tokens or "trello_token" not in tokens:
            raise ValueError(f"No se encontraron credenciales de Trello para usuario {user_id}")
        
        # Configurar servidor con tokens del usuario
        trello_server = self.orchestrator.servers["trello"]
        trello_server.env_vars = {
            "TRELLO_API_KEY": tokens["trello_api_key"],
            "TRELLO_TOKEN": tokens["trello_token"],
            "TRELLO_BOARD_ID": tokens.get("trello_board_id", "")
        }
        
        # Iniciar servidor si no está en ejecución
        if not trello_server.running:
            await self.orchestrator.start_server("trello")
        
        # Preparar solicitud MCP
        request = {
            "type": "function",
            "function": {
                "name": operation,
                "arguments": json.dumps(arguments or {})
            }
        }
        
        # Enviar solicitud y devolver respuesta
        return await self.orchestrator.send_request("trello", request)
    
    async def execute_twitter_x_operation(self, 
                                         user_id: str, 
                                         operation: str, 
                                         arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta una operación en Twitter/X.
        
        Args:
            user_id: ID único del usuario
            operation: Nombre de la operación a ejecutar
            arguments: Argumentos para la operación
            
        Returns:
            Respuesta de la operación
        """
        if not self.initialized:
            await self.initialize()
        
        # Cargar tokens del usuario
        tokens = self.orchestrator.load_user_tokens(user_id)
        if not tokens or "twitter_api_key" not in tokens:
            raise ValueError(f"No se encontraron credenciales de Twitter/X para usuario {user_id}")
        
        # Configurar servidor con tokens del usuario
        twitter_x_server = self.orchestrator.servers["twitter_x"]
        twitter_x_server.env_vars = {
            "TWITTER_API_KEY": tokens["twitter_api_key"],
            "TWITTER_API_SECRET": tokens["twitter_api_secret"],
            "TWITTER_ACCESS_TOKEN": tokens["twitter_access_token"],
            "TWITTER_ACCESS_SECRET": tokens["twitter_access_secret"]
        }
        
        # Iniciar servidor si no está en ejecución
        if not twitter_x_server.running:
            await self.orchestrator.start_server("twitter_x")
        
        # Preparar solicitud MCP
        request = {
            "type": "function",
            "function": {
                "name": operation,
                "arguments": json.dumps(arguments or {})
            }
        }
        
        # Enviar solicitud y devolver respuesta
        return await self.orchestrator.send_request("twitter_x", request)
    
    async def save_user_tokens(self, 
                              user_id: str, 
                              service: str, 
                              tokens: Dict[str, str]) -> bool:
        """
        Guarda los tokens de un usuario para un servicio específico.
        
        Args:
            user_id: ID único del usuario
            service: Nombre del servicio (github, notion, slack, etc.)
            tokens: Tokens para el servicio
            
        Returns:
            True si el guardado fue exitoso, False en caso contrario
        """
        if not self.initialized:
            await self.initialize()
        
        # Cargar tokens existentes
        existing_tokens = self.orchestrator.load_user_tokens(user_id) or {}
        
        # Actualizar tokens para el servicio
        if service == "github":
            existing_tokens["github"] = tokens.get("token")
        elif service == "notion":
            existing_tokens["notion"] = tokens.get("token")
        elif service == "slack":
            existing_tokens["slack_xoxc"] = tokens.get("xoxc_token")
            existing_tokens["slack_xoxd"] = tokens.get("xoxd_token")
        elif service == "google_workspace":
            existing_tokens["google_access_token"] = tokens.get("access_token")
            existing_tokens["google_client_id"] = tokens.get("client_id")
            existing_tokens["google_client_secret"] = tokens.get("client_secret")
            existing_tokens["google_refresh_token"] = tokens.get("refresh_token")
        elif service == "instagram":
            existing_tokens["instagram_session_id"] = tokens.get("session_id")
            existing_tokens["instagram_csrf_token"] = tokens.get("csrf_token")
            existing_tokens["instagram_ds_user_id"] = tokens.get("ds_user_id")
        elif service == "trello":
            existing_tokens["trello_api_key"] = tokens.get("api_key")
            existing_tokens["trello_token"] = tokens.get("token")
            existing_tokens["trello_board_id"] = tokens.get("board_id")
        elif service == "twitter_x":
            existing_tokens["twitter_api_key"] = tokens.get("api_key")
            existing_tokens["twitter_api_secret"] = tokens.get("api_secret")
            existing_tokens["twitter_access_token"] = tokens.get("access_token")
            existing_tokens["twitter_access_secret"] = tokens.get("access_secret")
        else:
            logger.warning(f"Servicio desconocido: {service}")
            return False
        
        # Guardar tokens actualizados
        return self.orchestrator.save_user_tokens(user_id, existing_tokens)
    
    async def shutdown(self) -> bool:
        """
        Detiene todos los servidores MCP y libera recursos.
        
        Returns:
            True si el apagado fue exitoso, False en caso contrario
        """
        if not self.initialized:
            logger.info("Cliente MCP no está inicializado")
            return True
        
        try:
            # Detener todos los servidores
            await self.orchestrator.stop_all_servers()
            self.initialized = False
            logger.info("Cliente MCP apagado correctamente")
            return True
        
        except Exception as e:
            logger.error(f"Error al apagar cliente MCP: {e}")
            return False

# Instancia global del cliente MCP
_mcp_client = None

async def get_mcp_client() -> MCPClient:
    """
    Obtiene la instancia global del cliente MCP.
    
    Returns:
        Instancia del cliente MCP
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
        await _mcp_client.initialize()
    return _mcp_client

# Ejemplo de uso
async def example_usage():
    # Obtener cliente MCP
    client = await get_mcp_client()
    
    # Guardar tokens de ejemplo para un usuario
    await client.save_user_tokens("user123", "github", {"token": "ghp_example_token"})
    await client.save_user_tokens("user123", "notion", {"token": "secret_example_token"})
    await client.save_user_tokens("user123", "google_workspace", {
        "access_token": "example_access_token",
        "client_id": "example_client_id",
        "client_secret": "example_client_secret",
        "refresh_token": "example_refresh_token"
    })
    
    # Ejecutar operación en GitHub
    github_response = await client.execute_github_operation(
        user_id="user123",
        operation="get_me",
        arguments={}
    )
    
    print(f"Respuesta de GitHub: {github_response}")
    
    # Ejecutar operación en Google Workspace
    google_response = await client.execute_google_workspace_operation(
        user_id="user123",
        operation="list_files",
        arguments={"pageSize": 10}
    )
    
    print(f"Respuesta de Google Workspace: {google_response}")
    
    # Apagar cliente
    await client.shutdown()

if __name__ == "__main__":
    # Ejecutar ejemplo
    asyncio.run(example_usage())
