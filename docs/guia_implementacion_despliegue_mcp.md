# Guía de Implementación y Despliegue de Servidores MCP en GENIA

## Introducción

Este documento proporciona instrucciones paso a paso para implementar, configurar y desplegar todos los servidores MCP (Model Context Protocol) en GENIA. La integración de estos servidores permite que GENIA funcione como un orquestador central que permite a los usuarios ejecutar tareas en múltiples herramientas externas utilizando sus propias cuentas.

## Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Servidores MCP Implementados](#servidores-mcp-implementados)
4. [Guía de Instalación](#guía-de-instalación)
5. [Configuración de Servidores](#configuración-de-servidores)
6. [Integración con GENIA](#integración-con-genia)
7. [Interfaz de Usuario](#interfaz-de-usuario)
8. [Pruebas y Validación](#pruebas-y-validación)
9. [Despliegue en Producción](#despliegue-en-producción)
10. [Mantenimiento y Escalabilidad](#mantenimiento-y-escalabilidad)
11. [Solución de Problemas](#solución-de-problemas)
12. [Referencias](#referencias)

## Resumen Ejecutivo

La integración de servidores MCP en GENIA permite a los usuarios conectar sus propias cuentas de servicios externos (GitHub, Notion, Google Workspace, etc.) y ejecutar operaciones en estas plataformas a través de una interfaz unificada. Esta implementación sigue la visión de GENIA como un sistema SaaS que orquesta herramientas externas para automatizar tareas de los usuarios.

**Características principales:**
- Orquestación centralizada de múltiples herramientas externas
- Autenticación por usuario (cada usuario conecta sus propias cuentas)
- API unificada para todas las operaciones
- Gestión segura de tokens y credenciales
- Arquitectura extensible para añadir nuevos servidores MCP

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

## Servidores MCP Implementados

Se han implementado los siguientes servidores MCP en GENIA:

### 1. GitHub MCP Server
- **Descripción**: Permite interactuar con repositorios, issues y pull requests de GitHub.
- **Operaciones**: Listar repositorios, crear issues, comentar en PRs, etc.
- **Autenticación**: Token personal de acceso (PAT).

### 2. Notion MCP Server
- **Descripción**: Permite buscar, leer y escribir en páginas y bases de datos de Notion.
- **Operaciones**: Búsqueda, lectura de páginas, creación de contenido, etc.
- **Autenticación**: Token de integración interna.

### 3. Slack MCP Server
- **Descripción**: Permite enviar mensajes y leer canales en Slack.
- **Operaciones**: Enviar mensajes, listar canales, leer mensajes, etc.
- **Autenticación**: Tokens xoxc y xoxd.

### 4. Google Workspace MCP Server
- **Descripción**: Permite gestionar archivos en Google Drive.
- **Operaciones**: Listar archivos, crear archivos, leer contenido, etc.
- **Autenticación**: Token de acceso OAuth, token de actualización.

### 5. Google Sheets MCP Server
- **Descripción**: Permite leer y escribir en hojas de cálculo de Google Sheets.
- **Operaciones**: Leer valores, escribir valores, crear hojas, etc.
- **Autenticación**: Token de acceso OAuth, token de actualización.

### 6. Instagram DM MCP Server
- **Descripción**: Permite leer y enviar mensajes directos en Instagram.
- **Operaciones**: Leer mensajes recientes, enviar mensajes, etc.
- **Autenticación**: Cookies de sesión (session_id, csrf_token, ds_user_id).

### 7. Trello MCP Server
- **Descripción**: Permite gestionar tableros, listas y tarjetas en Trello.
- **Operaciones**: Listar tableros, crear tarjetas, mover tarjetas, etc.
- **Autenticación**: API Key y Token.

### 8. Twitter/X MCP Server
- **Descripción**: Permite leer la timeline y publicar tweets en Twitter/X.
- **Operaciones**: Leer timeline, crear tweets, responder a tweets, etc.
- **Autenticación**: API Key, API Secret, Access Token, Access Secret.

## Guía de Instalación

### Requisitos Previos

#### Software Necesario
- Docker 20.10.0 o superior
- Node.js 16.0.0 o superior
- NPM 7.0.0 o superior
- Python 3.8.0 o superior
- Pip 20.0.0 o superior

#### Dependencias de Python
```bash
pip install asyncio aiohttp fastapi uvicorn pydantic python-dotenv
```

#### Dependencias de Node.js
```bash
npm install -g slack-mcp-server@latest instagram-dm-mcp @delorenj/mcp-server-trello
```

### Pasos de Instalación

1. **Clonar el repositorio de GENIA**
   ```bash
   git clone https://github.com/tu-organizacion/genia-backend.git
   cd genia-backend
   ```

2. **Crear estructura de directorios**
   ```bash
   mkdir -p app/mcp_client/config
   ```

3. **Copiar archivos de implementación MCP**
   Copia los siguientes archivos a sus respectivas ubicaciones:
   - `mcp_orchestrator_extended.py` → `app/mcp_client/`
   - `mcp_client_extended.py` → `app/mcp_client/`
   - `validate_mcp_extended.py` → `app/mcp_client/`
   - `mcp_routes.py` → `app/api/`

4. **Configurar variables de entorno**
   Crea un archivo `.env` en la raíz del proyecto con las variables necesarias (ver sección de Configuración).

5. **Instalar dependencias del proyecto**
   ```bash
   pip install -r requirements.txt
   ```

6. **Verificar instalación**
   ```bash
   python -m app.mcp_client.validate_mcp_extended
   ```

## Configuración de Servidores

### Configuración General

Crea un archivo `.env` en la raíz del proyecto con la siguiente estructura:

```
# Configuración general
MCP_TOKEN_ENCRYPTION_KEY=your_encryption_key

# Configuración de Docker
DOCKER_HOST=unix:///var/run/docker.sock

# Configuración de base de datos
DATABASE_URL=postgres://user:password@host:port/database
```

### Configuración por Servidor

#### GitHub MCP Server
```
# GitHub MCP (opcional, solo para pruebas)
GITHUB_TOKEN=ghp_your_github_token
```

#### Notion MCP Server
```
# Notion MCP (opcional, solo para pruebas)
NOTION_TOKEN=secret_your_notion_token
```

#### Slack MCP Server
```
# Slack MCP (opcional, solo para pruebas)
SLACK_XOXC_TOKEN=xoxc-your-slack-token
SLACK_XOXD_TOKEN=xoxd-your-slack-token
```

#### Google Workspace MCP Server
```
# Google Workspace MCP (opcional, solo para pruebas)
GOOGLE_ACCESS_TOKEN=your_google_access_token
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REFRESH_TOKEN=your_google_refresh_token
```

#### Instagram MCP Server
```
# Instagram MCP (opcional, solo para pruebas)
INSTAGRAM_SESSION_ID=your_instagram_session_id
INSTAGRAM_CSRF_TOKEN=your_instagram_csrf_token
INSTAGRAM_DS_USER_ID=your_instagram_ds_user_id
```

#### Trello MCP Server
```
# Trello MCP (opcional, solo para pruebas)
TRELLO_API_KEY=your_trello_api_key
TRELLO_TOKEN=your_trello_token
TRELLO_BOARD_ID=your_trello_board_id
```

#### Twitter/X MCP Server
```
# Twitter/X MCP (opcional, solo para pruebas)
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

## Interfaz de Usuario

### Pantallas Recomendadas

1. **Dashboard de Conexiones**
   - Muestra todas las herramientas disponibles
   - Indica cuáles están conectadas y cuáles no
   - Permite conectar/desconectar herramientas

2. **Página de Conexión**
   - Formulario para introducir credenciales
   - Instrucciones para obtener tokens/claves
   - Confirmación de conexión exitosa

3. **Panel de Operaciones**
   - Lista de operaciones disponibles por herramienta
   - Formularios para ejecutar operaciones
   - Visualización de resultados

### Ejemplo de Implementación Frontend (React)

```jsx
// Componente de Conexiones
function ConnectionsDashboard() {
  const [connections, setConnections] = useState({});
  
  useEffect(() => {
    // Cargar conexiones al montar el componente
    fetch('/api/mcp/connections')
      .then(res => res.json())
      .then(data => setConnections(data.connections));
  }, []);
  
  return (
    <div className="connections-dashboard">
      <h1>Tus Conexiones</h1>
      
      {Object.entries(connections).map(([service, isConnected]) => (
        <div key={service} className="connection-card">
          <h3>{service}</h3>
          <p>Estado: {isConnected ? 'Conectado' : 'No conectado'}</p>
          
          {isConnected ? (
            <button onClick={() => disconnectService(service)}>
              Desconectar
            </button>
          ) : (
            <button onClick={() => navigateToConnect(service)}>
              Conectar
            </button>
          )}
        </div>
      ))}
    </div>
  );
}

// Componente de Conexión
function ConnectService({ service }) {
  const [formData, setFormData] = useState({});
  
  const handleConnect = async (e) => {
    e.preventDefault();
    
    try {
      const response = await fetch(`/api/mcp/connect/${service}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // Mostrar mensaje de éxito y redirigir
        showSuccessMessage(`${service} conectado correctamente`);
        navigateToDashboard();
      } else {
        // Mostrar error
        showErrorMessage(data.detail);
      }
    } catch (error) {
      showErrorMessage('Error al conectar servicio');
    }
  };
  
  return (
    <div className="connect-service">
      <h1>Conectar {service}</h1>
      
      <form onSubmit={handleConnect}>
        {/* Campos específicos según el servicio */}
        {service === 'github' && (
          <div className="form-group">
            <label>Token Personal de Acceso:</label>
            <input
              type="password"
              onChange={(e) => setFormData({...formData, token: e.target.value})}
            />
            <p className="help-text">
              Puedes generar un token en 
              <a href="https://github.com/settings/tokens" target="_blank">
                GitHub Settings
              </a>
            </p>
          </div>
        )}
        
        {/* Campos para otros servicios... */}
        
        <button type="submit">Conectar</button>
      </form>
    </div>
  );
}
```

## Pruebas y Validación

### Pruebas Unitarias

Se han implementado pruebas unitarias para validar el funcionamiento de cada componente:

1. **Pruebas del Orquestador**
   - Registro de servidores
   - Inicio y detención de servidores
   - Gestión de tokens de usuario

2. **Pruebas del Cliente**
   - Inicialización del cliente
   - Ejecución de operaciones en cada servicio
   - Gestión de errores

3. **Pruebas de API**
   - Endpoints de conexión
   - Endpoints de ejecución
   - Autenticación y autorización

### Ejecución de Pruebas

Para ejecutar las pruebas de validación:

```bash
python -m app.mcp_client.validate_mcp_extended
```

### Resultados de Pruebas

Los resultados de las pruebas se guardan en el archivo `mcp_validation_extended.log`. Revisa este archivo para verificar que todas las pruebas hayan pasado correctamente.

## Despliegue en Producción

### Despliegue en Render

1. **Preparación del Proyecto**
   - Asegúrate de que todos los archivos estén en el repositorio
   - Verifica que el archivo `requirements.txt` incluya todas las dependencias

2. **Configuración en Render**
   - Crea un nuevo servicio Web en Render
   - Conecta con el repositorio de GitHub
   - Selecciona la rama principal
   - Configura el comando de inicio: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Añade todas las variables de entorno necesarias

3. **Configuración de Secretos**
   - Añade `MCP_TOKEN_ENCRYPTION_KEY` como variable de entorno secreta
   - Configura la conexión a la base de datos

### Configuración de Base de Datos en Supabase

1. **Crear Tabla de Tokens**
   ```sql
   CREATE TABLE user_tokens (
     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
     user_id UUID NOT NULL REFERENCES auth.users(id),
     service TEXT NOT NULL,
     tokens JSONB NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
   );
   
   -- Índice para búsquedas rápidas por usuario
   CREATE INDEX idx_user_tokens_user_id ON user_tokens(user_id);
   
   -- Política de seguridad (RLS)
   CREATE POLICY "Users can only access their own tokens"
     ON user_tokens
     FOR ALL
     USING (auth.uid() = user_id);
   ```

2. **Implementar Funciones para Gestión de Tokens**
   ```sql
   -- Función para guardar tokens
   CREATE OR REPLACE FUNCTION save_user_tokens(
     p_user_id UUID,
     p_service TEXT,
     p_tokens JSONB
   ) RETURNS BOOLEAN AS $$
   DECLARE
     v_exists BOOLEAN;
   BEGIN
     SELECT EXISTS(
       SELECT 1 FROM user_tokens
       WHERE user_id = p_user_id AND service = p_service
     ) INTO v_exists;
     
     IF v_exists THEN
       UPDATE user_tokens
       SET tokens = p_tokens, updated_at = NOW()
       WHERE user_id = p_user_id AND service = p_service;
     ELSE
       INSERT INTO user_tokens (user_id, service, tokens)
       VALUES (p_user_id, p_service, p_tokens);
     END IF;
     
     RETURN TRUE;
   EXCEPTION
     WHEN OTHERS THEN
       RETURN FALSE;
   END;
   $$ LANGUAGE plpgsql SECURITY DEFINER;
   ```

### Consideraciones de Seguridad

- Utiliza HTTPS para todas las comunicaciones
- Cifra los tokens en reposo y en tránsito
- Implementa rotación de tokens cuando sea posible
- Utiliza permisos mínimos necesarios para cada servicio
- Monitorea el uso de tokens y revoca accesos sospechosos

## Mantenimiento y Escalabilidad

### Añadir Nuevos Servidores MCP

Para añadir un nuevo servidor MCP:

1. **Analizar Requisitos**
   - Estudiar la documentación del servidor MCP
   - Identificar requisitos de autenticación y dependencias

2. **Extender el Orquestador**
   - Añadir configuración del nuevo servidor en `mcp_orchestrator_extended.py`
   - Definir variables de entorno necesarias

3. **Extender el Cliente**
   - Implementar métodos específicos en `mcp_client_extended.py`
   - Añadir gestión de tokens para el nuevo servicio

4. **Actualizar la API**
   - Añadir endpoints específicos en `mcp_routes.py`
   - Implementar validaciones para el nuevo servicio

5. **Actualizar Documentación**
   - Documentar el nuevo servidor y sus operaciones
   - Actualizar ejemplos de uso

### Monitoreo y Logs

Configura un sistema de monitoreo para:

1. **Estado de Servidores**
   - Verificar que todos los servidores estén funcionando correctamente
   - Detectar y reiniciar servidores caídos

2. **Uso de Recursos**
   - Monitorear uso de CPU y memoria
   - Identificar cuellos de botella

3. **Errores y Excepciones**
   - Registrar errores en logs estructurados
   - Configurar alertas para errores críticos

4. **Métricas de Uso**
   - Número de operaciones por servicio
   - Tiempo de respuesta promedio
   - Tasa de éxito/error

## Solución de Problemas

### Problemas Comunes y Soluciones

#### 1. Error al iniciar servidores Docker

**Problema**: No se pueden iniciar los servidores MCP basados en Docker.

**Solución**:
- Verifica que Docker esté instalado y en ejecución: `docker --version`
- Asegúrate de que el usuario tenga permisos para usar Docker: `sudo usermod -aG docker $USER`
- Comprueba la conectividad a Internet para descargar imágenes
- Verifica los logs de Docker: `docker logs <container_id>`

#### 2. Error de autenticación en servicios externos

**Problema**: Los tokens de usuario son rechazados por el servicio externo.

**Solución**:
- Verifica que los tokens sean válidos y no hayan expirado
- Comprueba que los permisos asignados sean suficientes
- Implementa renovación automática de tokens cuando sea posible
- Revisa los logs del servidor MCP para mensajes de error específicos

#### 3. Problemas de rendimiento con múltiples servidores

**Problema**: El sistema se vuelve lento al gestionar múltiples servidores MCP.

**Solución**:
- Implementa inicio bajo demanda de servidores
- Utiliza un sistema de caché para resultados frecuentes
- Considera implementar un pool de servidores pre-iniciados
- Optimiza la gestión de recursos en el orquestador

### Herramientas de Diagnóstico

1. **Logs del Sistema**
   - Revisa `mcp_validation_extended.log` para resultados de pruebas
   - Configura logging detallado en producción

2. **Estado de Servidores**
   - Utiliza el endpoint `/api/mcp/status` para verificar el estado de los servidores
   - Implementa un dashboard de monitoreo

3. **Herramientas de Depuración**
   - Utiliza el modo de depuración en el orquestador: `DEBUG=true`
   - Implementa endpoints de diagnóstico para administradores

## Referencias

### Documentación de Servidores MCP

- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [Notion MCP Server](https://github.com/notion/notion-mcp-server)
- [Slack MCP Server](https://github.com/slack/slack-mcp-server)
- [Google Workspace MCP Server](https://github.com/distrihub/mcp-google-workspace)
- [Instagram DM MCP Server](https://github.com/instagram-dm-mcp)
- [Trello MCP Server](https://github.com/delorenj/mcp-server-trello)
- [Twitter/X MCP Server](https://github.com/x-mcp-server)

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
- [Supabase Documentation](https://supabase.io/docs)
- [Render Documentation](https://render.com/docs)

---

## Conclusión

Esta guía proporciona instrucciones detalladas para implementar, configurar y desplegar todos los servidores MCP en GENIA. Siguiendo estos pasos, podrás integrar múltiples servicios externos en GENIA y proporcionar a tus usuarios una experiencia unificada para gestionar sus tareas en diferentes plataformas.

La arquitectura implementada es extensible y escalable, permitiendo añadir fácilmente nuevos servidores MCP en el futuro. Además, el enfoque de autenticación por usuario garantiza que cada usuario pueda conectar sus propias cuentas de servicios externos, alineándose con la visión de GENIA como un sistema SaaS que orquesta herramientas externas para automatizar tareas.
