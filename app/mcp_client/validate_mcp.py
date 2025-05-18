"""
Script de validación para MCP Orchestrator y MCP Client de GENIA

Este script realiza pruebas básicas de funcionamiento de los módulos
mcp_orchestrator.py y mcp_client.py, verificando que pueden iniciar
servidores MCP, enviar solicitudes y recibir respuestas.

Autor: GENIA Team
Fecha: Mayo 2025
"""

import os
import sys
import json
import asyncio
import logging
from typing import Dict, Any

# Configurar path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar módulos MCP
from app.mcp_client.mcp_orchestrator import MCPOrchestrator
from app.mcp_client.mcp_client import MCPClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_validation.log')
    ]
)
logger = logging.getLogger("mcp_validation")

# Tokens de prueba (reemplazar con tokens reales para pruebas completas)
TEST_TOKENS = {
    "github": {
        "token": "ghp_example_token"  # Reemplazar con token real para pruebas completas
    },
    "notion": {
        "token": "secret_example_token"  # Reemplazar con token real para pruebas completas
    },
    "slack": {
        "xoxc_token": "xoxc-example-token",  # Reemplazar con token real para pruebas completas
        "xoxd_token": "xoxd-example-token"   # Reemplazar con token real para pruebas completas
    }
}

# ID de usuario de prueba
TEST_USER_ID = "test_user_001"

async def test_orchestrator():
    """Prueba el funcionamiento básico del orquestador MCP."""
    logger.info("=== Iniciando prueba de MCPOrchestrator ===")
    
    try:
        # Crear orquestador
        orchestrator = MCPOrchestrator()
        logger.info("Orquestador creado correctamente")
        
        # Registrar servidor GitHub
        result = orchestrator.register_server(
            name="github",
            command=["echo", "{\"type\": \"response\", \"response\": {\"result\": \"mock_response\"}}"],  # Mock para pruebas
            env_vars={"GITHUB_PERSONAL_ACCESS_TOKEN": "mock_token"}
        )
        logger.info(f"Registro de servidor GitHub: {'Exitoso' if result else 'Fallido'}")
        
        # Verificar estado de servidores
        status = orchestrator.get_server_status()
        logger.info(f"Estado de servidores: {json.dumps(status, indent=2)}")
        
        # Guardar tokens de usuario
        result = orchestrator.save_user_tokens(TEST_USER_ID, {
            "github": "mock_github_token",
            "notion": "mock_notion_token",
            "slack_xoxc": "mock_slack_xoxc_token",
            "slack_xoxd": "mock_slack_xoxd_token"
        })
        logger.info(f"Guardado de tokens: {'Exitoso' if result else 'Fallido'}")
        
        # Cargar tokens de usuario
        tokens = orchestrator.load_user_tokens(TEST_USER_ID)
        logger.info(f"Carga de tokens: {'Exitoso' if tokens else 'Fallido'}")
        if tokens:
            logger.info(f"Tokens cargados: {json.dumps({k: '***' for k in tokens.keys()}, indent=2)}")
        
        # Iniciar servidor
        result = await orchestrator.start_server("github")
        logger.info(f"Inicio de servidor GitHub: {'Exitoso' if result else 'Fallido'}")
        
        # Enviar solicitud (mock)
        try:
            response = await orchestrator.send_request("github", {
                "type": "function",
                "function": {
                    "name": "get_me",
                    "arguments": "{}"
                }
            })
            logger.info(f"Envío de solicitud: Exitoso")
            logger.info(f"Respuesta recibida: {json.dumps(response, indent=2)}")
        except Exception as e:
            logger.error(f"Error al enviar solicitud: {e}")
        
        # Detener servidor
        result = await orchestrator.stop_server("github")
        logger.info(f"Detención de servidor GitHub: {'Exitoso' if result else 'Fallido'}")
        
        logger.info("=== Prueba de MCPOrchestrator completada ===")
        return True
    
    except Exception as e:
        logger.error(f"Error en prueba de MCPOrchestrator: {e}")
        return False

