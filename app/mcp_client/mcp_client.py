"""
MCP Client para GENIA

Este módulo implementa un cliente para interactuar con el orquestador MCP,
proporcionando una interfaz simplificada para los servicios de GENIA.

Autor: GENIA Team
Fecha: Mayo 2025
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from .mcp_orchestrator import MCPOrchestrator

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
    
    async def save_user_tokens(self, 
                              user_id: str, 
                              service: str, 
                              tokens: Dict[str, str]) -> bool:
        """
        Guarda los tokens de un usuario para un servicio específico.
        
        Args:
            user_id: ID único del usuario
            service: Nombre del servicio (github, notion, slack)
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
    
    # Ejecutar operación en GitHub
    github_response = await client.execute_github_operation(
        user_id="user123",
        operation="get_me",
        arguments={}
    )
    
    print(f"Respuesta de GitHub: {github_response}")
    
    # Apagar cliente
    await client.shutdown()

if __name__ == "__main__":
    # Ejecutar ejemplo
    asyncio.run(example_usage())
