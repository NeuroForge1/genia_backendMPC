# Documentación de Integración de Servidores MCP en GENIA

## Introducción

Este documento proporciona instrucciones detalladas para implementar y configurar todos los servidores MCP (Model Context Protocol) en GENIA, permitiendo que funcione como un orquestador central de herramientas externas para los usuarios.

## Índice

1. [Visión General](#visión-general)
2. [Servidores MCP Integrados](#servidores-mcp-integrados)
3. [Arquitectura de Integración](#arquitectura-de-integración)
4. [Requisitos Previos](#requisitos-previos)
5. [Instalación y Configuración](#instalación-y-configuración)
6. [Autenticación y Gestión de Tokens](#autenticación-y-gestión-de-tokens)
7. [API y Endpoints](#api-y-endpoints)
8. [Ejemplos de Uso](#ejemplos-de-uso)
9. [Despliegue en Producción](#despliegue-en-producción)
10. [Solución de Problemas](#solución-de-problemas)

## Visión General

GENIA funciona como un orquestador central que permite a los usuarios ejecutar tareas en múltiples herramientas externas utilizando sus propias cuentas. La integración de servidores MCP permite a GENIA comunicarse con estas herramientas de manera estandarizada, gestionando la autenticación, el ciclo de vida de los procesos y la comunicación entre componentes.

### Características Principales

- **Orquestación Centralizada**: GENIA gestiona todos los servidores MCP desde un punto central
- **Autenticación por Usuario**: Cada usuario conecta sus propias cuentas de servicios externos
- **Gestión de Tokens Segura**: Los tokens de usuario se almacenan de forma segura y cifrada
- **API Unificada**: Interfaz REST para interactuar con todos los servicios externos
- **Escalabilidad**: Fácil adición de nuevos servidores MCP sin modificar el núcleo del sistema

## Servidores MCP Integrados

### GitHub MCP Server
- **Funcionalidades**: Gestión de repositorios, issues, pull requests
- **Autenticación**: Token personal de acceso (PAT)
- **Operaciones Principales**: `get_me`, `get_my_repos`, `create_issue`

### Notion MCP Server
- **Funcionalidades**: Búsqueda, lectura y escritura de páginas y bases de datos
- **Autenticación**: Token de integración interna
- **Operaciones Principales**: `search`, `get_page`, `create_page`

### Slack MCP Server
- **Funcionalidades**: Envío de mensajes, lectura de canales
- **Autenticación**: Tokens xoxc y xoxd
- **Operaciones Principales**: `post_message`, `get_channels`, `get_messages`

### Google Workspace MCP Server
- **Funcionalidades**: Gestión de archivos en Drive
- **Autenticación**: Token de acceso OAuth, token de actualización
- **Operaciones Principales**: `list_files`, `create_file`, `get_file`

### Google Sheets MCP Server
- **Funcionalidades**: Lectura y escritura de hojas de cálculo
- **Autenticación**: Token de acceso OAuth, token de actualización
- **Operaciones Principales**: `read_values`, `write_values`, `create_spreadsheet`

### Instagram DM MCP Server
- **Funcionalidades**: Lectura y envío de mensajes directos
- **Autenticación**: Cookies de sesión (session_id, csrf_token, ds_user_id)
- **Operaciones Principales**: `get_recent_messages`, `send_message`

### Trello MCP Server
- **Funcionalidades**: Gestión de tableros, listas y tarjetas
- **Autenticación**: API Key y Token
- **Operaciones Principales**: `get_lists`, `get_cards_by_list_id`, `add_card_to_list`

### Twitter/X MCP Server
- **Funcionalidades**: Lectura de timeline, publicación de tweets
- **Autenticación**: API Key, API Secret, Access Token, Access Secret
- **Operaciones Principales**: `get_home_timeline`, `create_tweet`, `reply_to_tweet`

## Arquitectura de Integración

La integración de servidores MCP en GENIA sigue una arquitectura de tres capas:

1. **Capa de Orquestación**: Gestiona el ciclo de vida de los servidores MCP
   - `mcp_orchestrator_extended.py`: Orquestador central para todos los servidores MCP

2. **Capa de Cliente**: Proporciona una interfaz simplificada para interactuar con los servidores
   - `mcp_client_extended.py`: Cliente para todos los servidores MCP

3. **Capa de API**: Expone endpoints REST para que los servicios de GENIA interactúen con los servidores
   - `mcp_routes.py`: Endpoints para conectar cuentas y ejecutar operaciones

### Diagrama de Flujo

```
Usuario -> GENIA Frontend -> GENIA Backend -> MCP API -> MCP Client -> MCP Orchestrator -> Servidores MCP -> Servicios Externos
```

## Requisitos Previos

### Software Necesario

- **Docker**: Para ejecutar los contenedores de GitHub y Notion MCP
- **Node.js y NPM/NPX**: Para los servidores Slack, Instagram y Trello MCP
- **Python 3.8+**: Para el orquestador MCP
- **Rust** (opcional): Para compilar el servidor Google Workspace MCP

### Dependencias de Python

```bash
pip install asyncio aiohttp fastapi uvicorn
```

### Dependencias de Node.js

```bash
npm install -g slack-mcp-server@latest instagram-dm-mcp @delorenj/mcp-server-trello
```

## Instalación y Configuración

### 1. Estructura de Directorios

```
genia_backendMPC/
├── app/
│   ├── mcp_client/
│   │   ├── __init__.py
│   │   ├── mcp_orchestrator_extended.py
│   │   ├── mcp_client_extended.py
│   │   ├── validate_mcp_extended.py
│   │   └── config/                # Directorio para tokens y configuración
│   ├── api/
│   │   ├── __init__.py
│   │   └── mcp_routes.py
│   └── services/
│       ├── __init__.py
│       └── mcp_service.py
└── docs/
    └── integracion_servidores_mcp.md
```

### 2. Configuración de Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```
# Configuración general
MCP_TOKEN_ENCRYPTION_KEY=your_encryption_key

# GitHub MCP
GITHUB_TOKEN=ghp_your_github_token

# Notion MCP
NOTION_TOKEN=secret_your_notion_token

# Slack MCP
SLACK_XOXC_TOKEN=xoxc-your-slack-token
SLACK_XOXD_TOKEN=xoxd-your-slack-token

# Google Workspace MCP
GOOGLE_ACCESS_TOKEN=your_google_access_token
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token

# Instagram MCP
INSTAGRAM_SESSION_ID=your_instagram_session_id
INSTAGRAM_CSRF_TOKEN=your_instagram_csrf_token
INSTAGRAM_DS_USER_ID=your_instagram_ds_user_id

# Trello MCP
TRELLO_API_KEY=your_trello_api_key
TRELLO_TOKEN=your_trello_token
TRELLO_BOARD_ID=your_trello_board_id

# Twitter/X MCP
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret
```

### 3. Inicialización del Sistema

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

### 4. Inicialización al Arranque

En el archivo principal de la aplicación (por ejemplo, `main.py`):

```python
from app.services.mcp_service import initialize_mcp

@app.on_event("startup")
async def startup_event():
    # Inicializar cliente MCP
    await initialize_mcp()
```

## Autenticación y Gestión de Tokens

### Flujo de Autenticación

1. El usuario se autentica en GENIA
2. El usuario conecta sus cuentas de servicios externos a través de la interfaz de GENIA
3. GENIA almacena los tokens de forma segura asociados al ID del usuario
4. Cuando el usuario solicita una operación, GENIA utiliza sus tokens para autenticarse con el servicio correspondiente

### Almacenamiento de Tokens

Los tokens se almacenan de forma segura en:

1. **Desarrollo**: Archivos JSON cifrados en el directorio `app/mcp_client/config/`
2. **Producción**: Base de datos Supabase con cifrado adicional

### Ejemplo de Conexión de Cuenta

```python
# Conectar cuenta de GitHub
await client.save_user_tokens(
    user_id="user123",
    service="github",
    tokens={"token": "ghp_user_personal_token"}
)

# Conectar cuenta de Google Workspace
await client.save_user_tokens(
    user_id="user123",
    service="google_workspace",
    tokens={
        "access_token": "user_access_token",
        "client_id": "user_client_id",
        "client_secret": "user_client_secret",
        "refresh_token": "user_refresh_token"
    }
)
```

## API y Endpoints

### Endpoints Principales

#### Gestión de Conexiones

- `GET /api/mcp/connections`: Obtiene las conexiones activas del usuario
- `POST /api/mcp/connect/{service}`: Conecta una cuenta de servicio externo
- `DELETE /api/mcp/disconnect/{service}`: Desconecta una cuenta de servicio externo

#### Ejecución de Operaciones

- `POST /api/mcp/execute/{service}/{operation}`: Ejecuta una operación en un servicio externo

#### Endpoints Específicos por Servicio

- `GET /api/mcp/github/repos`: Obtiene los repositorios del usuario en GitHub
- `GET /api/mcp/notion/search`: Busca en Notion del usuario
- `GET /api/mcp/google/files`: Lista archivos en Google Drive del usuario
- `GET /api/mcp/instagram/messages`: Obtiene mensajes directos de Instagram del usuario
- `GET /api/mcp/trello/lists`: Obtiene las listas del tablero de Trello del usuario
- `GET /api/mcp/twitter/timeline`: Obtiene la línea de tiempo de Twitter/X del usuario

#### Estado del Sistema

- `GET /api/mcp/status`: Obtiene el estado de los servidores MCP

### Ejemplos de Solicitudes

#### Conectar Cuenta de GitHub

```http
POST /api/mcp/connect/github
Content-Type: application/json

{
  "token": "ghp_user_personal_token"
}
```

#### Ejecutar Operación en Google Workspace

```http
POST /api/mcp/execute/google_workspace/list_files
Content-Type: application/json

{
  "pageSize": 10,
  "query": "mimeType='application/pdf'"
}
```

## Ejemplos de Uso

### Ejemplo 1: Buscar en Notion y Crear Tarjeta en Trello

```javascript
// Frontend (React)
async function searchNotionAndCreateTrelloCard() {
  // 1. Buscar en Notion
  const notionResponse = await fetch('/api/mcp/notion/search?query=proyecto');
  const notionData = await notionResponse.json();
  
  // 2. Crear tarjeta en Trello con los resultados
  const trelloResponse = await fetch('/api/mcp/execute/trello/add_card_to_list', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      listId: "60d21b4c7f96d10081ba9812",
      name: "Resultados de búsqueda en Notion",
      description: JSON.stringify(notionData.results, null, 2)
    })
  });
  
  return await trelloResponse.json();
}
```

### Ejemplo 2: Publicar Tweet con Datos de Google Sheets

```python
# Backend (Python)
async def tweet_google_sheets_data(user_id, spreadsheet_id, range):
    # 1. Leer datos de Google Sheets
    sheets_result = await execute_tool_operation(
        user_id=user_id,
        service="google_sheets",
        operation="read_values",
        arguments={
            "spreadsheetId": spreadsheet_id,
            "range": range
        }
    )
    
    # 2. Formatear datos para tweet
    values = sheets_result.get("response", {}).get("result", {}).get("values", [])
    tweet_text = "Datos actualizados:\n"
    for row in values[:3]:  # Primeras 3 filas
        tweet_text += " - " + " | ".join(row) + "\n"
    
    # 3. Publicar tweet
    tweet_result = await execute_tool_operation(
        user_id=user_id,
        service="twitter_x",
        operation="create_tweet",
        arguments={
            "text": tweet_text
        }
    )
    
    return tweet_result
```

## Despliegue en Producción

### Configuración en Render

1. Accede al panel de control de Render
2. Selecciona el servicio `genia-backend`
3. Ve a la sección "Environment"
4. Añade todas las variables de entorno necesarias (ver sección de Configuración)

### Configuración de Base de Datos en Supabase

1. Crea una tabla `user_tokens` con la siguiente estructura:
   - `id`: UUID (primary key)
   - `user_id`: UUID (foreign key a tabla users)
   - `service`: String (github, notion, slack, etc.)
   - `tokens`: JSON (tokens cifrados)
   - `created_at`: Timestamp
   - `updated_at`: Timestamp

2. Implementa funciones para cifrar/descifrar tokens antes de guardarlos

### Consideraciones de Seguridad

- Utiliza HTTPS para todas las comunicaciones
- Cifra los tokens en reposo y en tránsito
- Implementa rotación de tokens cuando sea posible
- Utiliza permisos mínimos necesarios para cada servicio
- Monitorea el uso de tokens y revoca accesos sospechosos

## Solución de Problemas

### Problemas Comunes y Soluciones

#### 1. Error al iniciar servidores Docker

**Problema**: No se pueden iniciar los servidores MCP basados en Docker.

**Solución**:
- Verifica que Docker esté instalado y en ejecución
- Asegúrate de que el usuario tenga permisos para usar Docker
- Comprueba la conectividad a Internet para descargar imágenes

#### 2. Error de autenticación en servicios externos

**Problema**: Los tokens de usuario son rechazados por el servicio externo.

**Solución**:
- Verifica que los tokens sean válidos y no hayan expirado
- Comprueba que los permisos asignados sean suficientes
- Implementa renovación automática de tokens cuando sea posible

#### 3. Problemas de rendimiento con múltiples servidores

**Problema**: El sistema se vuelve lento al gestionar múltiples servidores MCP.

**Solución**:
- Implementa inicio bajo demanda de servidores
- Utiliza un sistema de caché para resultados frecuentes
- Considera implementar un pool de servidores pre-iniciados

### Logs y Monitoreo

- Configura logs detallados para cada servidor MCP
- Implementa monitoreo de estado y rendimiento
- Configura alertas para errores críticos

### Contacto y Soporte

Para obtener ayuda adicional:

- Consulta la documentación oficial de cada servidor MCP
- Revisa los issues en los repositorios correspondientes
- Contacta al equipo de desarrollo de GENIA

---

## Conclusión

Esta documentación proporciona una guía completa para implementar y configurar todos los servidores MCP en GENIA, permitiendo que funcione como un orquestador central de herramientas externas para los usuarios. Siguiendo estas instrucciones, podrás integrar múltiples servicios externos en GENIA y proporcionar a tus usuarios una experiencia unificada para gestionar sus tareas en diferentes plataformas.
