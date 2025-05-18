"""
MCP Orchestrator Extendido para GENIA

Este módulo implementa un orquestador central para todos los servidores MCP,
permitiendo a GENIA interactuar con múltiples herramientas externas
a través de una interfaz unificada.

Autor: GENIA Team
Fecha: Mayo 2025
"""

import os
import json
import asyncio
import logging
import subprocess
from typing import Dict, List, Any, Optional, Tuple
import aiohttp
from aiohttp import ClientSession

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_orchestrator")

class MCPServer:
    """Clase que representa un servidor MCP y gestiona su ciclo de vida."""
    
    def __init__(self, 
                 name: str, 
                 command: List[str], 
                 env_vars: Dict[str, str] = None,
                 server_type: str = "stdio"):
        """
        Inicializa un servidor MCP.
        
        Args:
            name: Nombre único del servidor MCP
            command: Comando y argumentos para iniciar el servidor
            env_vars: Variables de entorno necesarias
            server_type: Tipo de servidor (stdio, sse, etc.)
        """
        self.name = name
        self.command = command
        self.env_vars = env_vars or {}
        self.server_type = server_type
        self.process = None
        self.running = False
        self.last_error = None
    
    async def start(self) -> bool:
        """Inicia el servidor MCP como un subproceso."""
        if self.running:
            logger.info(f"Servidor MCP '{self.name}' ya está en ejecución")
            return True
        
        try:
            # Preparar entorno con variables específicas del servidor
            env = os.environ.copy()
            env.update(self.env_vars)
            
            # Iniciar el proceso
            logger.info(f"Iniciando servidor MCP '{self.name}' con comando: {' '.join(self.command)}")
            self.process = await asyncio.create_subprocess_exec(
                *self.command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            self.running = True
            logger.info(f"Servidor MCP '{self.name}' iniciado con PID {self.process.pid}")
            
            # Iniciar tarea para capturar stderr
            asyncio.create_task(self._log_stderr())
            
            return True
        
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error al iniciar servidor MCP '{self.name}': {e}")
            return False
    
    async def stop(self) -> bool:
        """Detiene el servidor MCP."""
        if not self.running or not self.process:
            logger.info(f"Servidor MCP '{self.name}' no está en ejecución")
            return True
        
        try:
            logger.info(f"Deteniendo servidor MCP '{self.name}'")
            self.process.terminate()
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
            self.running = False
            logger.info(f"Servidor MCP '{self.name}' detenido")
            return True
        
        except asyncio.TimeoutError:
            logger.warning(f"Timeout al detener servidor MCP '{self.name}', forzando terminación")
            self.process.kill()
            await self.process.wait()
            self.running = False
            return True
        
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error al detener servidor MCP '{self.name}': {e}")
            return False
    
    async def _log_stderr(self):
        """Captura y registra la salida de error del servidor MCP."""
        if not self.process or not self.process.stderr:
            return
        
        while True:
            line = await self.process.stderr.readline()
            if not line:
                break
            
            error_line = line.decode('utf-8').strip()
            if error_line:
                logger.warning(f"[{self.name}] {error_line}")
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía una solicitud al servidor MCP y espera la respuesta.
        
        Args:
            request: Solicitud en formato MCP
            
        Returns:
            Respuesta del servidor MCP
        """
        if not self.running or not self.process:
            raise RuntimeError(f"Servidor MCP '{self.name}' no está en ejecución")
        
        try:
            # Serializar la solicitud
            request_json = json.dumps(request) + "\n"
            request_bytes = request_json.encode('utf-8')
            
            # Enviar solicitud
            self.process.stdin.write(request_bytes)
            await self.process.stdin.drain()
            
            # Leer respuesta
            response_line = await self.process.stdout.readline()
            if not response_line:
                raise RuntimeError(f"Servidor MCP '{self.name}' cerró la conexión")
            
            # Deserializar la respuesta
            response = json.loads(response_line.decode('utf-8'))
            return response
        
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error al comunicarse con servidor MCP '{self.name}': {e}")
            raise

class MCPOrchestrator:
    """
    Orquestador central para servidores MCP.
    
    Esta clase gestiona múltiples servidores MCP y proporciona una interfaz
    unificada para interactuar con ellos.
    """
    
    def __init__(self):
        """Inicializa el orquestador MCP."""
        self.servers: Dict[str, MCPServer] = {}
        self.config_dir = os.path.join(os.path.dirname(__file__), "config")
        self.user_tokens: Dict[str, Dict[str, str]] = {}
        
        # Crear directorio de configuración si no existe
        os.makedirs(self.config_dir, exist_ok=True)
    
    def register_server(self, 
                       name: str, 
                       command: List[str], 
                       env_vars: Dict[str, str] = None,
                       server_type: str = "stdio") -> bool:
        """
        Registra un nuevo servidor MCP.
        
        Args:
            name: Nombre único del servidor MCP
            command: Comando y argumentos para iniciar el servidor
            env_vars: Variables de entorno necesarias
            server_type: Tipo de servidor (stdio, sse, etc.)
            
        Returns:
            True si el registro fue exitoso, False en caso contrario
        """
        if name in self.servers:
            logger.warning(f"Servidor MCP '{name}' ya está registrado")
            return False
        
        server = MCPServer(name, command, env_vars, server_type)
        self.servers[name] = server
        logger.info(f"Servidor MCP '{name}' registrado")
        return True
    
    def unregister_server(self, name: str) -> bool:
        """
        Elimina un servidor MCP del registro.
        
        Args:
            name: Nombre del servidor MCP a eliminar
            
        Returns:
            True si la eliminación fue exitosa, False en caso contrario
        """
        if name not in self.servers:
            logger.warning(f"Servidor MCP '{name}' no está registrado")
            return False
        
        del self.servers[name]
        logger.info(f"Servidor MCP '{name}' eliminado del registro")
        return True
    
    async def start_server(self, name: str) -> bool:
        """
        Inicia un servidor MCP registrado.
        
        Args:
            name: Nombre del servidor MCP a iniciar
            
        Returns:
            True si el inicio fue exitoso, False en caso contrario
        """
        if name not in self.servers:
            logger.warning(f"Servidor MCP '{name}' no está registrado")
            return False
        
        return await self.servers[name].start()
    
    async def stop_server(self, name: str) -> bool:
        """
        Detiene un servidor MCP en ejecución.
        
        Args:
            name: Nombre del servidor MCP a detener
            
        Returns:
            True si la detención fue exitosa, False en caso contrario
        """
        if name not in self.servers:
            logger.warning(f"Servidor MCP '{name}' no está registrado")
            return False
        
        return await self.servers[name].stop()
    
    async def start_all_servers(self) -> Dict[str, bool]:
        """
        Inicia todos los servidores MCP registrados.
        
        Returns:
            Diccionario con el resultado del inicio de cada servidor
        """
        results = {}
        for name in self.servers:
            results[name] = await self.start_server(name)
        return results
    
    async def stop_all_servers(self) -> Dict[str, bool]:
        """
        Detiene todos los servidores MCP en ejecución.
        
        Returns:
            Diccionario con el resultado de la detención de cada servidor
        """
        results = {}
        for name in self.servers:
            results[name] = await self.stop_server(name)
        return results
    
    async def send_request(self, server_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía una solicitud a un servidor MCP específico.
        
        Args:
            server_name: Nombre del servidor MCP
            request: Solicitud en formato MCP
            
        Returns:
            Respuesta del servidor MCP
        """
        if server_name not in self.servers:
            raise ValueError(f"Servidor MCP '{server_name}' no está registrado")
        
        server = self.servers[server_name]
        if not server.running:
            await server.start()
        
        return await server.send_request(request)
    
    def save_user_tokens(self, user_id: str, tokens: Dict[str, str]) -> bool:
        """
        Guarda los tokens de un usuario para diferentes servicios.
        
        Args:
            user_id: ID único del usuario
            tokens: Diccionario de tokens por servicio
            
        Returns:
            True si el guardado fue exitoso, False en caso contrario
        """
        try:
            # Guardar en memoria
            self.user_tokens[user_id] = tokens
            
            # Guardar en archivo
            file_path = os.path.join(self.config_dir, f"user_{user_id}_tokens.json")
            with open(file_path, 'w') as f:
                json.dump(tokens, f)
            
            logger.info(f"Tokens guardados para usuario {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error al guardar tokens para usuario {user_id}: {e}")
            return False
    
    def load_user_tokens(self, user_id: str) -> Optional[Dict[str, str]]:
        """
        Carga los tokens de un usuario.
        
        Args:
            user_id: ID único del usuario
            
        Returns:
            Diccionario de tokens por servicio, o None si no se encontraron
        """
        # Verificar si ya están en memoria
        if user_id in self.user_tokens:
            return self.user_tokens[user_id]
        
        try:
            # Intentar cargar desde archivo
            file_path = os.path.join(self.config_dir, f"user_{user_id}_tokens.json")
            if not os.path.exists(file_path):
                logger.warning(f"No se encontraron tokens para usuario {user_id}")
                return None
            
            with open(file_path, 'r') as f:
                tokens = json.load(f)
            
            # Guardar en memoria para futuras consultas
            self.user_tokens[user_id] = tokens
            
            logger.info(f"Tokens cargados para usuario {user_id}")
            return tokens
        
        except Exception as e:
            logger.error(f"Error al cargar tokens para usuario {user_id}: {e}")
            return None
    
    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtiene el estado de todos los servidores MCP registrados.
        
        Returns:
            Diccionario con el estado de cada servidor
        """
        status = {}
        for name, server in self.servers.items():
            status[name] = {
                "running": server.running,
                "server_type": server.server_type,
                "last_error": server.last_error
            }
        return status

# Configuraciones predefinidas para servidores MCP comunes
GITHUB_MCP_CONFIG = {
    "name": "github",
    "command": ["docker", "run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
    "env_vars": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
    }
}

NOTION_MCP_CONFIG = {
    "name": "notion",
    "command": ["docker", "run", "-i", "--rm", "-e", "OPENAPI_MCP_HEADERS", "mcp/notion"],
    "env_vars": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer ${NOTION_TOKEN}\", \"Notion-Version\": \"2022-06-28\" }"
    }
}

SLACK_MCP_CONFIG = {
    "name": "slack",
    "command": ["npx", "-y", "slack-mcp-server@latest", "--transport", "stdio"],
    "env_vars": {
        "SLACK_MCP_XOXC_TOKEN": "${SLACK_XOXC_TOKEN}",
        "SLACK_MCP_XOXD_TOKEN": "${SLACK_XOXD_TOKEN}"
    }
}

# Nuevas configuraciones para servidores MCP adicionales

GOOGLE_WORKSPACE_MCP_CONFIG = {
    "name": "google_workspace",
    "command": ["mcp-google", "drive", "--access-token", "${GOOGLE_ACCESS_TOKEN}"],
    "env_vars": {
        "GOOGLE_ACCESS_TOKEN": "${GOOGLE_ACCESS_TOKEN}",
        "GOOGLE_CLIENT_ID": "${GOOGLE_CLIENT_ID}",
        "GOOGLE_CLIENT_SECRET": "${GOOGLE_CLIENT_SECRET}",
        "GOOGLE_REFRESH_TOKEN": "${GOOGLE_REFRESH_TOKEN}"
    }
}

GOOGLE_SHEETS_MCP_CONFIG = {
    "name": "google_sheets",
    "command": ["mcp-google", "sheets", "--access-token", "${GOOGLE_ACCESS_TOKEN}"],
    "env_vars": {
        "GOOGLE_ACCESS_TOKEN": "${GOOGLE_ACCESS_TOKEN}",
        "GOOGLE_CLIENT_ID": "${GOOGLE_CLIENT_ID}",
        "GOOGLE_CLIENT_SECRET": "${GOOGLE_CLIENT_SECRET}",
        "GOOGLE_REFRESH_TOKEN": "${GOOGLE_REFRESH_TOKEN}"
    }
}

INSTAGRAM_MCP_CONFIG = {
    "name": "instagram",
    "command": ["npx", "-y", "instagram-dm-mcp", "start"],
    "env_vars": {
        "INSTAGRAM_SESSION_ID": "${INSTAGRAM_SESSION_ID}",
        "INSTAGRAM_CSRF_TOKEN": "${INSTAGRAM_CSRF_TOKEN}",
        "INSTAGRAM_DS_USER_ID": "${INSTAGRAM_DS_USER_ID}"
    }
}

TRELLO_MCP_CONFIG = {
    "name": "trello",
    "command": ["npx", "-y", "@delorenj/mcp-server-trello"],
    "env_vars": {
        "TRELLO_API_KEY": "${TRELLO_API_KEY}",
        "TRELLO_TOKEN": "${TRELLO_TOKEN}",
        "TRELLO_BOARD_ID": "${TRELLO_BOARD_ID}"
    }
}

TWITTER_X_MCP_CONFIG = {
    "name": "twitter_x",
    "command": ["node", "x-mcp-server/build/index.js"],
    "env_vars": {
        "TWITTER_API_KEY": "${TWITTER_API_KEY}",
        "TWITTER_API_SECRET": "${TWITTER_API_SECRET}",
        "TWITTER_ACCESS_TOKEN": "${TWITTER_ACCESS_TOKEN}",
        "TWITTER_ACCESS_SECRET": "${TWITTER_ACCESS_SECRET}"
    }
}

# Ejemplo de uso
async def example_usage():
    # Crear orquestador
    orchestrator = MCPOrchestrator()
    
    # Registrar servidores con tokens de ejemplo
    orchestrator.register_server(
        name="github",
        command=["docker", "run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
        env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_example_token"}
    )
    
    orchestrator.register_server(
        name="notion",
        command=["docker", "run", "-i", "--rm", "-e", "OPENAPI_MCP_HEADERS", "mcp/notion"],
        env_vars={"OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer secret_example_token\", \"Notion-Version\": \"2022-06-28\" }"}
    )
    
    # Registrar servidores MCP adicionales
    orchestrator.register_server(
        name="google_workspace",
        command=["mcp-google", "drive", "--access-token", "example_access_token"],
        env_vars={
            "GOOGLE_ACCESS_TOKEN": "example_access_token",
            "GOOGLE_CLIENT_ID": "example_client_id",
            "GOOGLE_CLIENT_SECRET": "example_client_secret",
            "GOOGLE_REFRESH_TOKEN": "example_refresh_token"
        }
    )
    
    orchestrator.register_server(
        name="instagram",
        command=["npx", "-y", "instagram-dm-mcp", "start"],
        env_vars={
            "INSTAGRAM_SESSION_ID": "example_session_id",
            "INSTAGRAM_CSRF_TOKEN": "example_csrf_token",
            "INSTAGRAM_DS_USER_ID": "example_ds_user_id"
        }
    )
    
    orchestrator.register_server(
        name="trello",
        command=["npx", "-y", "@delorenj/mcp-server-trello"],
        env_vars={
            "TRELLO_API_KEY": "example_api_key",
            "TRELLO_TOKEN": "example_token",
            "TRELLO_BOARD_ID": "example_board_id"
        }
    )
    
    orchestrator.register_server(
        name="twitter_x",
        command=["node", "x-mcp-server/build/index.js"],
        env_vars={
            "TWITTER_API_KEY": "example_api_key",
            "TWITTER_API_SECRET": "example_api_secret",
            "TWITTER_ACCESS_TOKEN": "example_access_token",
            "TWITTER_ACCESS_SECRET": "example_access_secret"
        }
    )
    
    # Iniciar servidores
    await orchestrator.start_all_servers()
    
    # Enviar solicitud a GitHub MCP
    response = await orchestrator.send_request("github", {
        "type": "function",
        "function": {
            "name": "get_me",
            "arguments": "{}"
        }
    })
    
    print(f"Respuesta de GitHub MCP: {response}")
    
    # Enviar solicitud a Google Workspace MCP
    response = await orchestrator.send_request("google_workspace", {
        "type": "function",
        "function": {
            "name": "list_files",
            "arguments": "{\"pageSize\": 10}"
        }
    })
    
    print(f"Respuesta de Google Workspace MCP: {response}")
    
    # Detener servidores
    await orchestrator.stop_all_servers()

if __name__ == "__main__":
    # Ejecutar ejemplo
    asyncio.run(example_usage())
