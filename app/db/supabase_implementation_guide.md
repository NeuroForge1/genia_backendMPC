# Guía de Implementación de Supabase para GENIA MCP

Este documento proporciona instrucciones paso a paso para configurar la base de datos Supabase para el proyecto GENIA MCP.

## Requisitos Previos

- Cuenta en Supabase (https://supabase.com)
- Acceso a las credenciales proporcionadas en el archivo de configuración

## Pasos de Implementación

### 1. Crear un Nuevo Proyecto en Supabase

1. Inicia sesión en Supabase Dashboard
2. Haz clic en "New Project"
3. Ingresa los siguientes datos:
   - Nombre: GENIA MCP
   - Base de datos: Selecciona la región más cercana a tus usuarios
   - Contraseña: Genera una contraseña segura
4. Haz clic en "Create new project"

### 2. Configurar la Base de Datos

1. Una vez creado el proyecto, ve a la sección "SQL Editor"
2. Crea una nueva consulta
3. Copia y pega el contenido del archivo `supabase_init.sql`
4. Ejecuta la consulta para crear todas las tablas, funciones, triggers, políticas y datos iniciales

### 3. Configurar Autenticación

1. Ve a la sección "Authentication" > "Settings"
2. Habilita los siguientes proveedores:
   - Email (habilitado por defecto)
   - Google OAuth
   - Facebook OAuth
3. Configura los proveedores OAuth:
   
   **Google OAuth:**
   - Client ID: `767411502927-pdp64hebksqaublbmlab2t6o99dbpa7f.apps.googleusercontent.com`
   - Client Secret: (Usar el valor proporcionado en las credenciales)
   - Redirect URL: `https://[TU-PROYECTO].supabase.co/auth/v1/callback`
   
   **Facebook OAuth:**
   - Client ID: `1065465758725829`
   - Client Secret: `bef8457566d5b8626bd17909d5807070`
   - Redirect URL: `https://[TU-PROYECTO].supabase.co/auth/v1/callback`

4. En "URL Configuration", configura:
   - Site URL: URL de tu frontend (por ejemplo, `https://genia-frontendmpc.vercel.app`)
   - Redirect URLs: URLs permitidas para redirección (incluir tanto desarrollo como producción)

### 4. Configurar Políticas de Seguridad

Las políticas de seguridad (RLS) ya están incluidas en el script SQL, pero verifica que se hayan aplicado correctamente:

1. Ve a "Authentication" > "Policies"
2. Verifica que cada tabla tenga las políticas correspondientes:
   - `usuarios`: Políticas para administradores y usuarios propios
   - `herramientas_conectadas`: Políticas para administradores y conexiones propias
   - `tareas_generadas`: Políticas para administradores y tareas propias
   - `plantillas_usuario`: Políticas para administradores y plantillas propias

### 5. Obtener Credenciales de API

1. Ve a "Settings" > "API"
2. Copia las siguientes credenciales:
   - URL: `https://[TU-PROYECTO].supabase.co`
   - anon/public key
   - service_role key (para operaciones administrativas)

3. Actualiza estas credenciales en el archivo `.env` del backend:
   ```
   SUPABASE_URL=https://[TU-PROYECTO].supabase.co
   SUPABASE_ANON_KEY=[anon/public key]
   SUPABASE_SERVICE_ROLE_KEY=[service_role key]
   ```

### 6. Configurar Webhooks (Opcional)

Si deseas recibir notificaciones de eventos de la base de datos:

1. Ve a "Database" > "Webhooks"
2. Crea un nuevo webhook para eventos relevantes (por ejemplo, cuando se crea un nuevo usuario)
3. Configura la URL de destino (por ejemplo, un endpoint en tu backend o un servicio como n8n)

### 7. Verificar la Configuración

1. Ve a "Table Editor" para verificar que todas las tablas se hayan creado correctamente
2. Comprueba que los datos iniciales se hayan insertado en las tablas correspondientes
3. Prueba las políticas de seguridad creando un usuario de prueba y verificando los permisos

## Notas Importantes

- **Seguridad**: Nunca compartas la `service_role key` en código cliente o repositorios públicos
- **Backups**: Configura backups regulares en "Settings" > "Database"
- **Monitoreo**: Revisa regularmente los logs en "Logs" para detectar problemas
- **Escalado**: Si es necesario, puedes actualizar tu plan en "Settings" > "Billing"

## Solución de Problemas

- Si las políticas RLS no funcionan como se espera, verifica la sintaxis y los permisos
- Si hay problemas con la autenticación OAuth, verifica las URLs de redirección y los secretos
- Para problemas de rendimiento, revisa los índices y considera agregar más según sea necesario

## Recursos Adicionales

- [Documentación de Supabase](https://supabase.com/docs)
- [Guía de Row Level Security](https://supabase.com/docs/guides/auth/row-level-security)
- [Autenticación con Supabase](https://supabase.com/docs/guides/auth)
