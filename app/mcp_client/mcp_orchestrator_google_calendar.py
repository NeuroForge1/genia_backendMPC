"""
Extensión del orquestador MCP para Google Calendar

Este módulo extiende el orquestador MCP para soportar el servidor de Google Calendar,
permitiendo a GENIA interactuar con eventos de calendario de los usuarios.

Autor: GENIA Team
Fecha: Mayo 2025
"""

import os
import json
import logging
import asyncio
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_orchestrator_google_calendar")

class MCPOrchestratorGoogleCalendar:
    """
    Extensión del orquestador MCP para Google Calendar.
    
    Esta clase gestiona el ciclo de vida del servidor MCP de Google Calendar,
    incluyendo su inicialización, comunicación y terminación.
    """
    
    def __init__(self, base_dir: str = None, supabase_url: str = None, supabase_key: str = None):
        """
        Inicializa el orquestador de Google Calendar MCP.
        
        Args:
            base_dir: Directorio base donde se encuentra el servidor MCP
            supabase_url: URL de la API de Supabase
            supabase_key: Clave de API de Supabase
        """
        self.base_dir = base_dir or os.environ.get("GOOGLE_CALENDAR_MCP_DIR", "/opt/genia/mcp-servers/google-calendar-mcp")
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_KEY")
        self.supabase_jwt_secret = os.environ.get("SUPABASE_JWT_SECRET")
        
        # Proceso del servidor MCP
        self.process = None
        self.running = False
        self.start_time = None
        
        # Verificar Python 3.13+
        self.python_cmd = self._get_python_cmd()
        
        # Verificar UV Package Manager
        self.uv_cmd = self._get_uv_cmd()
        
        # Configuración de credenciales
        self.credentials_dir = os.path.join(self.base_dir, "credentials")
        os.makedirs(self.credentials_dir, exist_ok=True)
        
        logger.info(f"Orquestador de Google Calendar MCP inicializado en {self.base_dir}")
    
    def _get_python_cmd(self) -> str:
        """
        Obtiene el comando de Python 3.13+ disponible en el sistema.
        
        Returns:
            Comando de Python a utilizar
        """
        # Intentar con diferentes versiones de Python
        python_cmds = ["python3.13", "python3.14", "python3.15", "python3"]
        
        for cmd in python_cmds:
            try:
                # Verificar versión
                result = subprocess.run(
                    [cmd, "--version"], 
                    capture_output=True, 
                    text=True
                )
                version = result.stdout.strip()
                logger.info(f"Versión de Python encontrada: {version}")
                
                # Extraer número de versión
                import re
                match = re.search(r"(\d+\.\d+\.\d+)", version)
                if match:
                    version_num = match.group(1)
                    major, minor, _ = map(int, version_num.split("."))
                    
                    # Verificar si es 3.13+
                    if major == 3 and minor >= 13:
                        logger.info(f"Usando {cmd} (versión {version_num})")
                        return cmd
            except Exception as e:
                logger.debug(f"Error al verificar {cmd}: {e}")
                continue
        
        # Si llegamos aquí, no se encontró Python 3.13+
        logger.warning("No se encontró Python 3.13+. El servidor Google Calendar MCP requiere Python 3.13+")
        logger.warning("Usando python3 por defecto, pero puede haber problemas de compatibilidad")
        return "python3"
    
    def _get_uv_cmd(self) -> str:
        """
        Verifica si UV Package Manager está instalado.
        
        Returns:
            Comando de UV a utilizar
        """
        try:
            result = subprocess.run(
                ["uv", "--version"], 
                capture_output=True, 
                text=True
            )
            version = result.stdout.strip()
            logger.info(f"UV Package Manager encontrado: {version}")
            return "uv"
        except Exception as e:
            logger.warning(f"UV Package Manager no encontrado: {e}")
            logger.warning("El servidor Google Calendar MCP requiere UV Package Manager")
            return "uv"  # Devolvemos el comando de todas formas para intentar usarlo
    
    async def start_server(self) -> bool:
        """
        Inicia el servidor MCP de Google Calendar.
        
        Returns:
            True si el servidor se inició correctamente, False en caso contrario
        """
        if self.running:
            logger.info("El servidor Google Calendar MCP ya está en ejecución")
            return True
        
        try:
            # Preparar comando
            cmd = [
                self.uv_cmd,
                "--directory",
                self.base_dir,
                "run",
                "calendar_mcp.py"
            ]
            
            # Configurar variables de entorno
            env = os.environ.copy()
            env["SUPABASE_URL"] = self.supabase_url
            env["SUPABASE_KEY"] = self.supabase_key
            env["SUPABASE_JWT_SECRET"] = self.supabase_jwt_secret
            env["GOOGLE_CALENDAR_CREDENTIALS_DIR"] = self.credentials_dir
            
            # Iniciar proceso
            logger.info(f"Iniciando servidor Google Calendar MCP: {' '.join(cmd)}")
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=self.base_dir
            )
            
            # Esperar un momento para verificar que el proceso no falle inmediatamente
            await asyncio.sleep(2)
            
            if self.process.returncode is None:
                self.running = True
                self.start_time = asyncio.get_event_loop().time()
                logger.info(f"Servidor Google Calendar MCP iniciado con PID {self.process.pid}")
                
                # Iniciar tarea para leer la salida
                asyncio.create_task(self._read_output())
                
                return True
            else:
                logger.error(f"Error al iniciar servidor Google Calendar MCP: código de salida {self.process.returncode}")
                return False
        
        except Exception as e:
            logger.error(f"Error al iniciar servidor Google Calendar MCP: {e}")
            return False
    
    async def _read_output(self):
        """Lee la salida del proceso del servidor MCP y la registra."""
        while self.process and not self.process.stdout.at_eof():
            line = await self.process.stdout.readline()
            if line:
                logger.info(f"[Google Calendar MCP] {line.decode().strip()}")
        
        while self.process and not self.process.stderr.at_eof():
            line = await self.process.stderr.readline()
            if line:
                logger.error(f"[Google Calendar MCP] {line.decode().strip()}")
    
    async def stop_server(self) -> bool:
        """
        Detiene el servidor MCP de Google Calendar.
        
        Returns:
            True si el servidor se detuvo correctamente, False en caso contrario
        """
        if not self.running or not self.process:
            logger.info("El servidor Google Calendar MCP no está en ejecución")
            return True
        
        try:
            logger.info(f"Deteniendo servidor Google Calendar MCP (PID {self.process.pid})")
            
            # Intentar terminar el proceso de forma limpia
            self.process.terminate()
            
            # Esperar a que termine
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
                logger.info("Servidor Google Calendar MCP detenido correctamente")
            except asyncio.TimeoutError:
                # Si no termina en 5 segundos, forzar la terminación
                logger.warning("Timeout al esperar que termine el servidor, forzando terminación")
                self.process.kill()
                await self.process.wait()
            
            self.running = False
            self.process = None
            return True
        
        except Exception as e:
            logger.error(f"Error al detener servidor Google Calendar MCP: {e}")
            return False
    
    async def restart_server(self) -> bool:
        """
        Reinicia el servidor MCP de Google Calendar.
        
        Returns:
            True si el servidor se reinició correctamente, False en caso contrario
        """
        await self.stop_server()
        return await self.start_server()
    
    async def is_running(self) -> bool:
        """
        Verifica si el servidor MCP de Google Calendar está en ejecución.
        
        Returns:
            True si el servidor está en ejecución, False en caso contrario
        """
        if not self.running or not self.process:
            return False
        
        # Verificar si el proceso sigue en ejecución
        if self.process.returncode is not None:
            logger.warning(f"El servidor Google Calendar MCP ha terminado con código {self.process.returncode}")
            self.running = False
            self.process = None
            return False
        
        return True
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado actual del servidor MCP de Google Calendar.
        
        Returns:
            Diccionario con información de estado
        """
        is_running = await self.is_running()
        
        status = {
            "running": is_running,
            "pid": self.process.pid if is_running and self.process else None,
            "uptime": asyncio.get_event_loop().time() - self.start_time if is_running and self.start_time else None,
            "status": "running" if is_running else "stopped",
            "python_version": await self._get_python_version(),
            "uv_version": await self._get_uv_version()
        }
        
        return status
    
    async def _get_python_version(self) -> str:
        """
        Obtiene la versión de Python utilizada.
        
        Returns:
            Versión de Python
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                self.python_cmd, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode() or stderr.decode()
            return output.strip()
        except Exception as e:
            logger.error(f"Error al obtener versión de Python: {e}")
            return "unknown"
    
    async def _get_uv_version(self) -> str:
        """
        Obtiene la versión de UV Package Manager utilizada.
        
        Returns:
            Versión de UV
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                self.uv_cmd, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode() or stderr.decode()
            return output.strip()
        except Exception as e:
            logger.error(f"Error al obtener versión de UV: {e}")
            return "unknown"
    
    async def save_user_credentials(self, user_id: str, credentials: Dict[str, Any]) -> bool:
        """
        Guarda las credenciales de Google Calendar para un usuario.
        
        Args:
            user_id: ID del usuario
            credentials: Credenciales de Google Calendar
        
        Returns:
            True si las credenciales se guardaron correctamente, False en caso contrario
        """
        try:
            # Crear directorio para el usuario si no existe
            user_dir = os.path.join(self.credentials_dir, user_id)
            os.makedirs(user_dir, exist_ok=True)
            
            # Guardar credenciales
            credentials_file = os.path.join(user_dir, "credentials.json")
            with open(credentials_file, "w") as f:
                json.dump(credentials, f)
            
            logger.info(f"Credenciales de Google Calendar guardadas para el usuario {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error al guardar credenciales de Google Calendar para el usuario {user_id}: {e}")
            return False
    
    async def load_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Carga las credenciales de Google Calendar para un usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Credenciales de Google Calendar o None si no existen
        """
        try:
            # Verificar si existen credenciales para el usuario
            credentials_file = os.path.join(self.credentials_dir, user_id, "credentials.json")
            if not os.path.exists(credentials_file):
                logger.warning(f"No existen credenciales de Google Calendar para el usuario {user_id}")
                return None
            
            # Cargar credenciales
            with open(credentials_file, "r") as f:
                credentials = json.load(f)
            
            logger.info(f"Credenciales de Google Calendar cargadas para el usuario {user_id}")
            return credentials
        
        except Exception as e:
            logger.error(f"Error al cargar credenciales de Google Calendar para el usuario {user_id}: {e}")
            return None
    
    async def delete_user_credentials(self, user_id: str) -> bool:
        """
        Elimina las credenciales de Google Calendar para un usuario.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            True si las credenciales se eliminaron correctamente, False en caso contrario
        """
        try:
            # Verificar si existen credenciales para el usuario
            credentials_file = os.path.join(self.credentials_dir, user_id, "credentials.json")
            if not os.path.exists(credentials_file):
                logger.warning(f"No existen credenciales de Google Calendar para el usuario {user_id}")
                return True
            
            # Eliminar credenciales
            os.remove(credentials_file)
            
            # Intentar eliminar el directorio del usuario si está vacío
            user_dir = os.path.join(self.credentials_dir, user_id)
            if os.path.exists(user_dir) and not os.listdir(user_dir):
                os.rmdir(user_dir)
            
            logger.info(f"Credenciales de Google Calendar eliminadas para el usuario {user_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error al eliminar credenciales de Google Calendar para el usuario {user_id}: {e}")
            return False
    
    async def execute_operation(self, user_id: str, operation: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una operación en el servidor MCP de Google Calendar.
        
        Args:
            user_id: ID del usuario
            operation: Nombre de la operación a ejecutar
            arguments: Argumentos para la operación
        
        Returns:
            Resultado de la operación
        """
        # Verificar si el servidor está en ejecución
        if not await self.is_running():
            logger.info("El servidor Google Calendar MCP no está en ejecución, iniciándolo...")
            if not await self.start_server():
                return {
                    "status": "error",
                    "error": "No se pudo iniciar el servidor Google Calendar MCP"
                }
        
        try:
            # Verificar si existen credenciales para el usuario
            credentials = await self.load_user_credentials(user_id)
            if not credentials:
                return {
                    "status": "error",
                    "error": "No existen credenciales de Google Calendar para el usuario"
                }
            
            # Preparar comando para ejecutar la operación
            # Nota: En una implementación real, esto se haría mediante comunicación directa con el servidor MCP
            # a través de un socket o API. Aquí simulamos la ejecución para ilustrar el concepto.
            
            # Simular respuesta según la operación
            if operation == "list_events":
                return {
                    "status": "success",
                    "response": {
                        "result": {
                            "events": [
                                {
                                    "id": "event123",
                                    "summary": "Reunión de equipo",
                                    "start": {"dateTime": "2025-05-20T10:00:00Z"},
                                    "end": {"dateTime": "2025-05-20T11:00:00Z"}
                                },
                                {
                                    "id": "event456",
                                    "summary": "Almuerzo con cliente",
                                    "start": {"dateTime": "2025-05-21T13:00:00Z"},
                                    "end": {"dateTime": "2025-05-21T14:30:00Z"}
                                }
                            ]
                        }
                    }
                }
            elif operation == "create_event":
                return {
                    "status": "success",
                    "response": {
                        "result": {
                            "id": "event789",
                            "summary": arguments.get("summary", "Nuevo evento"),
                            "start": arguments.get("start", {"dateTime": "2025-05-22T15:00:00Z"}),
                            "end": arguments.get("end", {"dateTime": "2025-05-22T16:00:00Z"})
                        }
                    }
                }
            elif operation == "delete_event":
                return {
                    "status": "success",
                    "response": {
                        "result": {
                            "deleted": True,
                            "id": arguments.get("event_id")
                        }
                    }
                }
            elif operation == "update_event":
                return {
                    "status": "success",
                    "response": {
                        "result": {
                            "id": arguments.get("event_id"),
                            "summary": arguments.get("summary", "Evento actualizado"),
                            "start": arguments.get("start", {"dateTime": "2025-05-22T15:00:00Z"}),
                            "end": arguments.get("end", {"dateTime": "2025-05-22T16:00:00Z"}),
                            "updated": True
                        }
                    }
                }
            else:
                return {
                    "status": "error",
                    "error": f"Operación no soportada: {operation}"
                }
        
        except Exception as e:
            logger.error(f"Error al ejecutar operación {operation} en Google Calendar MCP: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
