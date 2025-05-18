# Guía de Implementación de Servidores MCP en GENIA

## Introducción

Este documento proporciona instrucciones detalladas para implementar y configurar los servidores MCP (Model Context Protocol) en GENIA, permitiendo que funcione como un orquestador central de herramientas externas para los usuarios.

## Índice

1. [Requisitos previos](#requisitos-previos)
2. [Estructura de archivos](#estructura-de-archivos)
3. [Instalación y configuración](#instalación-y-configuración)
4. [Integración con GENIA](#integración-con-genia)
5. [Pruebas y validación](#pruebas-y-validación)
6. [Despliegue en producción](#despliegue-en-producción)
7. [Mantenimiento y escalabilidad](#mantenimiento-y-escalabilidad)
8. [Solución de problemas](#solución-de-problemas)

## Requisitos previos

### Software necesario

- **Docker**: Para ejecutar los contenedores de GitHub y Notion MCP
  ```bash
  # Verificar instalación
  docker --version
  
  # Instalar en Ubuntu si es necesario
  sudo apt-get update
  sudo apt-get install docker.io
  sudo systemctl enable --now docker
  ```

- **Node.js y NPM/NPX**: Para el servidor Slack MCP
  ```bash
  # Verificar instalación
  node --version
  npm --version
  npx --version
  
  # Instalar en Ubuntu si es necesario
  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  sudo apt-get install -y nodejs
  ```

- **Python 3.8+**: Para el orquestador MCP
  ```bash
  # Verificar instalación
  python3 --version
  pip3 --version
  
  # Instalar dependencias
  pip3 install asyncio aiohttp
  ```

### Tokens y credenciales

#### GitHub

1. Accede a [https://github.com/settings/tokens](https://github.com/settings/tokens)
2. Haz clic en "Generate new token" (classic)
3. Asigna un nombre descriptivo como "GENIA MCP Integration"
4. Selecciona los siguientes permisos:
   - `repo` (completo)
   - `user` (solo lectura)
   - `read:org` (opcional)
5. Genera el token y guárdalo de forma segura

#### Notion

1. Accede a [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Haz clic en "+ New integration"
3. Asigna un nombre como "GENIA Integration"
4. Selecciona el workspace donde se usará
5. Configura los permisos necesarios (lectura/escritura de contenido)
6. Copia el "Internal Integration Token" generado

#### Slack

1. Abre Slack en tu navegador web
2. Abre las herramientas de desarrollador (F12 o Ctrl+Shift+I)
3. En la consola, ejecuta:
   ```javascript
   // Para obtener el token xoxc
   JSON.parse(localStorage.localConfig_v2).teams[document.location.pathname.match(/^\/client\/([A-Z0-9]+)/)[1]].token
   ```
4. Para el token xoxd, ve a la pestaña Application > Cookies y copia el valor de la cookie `d`

## Estructura de archivos

```
genia_backendMPC/
├── app/
│   ├── mcp_client/
│   │   ├── __init__.py
│   │   ├── mcp_orchestrator.py    # Orquestador central de MCP
│   │   ├── mcp_client.py          # Cliente para servicios GENIA
│   │   ├── validate_mcp.py        # Script de validación
│   │   └── config/                # Directorio para tokens y configuración
│   ├── api/
│   │   ├── __init__.py
│   │   └── mcp_routes.py          # Endpoints para interactuar con MCP
│   └── services/
│       ├── __init__.py
│       └── mcp_service.py         # Servicio para lógica de negocio MCP
└── docs/
    └── integracion_servidores_mcp_24h.md  # Documentación general
```

## Instalación y configuración

### 1. Clonar el repositorio

```bash
git clone <repositorio-genia>
cd genia_backendMPC
```

### 2. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```
# Tokens por defecto (solo para desarrollo)
GITHUB_TOKEN=ghp_your_github_token
NOTION_TOKEN=secret_your_notion_token
SLACK_XOXC_TOKEN=xoxc-your-slack-token
SLACK_XOXD_TOKEN=xoxd-your-slack-token

# Configuración de Docker
DOCKER_HOST=unix:///var/run/docker.sock

# Configuración de seguridad
MCP_TOKEN_ENCRYPTION_KEY=your_encryption_key
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Crear estructura de directorios

```bash
mkdir -p app/mcp_client/config
```

### 5. Verificar permisos de Docker

```bash
# Asegúrate de que el usuario tenga permisos para usar Docker
sudo usermod -aG docker $USER
# Reinicia la sesión para aplicar los cambios
```

## Integración con GENIA

### 1. Inicializar el cliente MCP

Añade el siguiente código en `app/services/mcp_service.py`:

```python
from app.mcp_client.mcp_client import get_mcp_client

async def initialize_mcp():
    """Inicializa el cliente MCP al arrancar la aplicación."""
    client = await get_mcp_client()
    return client

async def execute_tool_operation(user_id, tool, operation, arguments):
    """
    Ejecuta una operación en una herramienta externa.
    
    Args:
        user_id: ID del usuario
        tool: Nombre de la herramienta (github, notion, slack)
        operation: Operación a ejecutar
        arguments: Argumentos para la operación
        
    Returns:
        Resultado de la operación
    """
    client = await get_mcp_client()
    
    if tool == "github":
        return await client.execute_github_operation(user_id, operation, arguments)
    elif tool == "notion":
        return await client.execute_notion_operation(user_id, operation, arguments)
    elif tool == "slack":
        return await client.execute_slack_operation(user_id, operation, arguments)
    else:
        raise ValueError(f"Herramienta no soportada: {tool}")
```

### 2. Crear endpoints para interactuar con MCP

Añade el siguiente código en `app/api/mcp_routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
from app.services.mcp_service import execute_tool_operation
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/mcp", tags=["mcp"])

@router.post("/execute")
async def execute_mcp_operation(
    tool: str,
    operation: str,
    arguments: Dict[str, Any] = Body(...),
    current_user = Depends(get_current_user)
):
    """
    Ejecuta una operación en una herramienta externa a través de MCP.
    """
    try:
        result = await execute_tool_operation(
            user_id=current_user.id,
            tool=tool,
            operation=operation,
            arguments=arguments
        )
        return {"status": "success", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar operación: {str(e)}")

@router.post("/connect/{tool}")
async def connect_tool(
    tool: str,
    tokens: Dict[str, str] = Body(...),
    current_user = Depends(get_current_user)
):
    """
    Conecta una herramienta externa para un usuario.
    """
    try:
        client = await get_mcp_client()
        result = await client.save_user_tokens(current_user.id, tool, tokens)
        return {"status": "success", "connected": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar herramienta: {str(e)}")
```

### 3. Integrar con el sistema de autenticación

Asegúrate de que el sistema de autenticación de GENIA proporcione el ID de usuario para las operaciones MCP.

### 4. Añadir inicialización al arranque de la aplicación

En el archivo principal de la aplicación (por ejemplo, `main.py`):

```python
from app.services.mcp_service import initialize_mcp

@app.on_event("startup")
async def startup_event():
    # Inicializar cliente MCP
    await initialize_mcp()
```

## Pruebas y validación

### 1. Ejecutar script de validación

```bash
cd genia_backendMPC
python -m app.mcp_client.validate_mcp
```

### 2. Verificar logs

Revisa el archivo `mcp_validation.log` para verificar que todas las pruebas hayan pasado correctamente.

### 3. Probar endpoints

Usa herramientas como Postman o curl para probar los endpoints:

```bash
# Ejemplo con curl
curl -X POST "http://localhost:8000/mcp/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "tool": "github",
    "operation": "get_me",
    "arguments": {}
  }'
```

## Despliegue en producción

### 1. Configuración en Render

1. Accede al panel de control de Render
2. Selecciona el servicio `genia-backendMPC`
3. Ve a la sección "Environment"
4. Añade las siguientes variables de entorno:
   - `GITHUB_TOKEN`: Token por defecto para GitHub (opcional)
   - `NOTION_TOKEN`: Token por defecto para Notion (opcional)
   - `SLACK_XOXC_TOKEN`: Token por defecto para Slack (opcional)
   - `SLACK_XOXD_TOKEN`: Token por defecto para Slack (opcional)
   - `MCP_TOKEN_ENCRYPTION_KEY`: Clave para cifrar tokens de usuarios
   - `DOCKER_HOST`: Configuración para acceso a Docker (si es necesario)

### 2. Habilitar Docker en Render

Para usar Docker dentro de Render, necesitarás un plan que soporte Docker-in-Docker o usar una solución alternativa como:

1. Desplegar los servidores MCP como servicios independientes
2. Usar la API de Docker para gestionar contenedores remotos
3. Implementar versiones nativas de los servidores MCP sin Docker

### 3. Configuración de base de datos para tokens

Configura Supabase para almacenar los tokens de usuario de forma segura:

1. Crea una tabla `user_tokens` con la siguiente estructura:
   - `id`: UUID (primary key)
   - `user_id`: UUID (foreign key a tabla users)
   - `service`: String (github, notion, slack)
   - `tokens`: JSON (tokens cifrados)
   - `created_at`: Timestamp
   - `updated_at`: Timestamp

2. Implementa funciones para cifrar/descifrar tokens antes de guardarlos

## Mantenimiento y escalabilidad

### Añadir nuevos servidores MCP

Para añadir un nuevo servidor MCP:

1. Analiza su README y requisitos de despliegue
2. Añade la configuración en `mcp_orchestrator.py`
3. Implementa métodos específicos en `mcp_client.py`
4. Actualiza los endpoints en `mcp_routes.py`
5. Añade pruebas en `validate_mcp.py`

### Monitoreo y logs

Configura un sistema de monitoreo para:

1. Verificar el estado de los servidores MCP
2. Registrar errores y excepciones
3. Medir tiempos de respuesta y uso de recursos
4. Alertar sobre problemas críticos

## Solución de problemas

### Problemas comunes y soluciones

1. **Error al iniciar Docker**
   - Verifica que Docker esté instalado y en ejecución
   - Asegúrate de que el usuario tenga permisos adecuados
   - Comprueba la configuración de red y firewall

2. **Error al ejecutar NPX**
   - Verifica que Node.js y NPM estén instalados
   - Actualiza NPM a la última versión
   - Comprueba la conexión a internet

3. **Tokens inválidos o expirados**
   - Regenera los tokens según las instrucciones
   - Verifica los permisos asignados a cada token
   - Comprueba la fecha de expiración de los tokens

4. **Problemas de comunicación entre componentes**
   - Verifica la configuración de red
   - Comprueba que los puertos necesarios estén abiertos
   - Revisa los logs para identificar errores específicos

### Contacto y soporte

Para obtener ayuda adicional:

- Consulta la documentación oficial de cada servidor MCP
- Revisa los issues en los repositorios correspondientes
- Contacta al equipo de desarrollo de GENIA

---

## Conclusión

Siguiendo esta guía, habrás implementado con éxito los servidores MCP en GENIA, permitiendo que funcione como un orquestador central de herramientas externas para tus usuarios. Esta implementación sienta las bases para un sistema SaaS completo que permite a los usuarios ejecutar cualquier tarea autenticando sus propias herramientas.