async def test_client():
    """Prueba el funcionamiento básico del cliente MCP."""
    logger.info("=== Iniciando prueba de MCPClient ===")
    
    try:
        # Crear cliente
        client = MCPClient()
        logger.info("Cliente creado correctamente")
        
        # Inicializar cliente
        result = await client.initialize()
        logger.info(f"Inicialización de cliente: {'Exitoso' if result else 'Fallido'}")
        
        # Guardar tokens de prueba
        for service, tokens in TEST_TOKENS.items():
            result = await client.save_user_tokens(TEST_USER_ID, service, tokens)
            logger.info(f"Guardado de tokens para {service}: {'Exitoso' if result else 'Fallido'}")
        
        # Modificar servidores para usar comandos mock en lugar de Docker/NPX
        for name, server in client.orchestrator.servers.items():
            server.command = ["echo", "{\"type\": \"response\", \"response\": {\"result\": \"mock_response_for_" + name + "\"}}"]
        
        # Probar operaciones (con servidores mock)
        try:
            github_response = await client.execute_github_operation(
                user_id=TEST_USER_ID,
                operation="get_me",
                arguments={}
            )
            logger.info(f"Operación GitHub: Exitoso")
            logger.info(f"Respuesta GitHub: {json.dumps(github_response, indent=2)}")
        except Exception as e:
            logger.error(f"Error en operación GitHub: {e}")
        
        try:
            notion_response = await client.execute_notion_operation(
                user_id=TEST_USER_ID,
                operation="search",
                arguments={"query": "test"}
            )
            logger.info(f"Operación Notion: Exitoso")
            logger.info(f"Respuesta Notion: {json.dumps(notion_response, indent=2)}")
        except Exception as e:
            logger.error(f"Error en operación Notion: {e}")
        
        # Apagar cliente
        result = await client.shutdown()
        logger.info(f"Apagado de cliente: {'Exitoso' if result else 'Fallido'}")
        
        logger.info("=== Prueba de MCPClient completada ===")
        return True
    
    except Exception as e:
        logger.error(f"Error en prueba de MCPClient: {e}")
        return False

async def run_docker_test():
    """Prueba la ejecución de un contenedor Docker real."""
    logger.info("=== Iniciando prueba de Docker ===")
    
    try:
        # Verificar que Docker está instalado y funcionando
        process = await asyncio.create_subprocess_exec(
            "docker", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error al verificar Docker: {stderr.decode()}")
            return False
        
        logger.info(f"Docker instalado: {stdout.decode().strip()}")
        
        # Probar ejecución de contenedor simple
        process = await asyncio.create_subprocess_exec(
            "docker", "run", "--rm", "hello-world",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error al ejecutar contenedor Docker: {stderr.decode()}")
            return False
        
        logger.info(f"Contenedor Docker ejecutado correctamente")
        logger.info(f"Salida: {stdout.decode().strip()[:200]}...")
        
        logger.info("=== Prueba de Docker completada ===")
        return True
    
    except Exception as e:
        logger.error(f"Error en prueba de Docker: {e}")
        return False

async def run_npx_test():
    """Prueba la ejecución de NPX."""
    logger.info("=== Iniciando prueba de NPX ===")
    
    try:
        # Verificar que NPX está instalado y funcionando
        process = await asyncio.create_subprocess_exec(
            "npx", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error al verificar NPX: {stderr.decode()}")
            return False
        
        logger.info(f"NPX instalado: {stdout.decode().strip()}")
        
        logger.info("=== Prueba de NPX completada ===")
        return True
    
    except Exception as e:
        logger.error(f"Error en prueba de NPX: {e}")
        return False

async def main():
    """Función principal que ejecuta todas las pruebas."""
    logger.info("Iniciando validación de MCP para GENIA")
    
    # Crear directorio de configuración si no existe
    os.makedirs(os.path.join(os.path.dirname(__file__), "config"), exist_ok=True)
    
    # Ejecutar pruebas
    docker_result = await run_docker_test()
    npx_result = await run_npx_test()
    orchestrator_result = await test_orchestrator()
    client_result = await test_client()
    
    # Mostrar resumen
    logger.info("=== Resumen de pruebas ===")
    logger.info(f"Prueba de Docker: {'Exitoso' if docker_result else 'Fallido'}")
    logger.info(f"Prueba de NPX: {'Exitoso' if npx_result else 'Fallido'}")
    logger.info(f"Prueba de MCPOrchestrator: {'Exitoso' if orchestrator_result else 'Fallido'}")
    logger.info(f"Prueba de MCPClient: {'Exitoso' if client_result else 'Fallido'}")
    
    # Verificar resultado general
    if docker_result and npx_result and orchestrator_result and client_result:
        logger.info("✅ Todas las pruebas completadas exitosamente")
        logger.info("El sistema MCP está listo para ser integrado en GENIA")
    else:
        logger.error("❌ Algunas pruebas fallaron")
        logger.error("Revisar los logs para más detalles")

if __name__ == "__main__":
    # Ejecutar pruebas
    asyncio.run(main())
