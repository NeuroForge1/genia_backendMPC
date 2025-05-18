# Guía de Implementación y Despliegue de Servidores MCP en GENIA - Versión Final

## Introducción

Este documento proporciona instrucciones detalladas para implementar, configurar y desplegar todos los servidores MCP (Model Context Protocol) en GENIA. La integración de estos servidores permite que GENIA funcione como un orquestador central que permite a los usuarios ejecutar tareas en múltiples herramientas externas utilizando sus propias cuentas.

## Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Repositorios Creados](#repositorios-creados)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Guía de Instalación](#guía-de-instalación)
5. [Configuración de Servidores](#configuración-de-servidores)
6. [Integración con GENIA](#integración-con-genia)
7. [Pruebas y Validación](#pruebas-y-validación)
8. [Despliegue en Render](#despliegue-en-render)
9. [Solución de Problemas](#solución-de-problemas)
10. [Referencias](#referencias)

## Resumen Ejecutivo

La integración de servidores MCP en GENIA permite a los usuarios conectar sus propias cuentas de servicios externos (GitHub, Notion, Google Workspace, etc.) y ejecutar operaciones en estas plataformas a través de una interfaz unificada. Esta implementación sigue la visión de GENIA como un sistema SaaS que orquesta herramientas externas para automatizar tareas de los usuarios.

**Características principales:**
- Orquestación centralizada de múltiples herramientas externas
- Autenticación por usuario (cada usuario conecta sus propias cuentas)
- API unificada para todas las operaciones
- Gestión segura de tokens y credenciales
- Arquitectura extensible para añadir nuevos servidores MCP

## Repositorios Creados

Se han creado los siguientes repositorios en GitHub para los servidores MCP:

1. [GitHub MCP Server](https://github.com/NeuroForge1/genia-mcp-server-github)
2. [Notion MCP Server](https://github.com/NeuroForge1/genia-mcp-server-notion)
3. [Slack MCP Server](https://github.com/NeuroForge1/genia-mcp-server-slack)
4. [Google Workspace MCP Server](https://github.com/NeuroForge1/genia-mcp-server-google-workspace)
5. [Instagram MCP Server](https://github.com/NeuroForge1/genia-mcp-server-instagram)
6. [Trello MCP Server](https://github.com/NeuroForge1/genia-mcp-server-trello)
7. [Twitter/X MCP Server](https://github.com/NeuroForge1/genia-mcp-server-twitter-x)

Cada repositorio contiene la documentación detallada y el código necesario para implementar el servidor MCP correspondiente.

## Arquitectura del Sistema

La arquitectura de integración de servidores MCP en GENIA consta de tres componentes principales:

1. **Orquestador MCP**: Gestiona el ciclo de vida de los servidores MCP y la comunicación con ellos.
2. **Cliente MCP**: Proporciona una interfaz simplificada para interactuar con los servidores MCP.
3. **API MCP**: Expone endpoints REST para que los servicios de GENIA interactúen con los servidores MCP.

### Diagrama de Arquitectura

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   GENIA     │     │  API MCP    │     │ Cliente MCP │     │ Orquestador │
│  Frontend   │────▶│  Endpoints  │────▶│  Interfaz   │────▶│     MCP     │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                                   │
                    ┌─────────────┐     ┌─────────────┐     ┌──────▼──────┐
                    │  Servicios  │     │ Servidores  │     │ Servidores  │
                    │  Externos   │◀────│    MCP      │◀────│     MCP     │
                    └─────────────┘     └─────────────┘     └─────────────┘
```

### Flujo de Datos

1. El usuario interactúa con el frontend de GENIA
2. El frontend realiza solicitudes a los endpoints de la API MCP
3. La API MCP utiliza el Cliente MCP para ejecutar operaciones
4. El Cliente MCP se comunica con el Orquestador MCP
5. El Orquestador MCP gestiona los Servidores MCP
6. Los Servidores MCP se comunican con los Servicios Externos
7. Los resultados se devuelven a través de la misma cadena

## Guía de Instalación

### Requisitos Previos

#### Software Necesario

- **Docker**: Para ejecutar los contenedores de GitHub y Notion MCP
- **Node.js 16+**: Para los servidores Slack, Instagram y Trello MCP
- **NPM/NPX**: Para ejecutar los servidores basados en Node.js
- **Python 3.8+**: Para el orquestador MCP
- **Rust** (opcional): Para compilar el servidor Google Workspace MCP

#### Dependencias de Python

```bash
pip install asyncio aiohttp fastapi uvicorn pydantic python-dotenv
```

#### Dependencias de Node.js

```bash
npm install -g slack-mcp-server@latest instagram-dm-mcp @delorenj/mcp-server-trello
```

### Pasos de Instalación

1. **Clonar los repositorios**
   ```bash
   # Clonar el repositorio principal de GENIA
   git clone https://github.com/tu-organizacion/genia-backend.git
   cd genia-backend
   
   # Clonar los repositorios de servidores MCP
   mkdir -p mcp-servers
   cd mcp-servers
   git clone https://github.com/NeuroForge1/genia-mcp-server-github.git
   git clone https://github.com/NeuroForge1/genia-mcp-server-notion.git
   git clone https://github.com/NeuroForge1/genia-mcp-server-slack.git
   git clone https://github.com/NeuroForge1/genia-mcp-server-google-workspace.git
   git clone https://github.com/NeuroForge1/genia-mcp-server-instagram.git
   git clone https://github.com/NeuroForge1/genia-mcp-server-trello.git
   git clone https://github.com/NeuroForge1/genia-mcp-server-twitter-x.git
   ```

2. **Copiar archivos de implementación MCP**
   ```bash
   # Crear estructura de directorios
   mkdir -p app/mcp_client/config
   mkdir -p app/api
   
   # Copiar archivos
   cp mcp_orchestrator_extended.py app/mcp_client/
   cp mcp_client_extended.py app/mcp_client/
   cp validate_mcp_extended.py app/mcp_client/
   cp mcp_routes.py app/api/
   ```

3. **Configurar variables de entorno**
   ```bash
   # Crear archivo .env
   cat > .env << EOL
   # Configuración general
   MCP_TOKEN_ENCRYPTION_KEY=your_encryption_key

   # Configuración de Docker
   DOCKER_HOST=unix:///var/run/docker.sock

   # Configuración de base de datos
   DATABASE_URL=postgres://user:password@host:port/database
   EOL
   ```

4. **Instalar dependencias del proyecto**
   ```bash
   pip install -r requirements.txt
   ```

5. **Verificar instalación**
   ```bash
   python -m app.mcp_client.validate_mcp_extended
   ```

## Configuración de Servidores

### Configuración por Servidor

Cada servidor MCP requiere su propia configuración específica. A continuación se detallan las variables de entorno necesarias para cada uno:

#### GitHub MCP Server
```
GITHUB_TOKEN=ghp_your_github_token
```

#### Notion MCP Server
```
NOTION_TOKEN=secret_your_notion_token
```

#### Slack MCP Server
```
SLACK_XOXC_TOKEN=xoxc-your-slack-token
SLACK_XOXD_TOKEN=xoxd-your-slack-token
```

#### Google Workspace MCP Server
```
GOOGLE_ACCESS_TOKEN=your_google_access_token
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token
```

#### Instagram MCP Server
```
INSTAGRAM_SESSION_ID=your_instagram_session_id
INSTAGRAM_CSRF_TOKEN=your_instagram_csrf_token
INSTAGRAM_DS_USER_ID=your_instagram_ds_user_id
```

#### Trello MCP Server
```
TRELLO_API_KEY=your_trello_api_key
TRELLO_TOKEN=your_trello_token
TRELLO_BOARD_ID=your_trello_board_id
```

#### Twitter/X MCP Server
```
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret
```

## Integración con GENIA

### Inicialización del Sistema

Añade el siguiente código en `app/services/mcp_service.py`:

```python
from app.mcp_client.mcp_client_extended import get_mcp_client

async def initialize_mcp():
    """Inicializa el cliente MCP al arrancar la aplicación."""
    client = await get_mcp_client()
    return client

async def execute_tool_operation(user_id, service, operation, arguments):
    """
    Ejecuta una operación en una herramienta externa.
    
    Args:
        user_id: ID del usuario
        service: Nombre del servicio (github, notion, slack, etc.)
        operation: Operación a ejecutar
        arguments: Argumentos para la operación
        
    Returns:
        Resultado de la operación
    """
    client = await get_mcp_client()
    
    if service == "github":
        return await client.execute_github_operation(user_id, operation, arguments)
    elif service == "notion":
        return await client.execute_notion_operation(user_id, operation, arguments)
    elif service == "slack":
        return await client.execute_slack_operation(user_id, operation, arguments)
    elif service == "google_workspace":
        return await client.execute_google_workspace_operation(user_id, operation, arguments)
    elif service == "google_sheets":
        return await client.execute_google_sheets_operation(user_id, operation, arguments)
    elif service == "instagram":
        return await client.execute_instagram_operation(user_id, operation, arguments)
    elif service == "trello":
        return await client.execute_trello_operation(user_id, operation, arguments)
    elif service == "twitter_x":
        return await client.execute_twitter_x_operation(user_id, operation, arguments)
    else:
        raise ValueError(f"Servicio no soportado: {service}")
```

### Inicialización al Arranque

En el archivo principal de la aplicación (por ejemplo, `main.py`):

```python
from app.services.mcp_service import initialize_mcp

@app.on_event("startup")
async def startup_event():
    # Inicializar cliente MCP
    await initialize_mcp()
```

### Registro de Rutas API

En el archivo principal de la aplicación:

```python
from app.api.mcp_routes import router as mcp_router

app.include_router(mcp_router)
```

## Pruebas y Validación

### Pruebas en Entorno Local

Debido a las limitaciones del entorno de sandbox (Docker no disponible), las pruebas reales completas deben realizarse en un entorno con Docker funcional, como Render.

Para ejecutar pruebas simuladas en entorno local:

```bash
python -m app.mcp_client.validate_mcp_extended
```

### Pruebas Reales en Render

Para realizar pruebas reales en Render:

1. Desplegar la aplicación en Render
2. Configurar todas las variables de entorno necesarias
3. Ejecutar el script de pruebas reales:
   ```bash
   python -m app.mcp_client.real_tests_mcp
   ```

### Verificación de Funcionamiento

Para verificar que cada servidor MCP funciona correctamente:

1. Comprobar que el servidor se inicia correctamente
2. Verificar que se puede autenticar con las credenciales proporcionadas
3. Ejecutar una operación simple y verificar la respuesta
4. Comprobar el manejo de errores

## Despliegue en Render

### Configuración en Render

1. **Crear un nuevo servicio Web**
   - Conectar con el repositorio de GitHub
   - Seleccionar la rama principal
   - Configurar el comando de inicio: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Configurar variables de entorno**
   - Añadir todas las variables de entorno necesarias (ver sección de Configuración)
   - Configurar `MCP_TOKEN_ENCRYPTION_KEY` como variable secreta

3. **Configurar dependencias**
   - Asegurarse de que Docker está disponible en el entorno de Render
   - Configurar Node.js y NPM/NPX

### Verificación de Despliegue

1. **Comprobar logs de inicio**
   - Verificar que no hay errores durante el arranque
   - Comprobar que todos los servidores MCP se registran correctamente

2. **Probar endpoints de API**
   - Verificar que los endpoints de conexión funcionan
   - Probar operaciones básicas en cada servicio

3. **Monitorear rendimiento**
   - Comprobar uso de CPU y memoria
   - Verificar tiempos de respuesta

## Solución de Problemas

### Problemas Comunes y Soluciones

#### 1. Error al iniciar servidores Docker

**Problema**: No se pueden iniciar los servidores MCP basados en Docker.

**Solución**:
- Verificar que Docker está instalado y en ejecución: `docker --version`
- Asegurarse de que el usuario tenga permisos para usar Docker: `sudo usermod -aG docker $USER`
- Comprobar la conectividad a Internet para descargar imágenes
- Verificar los logs de Docker: `docker logs <container_id>`

#### 2. Error de autenticación en servicios externos

**Problema**: Los tokens de usuario son rechazados por el servicio externo.

**Solución**:
- Verificar que los tokens sean válidos y no hayan expirado
- Comprobar que los permisos asignados sean suficientes
- Implementar renovación automática de tokens cuando sea posible
- Revisar los logs del servidor MCP para mensajes de error específicos

#### 3. Problemas de rendimiento con múltiples servidores

**Problema**: El sistema se vuelve lento al gestionar múltiples servidores MCP.

**Solución**:
- Implementar inicio bajo demanda de servidores
- Utilizar un sistema de caché para resultados frecuentes
- Considerar implementar un pool de servidores pre-iniciados
- Optimizar la gestión de recursos en el orquestador

### Herramientas de Diagnóstico

1. **Logs del Sistema**
   - Revisar `mcp_validation_extended.log` para resultados de pruebas
   - Revisar `mcp_real_tests.log` para resultados de pruebas reales

2. **Estado de Servidores**
   - Utilizar el endpoint `/api/mcp/status` para verificar el estado de los servidores
   - Implementar un dashboard de monitoreo

3. **Herramientas de Depuración**
   - Utilizar el modo de depuración en el orquestador: `DEBUG=true`
   - Implementar endpoints de diagnóstico para administradores

## Referencias

### Repositorios de Servidores MCP

- [GitHub MCP Server](https://github.com/NeuroForge1/genia-mcp-server-github)
- [Notion MCP Server](https://github.com/NeuroForge1/genia-mcp-server-notion)
- [Slack MCP Server](https://github.com/NeuroForge1/genia-mcp-server-slack)
- [Google Workspace MCP Server](https://github.com/NeuroForge1/genia-mcp-server-google-workspace)
- [Instagram MCP Server](https://github.com/NeuroForge1/genia-mcp-server-instagram)
- [Trello MCP Server](https://github.com/NeuroForge1/genia-mcp-server-trello)
- [Twitter/X MCP Server](https://github.com/NeuroForge1/genia-mcp-server-twitter-x)

### Documentación de APIs

- [GitHub API](https://docs.github.com/en/rest)
- [Notion API](https://developers.notion.com/)
- [Slack API](https://api.slack.com/)
- [Google Drive API](https://developers.google.com/drive/api)
- [Google Sheets API](https://developers.google.com/sheets/api)
- [Instagram Graph API](https://developers.facebook.com/docs/instagram-api/)
- [Trello API](https://developer.atlassian.com/cloud/trello/rest/)
- [Twitter API](https://developer.twitter.com/en/docs/twitter-api)

### Recursos Adicionales

- [Model Context Protocol (MCP) Specification](https://github.com/modelcontextprotocol/spec)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)
- [Render Documentation](https://render.com/docs)

---

## Conclusión

Esta guía proporciona instrucciones detalladas para implementar, configurar y desplegar todos los servidores MCP en GENIA. Siguiendo estos pasos, podrás integrar múltiples servicios externos en GENIA y proporcionar a tus usuarios una experiencia unificada para gestionar sus tareas en diferentes plataformas.

La arquitectura implementada es extensible y escalable, permitiendo añadir fácilmente nuevos servidores MCP en el futuro. Además, el enfoque de autenticación por usuario garantiza que cada usuario pueda conectar sus propias cuentas de servicios externos, alineándose con la visión de GENIA como un sistema SaaS que orquesta herramientas externas para automatizar tareas.
