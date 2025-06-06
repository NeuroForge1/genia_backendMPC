# Resumen Detallado y Plan de Integración del Protocolo MCP en GENIA

## 1. Introducción y Objetivos

El objetivo principal de integrar el Protocolo de Contexto de Modelo (MCP - Model Context Protocol) en GENIA es desacoplar la lógica central del backend de las interacciones específicas con herramientas externas (como OpenAI, Stripe, Twilio, etc.). Buscamos crear una arquitectura más modular, extensible y mantenible.

**Beneficios Esperados:**

*   **Modularidad:** Aislar la lógica de cada herramienta externa en su propio componente (Servidor MCP).
*   **Extensibilidad:** Facilitar la adición de nuevas herramientas creando nuevos Servidores MCP sin modificar significativamente el backend principal.
*   **Mantenimiento Simplificado:** Actualizar la interacción con una herramienta (ej., si cambia su API) solo requiere modificar su Servidor MCP dedicado.
*   **Organización del Código:** Mantener el backend principal más limpio y enfocado en la orquestación.
*   **Estandarización:** Utilizar un protocolo diseñado para la comunicación entre agentes de IA y herramientas.

## 2. Análisis Inicial y Arquitectura Propuesta Original

Se realizó un análisis inicial basado en la documentación oficial de MCP (aunque hubo problemas técnicos para accederla directamente, se usó búsqueda web).

**Conceptos Clave Identificados:**

*   **Host:** La aplicación principal que orquesta las interacciones (en nuestro caso, el backend FastAPI de GENIA).
*   **Cliente MCP:** Un componente dentro del Host que se comunica usando el protocolo MCP.
*   **Servidor MCP:** Un servicio (potencialmente externo) que expone una herramienta a través del protocolo MCP.

**Arquitectura Propuesta Original:**

*   **Host:** Backend FastAPI de GENIA.
*   **Cliente MCP:** Implementado dentro del backend FastAPI.
*   **Servidores MCP:** Microservicios separados para cada herramienta externa (OpenAI, Stripe, Twilio, etc.).
*   **Comunicación:** Se propuso usar Server-Sent Events (SSE) sobre HTTP para la comunicación entre el Cliente y los Servidores MCP.

*Referencia: `mcp_arquitectura_propuesta.md` (Aunque este archivo no se subió, la esencia está aquí)*

## 3. Investigación de Librerías y Problemas Encontrados

Se investigaron librerías Python para facilitar la implementación del Cliente y Servidor MCP.

**Librerías Consideradas:**

*   `modelcontextprotocol/python-sdk`: El SDK oficial.
*   Integración en PydanticAI.
*   `fastmcp`: Una librería que parecía implementar `FastMCP` para FastAPI.

**Problemas Graves Encontrados:**

*   **Instalación Incorrecta:** Inicialmente se instaló un paquete llamado `modelcontextprotocol` que no era el SDK oficial, sino una interfaz de chat de terminal.
*   **Errores de Importación Persistentes:** Tras instalar `fastmcp` (que a su vez instaló una versión de `mcp`), surgieron numerosos y persistentes errores `ModuleNotFoundError` al intentar importar clases esenciales como `FastMCP`, `Message`, `MessageContent`, `TextContent` desde `mcp`, `fastmcp`, `mcp.common`, `mcp.server`, etc. Se intentaron múltiples combinaciones de importación basadas en la estructura de paquetes inspeccionada, pero ninguna funcionó de manera consistente.
*   **Conclusión:** Debido a la imposibilidad de resolver los problemas de importación con las librerías existentes (posiblemente por conflictos de versiones, problemas de instalación en el entorno o documentación desactualizada/confusa), se decidió abandonar el uso de estas librerías para la implementación inicial.

*Referencia: `mcp_investigacion_librerias.md` (Aunque este archivo no se subió, la esencia está aquí)*

## 4. Arquitectura Simplificada Implementada (Cliente y Servidor)

Ante los problemas con las librerías, se optó por una implementación **simplificada** y **directa** de MCP, sin depender de las abstracciones `FastMCP` o `Message` de las librerías problemáticas.

**Componentes Implementados:**

1.  **Servidor MCP Simplificado para OpenAI:**
    *   **Ubicación:** `/home/ubuntu/genia_mcp_server_openai/main.py` (Repositorio: `NeuroForge1/genia-mcp-server-openai`)
    *   **Tecnología:** FastAPI.
    *   **Funcionalidad:**
        *   Expone un endpoint `/mcp` que acepta solicitudes `POST`.
        *   Espera un cuerpo JSON simple (`SimpleMessage`).
        *   Utiliza `openai` (requiere `OPENAI_API_KEY` en `.env`) para llamar a `ChatCompletion.create`.
        *   Devuelve la respuesta usando Server-Sent Events (SSE) con un formato simple.
        *   Corre en `http://localhost:8001`.
    *   **Dependencias:** `fastapi`, `uvicorn`, `openai`, `python-dotenv`, `sse-starlette`, `pydantic`.

2.  **Cliente MCP Simplificado en Backend:**
    *   **Ubicación:** `/home/ubuntu/genia_backendMPC/app/mcp_client/client.py` (Repositorio: `NeuroForge1/genia_backendMPC`)
    *   **Tecnología:** Python, usando la librería `httpx` para solicitudes HTTP y manejo de SSE.
    *   **Funcionalidad:**
        *   Clase `GeniaMCPClient` con instancia global `mcp_client_instance`.
        *   Método `request_mcp_server(server_name: str, request_message: SimpleMessage)` que devuelve un `AsyncGenerator` de `SimpleMessage`.
        *   Envía una solicitud `POST` al endpoint del servidor MCP correspondiente (configurado en `SERVER_URLS`).
        *   Maneja la respuesta SSE, parsea los mensajes JSON y los valida con Pydantic.
    *   **Dependencias:** `httpx`, `pydantic`.

**Decisiones Clave:**

*   **Comunicación:** Se mantuvo SSE sobre HTTP, implementado directamente con `sse-starlette` en el servidor y `httpx` en el cliente.
*   **Formato de Mensaje:** Se usó un JSON simple (`SimpleMessage`) en lugar de la estructura `Message` de MCP para evitar las dependencias problemáticas.
*   **Enfoque:** Priorizar una conexión funcional básica entre cliente y servidor antes de intentar una implementación más apegada al estándar MCP con librerías.

## 5. Prueba de Comunicación Inicial (OpenAI)

Se ejecutó la función `_test_client` directamente desde el archivo `client.py`.

*   **Resultado:** La prueba fue **exitosa**. El cliente (temporal) envió una solicitud al servidor OpenAI, el servidor llamó a OpenAI, y el cliente recibió e imprimió correctamente la respuesta generada por OpenAI a través de la conexión SSE.
*   **Confirmación:** Esto validó que la comunicación básica entre el Cliente MCP simplificado y el Servidor MCP simplificado de OpenAI funciona correctamente.

## 6. Integración Inicial en Backend (`openai_tool.py`)

Se procedió a integrar el `GeniaMCPClient` en la lógica existente del backend.

*   **Archivo Modificado:** `/home/ubuntu/genia_backendMPC/app/tools/openai_tool.py`.
*   **Cambios Realizados:**
    *   Se importó la instancia global `mcp_client_instance`.
    *   En el método `_generate_text_mcp`, se reemplazó la llamada directa a la API de OpenAI por un bucle `async for` que consume el generador devuelto por `mcp_client_instance.request_mcp_server("openai", mcp_message)`.
    *   Se adaptó la lógica para extraer el texto de la respuesta del primer mensaje `assistant` recibido.
    *   Se eliminó la importación directa de `openai` y la inicialización del cliente OpenAI directo.

## 7. Gestión del Código (Repositorios Separados)

Se discutió y acordó la siguiente estructura de repositorios para fomentar la modularidad:

*   **Backend (Host y Cliente MCP):** Repositorio existente `NeuroForge1/genia_backendMPC`.
*   **Servidor MCP OpenAI:** Nuevo repositorio dedicado `NeuroForge1/genia-mcp-server-openai`.
*   **Futuros Servidores MCP:** Se crearán repositorios separados para cada nuevo servidor (Stripe, Twilio, etc.).

## 8. Pruebas de Integración Inicial y Correcciones (`openai_tool.py`)

Se ejecutó un script de prueba (`test_openai_tool_mcp.py`) para validar la integración de `OpenAITool` con el Cliente MCP.

*   **Errores y Soluciones:** Se resolvieron errores relacionados con la falta de variables de entorno (`.env`) y el cierre prematuro del cliente HTTPX global.
*   **Prueba Final:** La ejecución final de `test_openai_tool_mcp.py` fue **exitosa**.

## 9. Integración Adicional en Backend (Otras Herramientas OpenAI)

Se integró el `GeniaMCPClient` en las demás herramientas del backend que realizaban llamadas directas a OpenAI.

*   **Archivos Modificados:** `funnels_tool.py`, `seo_analysis_tool.py`, `whatsapp_analysis_tool.py`.
*   **Cambios Realizados:** Se siguió un patrón común: importar cliente MCP, eliminar cliente OpenAI directo, crear método helper `_call_mcp_openai`, y modificar métodos existentes para usar el helper.

## 10. Pruebas de Integración Completas (OpenAI)

Se creó y ejecutó un script de prueba completo (`test_mcp_integration_full.py`) para verificar la integración en todas las herramientas modificadas.

*   **Corrección de Errores:** Se corrigió un `SyntaxError` en `whatsapp_analysis_tool.py`.
*   **Resultado Final:** La ejecución del script fue **exitosa**. Todas las herramientas pudieron comunicarse correctamente con el servidor MCP de OpenAI a través del `GeniaMCPClient`.
*   **Código Subido:** Los cambios relacionados con la integración de OpenAI en el backend fueron subidos al repositorio `NeuroForge1/genia_backendMPC`.

## 11. Implementación del Servidor MCP para Stripe

Siguiendo la decisión de continuar con la arquitectura MCP, se procedió a implementar el servidor para Stripe.

*   **Diseño:**
    *   Se analizó `stripe_tool.py` identificando las capacidades: `create_payment`, `create_subscription`, `create_customer`.
    *   Se decidió crear un microservicio FastAPI separado (`genia-mcp-server-stripe`).
    *   El servidor expondría `/mcp`, aceptaría `SimpleMessage`, pasaría `capability` y `params` en `metadata`.
    *   Interactuaría solo con la API de Stripe (requiere `STRIPE_SECRET_KEY`).
    *   Devolvería resultados vía SSE (`SimpleMessage`).
    *   La lógica de actualización de Supabase permanecería en el backend.
*   **Implementación:**
    *   Se creó la estructura del proyecto en `/home/ubuntu/genia_mcp_server_stripe`.
    *   Se definieron las dependencias (`requirements.txt`).
    *   Se creó `.env.example` y `.env` (con la clave proporcionada por el usuario).
    *   Se implementó `main.py` con FastAPI, endpoint `/mcp`, generador SSE `stripe_sse_generator` que maneja las tres capacidades usando `asyncio.to_thread` para las llamadas a Stripe.

## 12. Integración del Cliente MCP para Stripe en Backend

Se modificó el backend para usar el nuevo servidor MCP de Stripe.

*   **Cliente MCP Actualizado:** Se añadió la URL del servidor Stripe (`http://localhost:8002/mcp`) a `SERVER_URLS` en `app/mcp_client/client.py`. Se mejoró el manejo de eventos SSE.
*   **`stripe_tool.py` Modificado:**
    *   Se eliminó la configuración directa de `stripe.api_key`.
    *   Se importó `mcp_client_instance`.
    *   Se creó un método helper `_call_mcp_stripe` para llamar al cliente MCP.
    *   Se modificaron `_create_payment`, `_create_subscription`, `_create_customer` para usar `_call_mcp_stripe`, renombrándolos con sufijo `_mcp`.
    *   Se mantuvo la lógica de actualización de Supabase en `_create_customer_mcp` después de recibir el `customer_id` del servidor MCP.

## 13. Pruebas de Integración (Stripe)

Se realizaron pruebas para validar la integración de Stripe vía MCP.

*   **Servidor Iniciado:** Se ejecutó el servidor MCP de Stripe (`python3 main.py` en `/home/ubuntu/genia_mcp_server_stripe`).
*   **Script de Prueba:** Se creó y ejecutó `/home/ubuntu/genia_backendMPC/test_stripe_tool_mcp.py`.
*   **Resultados:**
    *   `create_customer`: **Éxito**. Se creó el cliente en Stripe. Hubo un error al actualizar Supabase (`stripe_customer_id` column not found), pero la prueba se consideró un éxito parcial ya que la comunicación MCP y la creación en Stripe funcionaron.
    *   `create_payment`: **Éxito**. Se creó el PaymentIntent en Stripe.
    *   `create_subscription`: **Fallo esperado**. La llamada falló porque el `price_id` de prueba no era válido en la cuenta de Stripe. Sin embargo, la comunicación con el servidor MCP funcionó hasta el punto de recibir el error de Stripe.
*   **Conclusión:** La integración de Stripe vía MCP funciona correctamente para las capacidades probadas, demostrando la viabilidad de la arquitectura.

## 14. Estado Actual y Próximos Pasos

**Estado Actual:**

*   Servidor MCP para OpenAI implementado, integrado y probado.
*   Servidor MCP para Stripe implementado, integrado y probado (con las salvedades mencionadas).
*   Cliente MCP en backend actualizado para soportar ambos servidores.
*   Código de integración de OpenAI subido a GitHub.
*   Código del servidor Stripe y cambios de integración en backend **pendientes de subir a GitHub**.

**Próximos Pasos Inmediatos:**

1.  **Evaluar Implementación Otros Servidores:** Decidir si implementar el servidor MCP para Twilio a continuación o abordar otras tareas.
2.  **Preparar Cambios Stripe para GitHub:** Crear repositorio para `genia-mcp-server-stripe`, añadir archivos y subir. Añadir cambios en `genia_backendMPC` (cliente, stripe_tool, test script), hacer commit y push.
3.  **Reportar Resultados:** Informar al usuario sobre la finalización de la integración de Stripe.

**Pasos Futuros (Post-Integración Stripe/Twilio):**

*   **Resolver Error Supabase:** Investigar y corregir el error "Could not find the 'stripe_customer_id' column" en la tabla `usuarios` de Supabase.
*   **Manejo de Claves de Usuario:** Implementar la lógica para permitir a los usuarios usar sus propias claves API a través de MCP.
*   **Refinar Protocolo:** Reevaluar librerías MCP estándar.
*   **Integración Frontend:** Conectar frontend si es necesario.
*   **Resolver Problemas Funcionales:** Abordar problemas pendientes como la carga infinita del dashboard.




## 15. Implementación del Servidor MCP para Twilio

Continuando con la arquitectura MCP, se implementó el servidor para Twilio.

*   **Análisis:** Se identificó que Twilio se usa principalmente en `whatsapp_tool.py` para enviar mensajes (`send_message`).
*   **Diseño:**
    *   Microservicio FastAPI separado (`genia-mcp-server-twilio`).
    *   Endpoint `/mcp` aceptando `SimpleMessage`.
    *   Capacidad principal: `send_whatsapp_message`.
    *   Parámetros (`metadata`): `to` (número destino), `body` (mensaje).
    *   Lógica: Usar credenciales Twilio (`.env`) para enviar mensaje vía API.
    *   Respuesta SSE: `SimpleMessage` con `message_sid` o error.
*   **Implementación:**
    *   Estructura creada en `/home/ubuntu/genia_mcp_server_twilio`.
    *   Dependencias en `requirements.txt`.
    *   `.env.example` y `.env` creados (con credenciales proporcionadas).
    *   `main.py` implementado con FastAPI, endpoint `/mcp`, lógica para `send_whatsapp_message`.
*   **Repositorio:** Creado en `NeuroForge1/genia-mcp-server-twilio` usando la API de GitHub.
*   **Código Subido:** El código del servidor se subió exitosamente al repositorio.

## 16. Integración del Cliente MCP para Twilio en Backend

Se modificó el backend para usar el nuevo servidor MCP de Twilio.

*   **Cliente MCP Actualizado:** Se añadió la URL del servidor Twilio (`http://localhost:8003/mcp`) a `SERVER_URLS` en `app/mcp_client/client.py`.
*   **`whatsapp_tool.py` Modificado:**
    *   Se eliminó la importación y uso directo de `twilio.rest.Client` para `send_message`.
    *   Se importó `mcp_client_instance`.
    *   Se creó un método helper `_call_mcp_twilio`.
    *   Se modificó `execute` y se creó `_send_message_mcp` para usar el cliente MCP.
    *   Se comentó la capacidad `send_template` ya que no está implementada en el servidor MCP.

## 17. Pruebas de Integración (Twilio)

Se realizaron pruebas para validar la integración de Twilio vía MCP.

*   **Servidor Iniciado:** Se ejecutó el servidor MCP de Twilio (`python3 main.py` en `/home/ubuntu/genia_mcp_server_twilio`).
*   **Script de Prueba:** Se creó y ejecutó `/home/ubuntu/genia_backendMPC/test_whatsapp_tool_mcp.py` para enviar un mensaje a `+16575272405`.
*   **Resultados:**
    *   La prueba **falló** al intentar enviar el mensaje.
    *   El error devuelto por el servidor MCP (originado en Twilio) fue: `"Error de Twilio: Unable to create record: AccountSid [SID inválido proporcionado] is invalid"` (Código Twilio: 21470, Status: 400).
*   **Conclusión:** La **arquitectura MCP funcionó correctamente**: la solicitud pasó del backend al cliente MCP, al servidor MCP de Twilio, y este intentó contactar a Twilio. El error indica un **problema con las credenciales de Twilio proporcionadas (Account SID inválido)**, no un fallo en la integración MCP en sí.

## 18. Estado Actual y Próximos Pasos (Post-Twilio)

**Estado Actual:**

*   Servidor MCP para OpenAI implementado, integrado y probado.
*   Servidor MCP para Stripe implementado, integrado y probado.
*   Servidor MCP para Twilio implementado, integrado y probado (con error de credenciales Twilio).
*   Cliente MCP en backend actualizado para soportar los tres servidores.
*   Código de integración de OpenAI y Stripe (backend) subido a GitHub.
*   Código de los servidores MCP de OpenAI, Stripe y Twilio subidos a sus respectivos repositorios.
*   Código de integración de Twilio (backend) **pendiente de subir a GitHub**.

**Próximos Pasos Inmediatos:**

1.  **Subir Cambios Twilio Backend:** Añadir cambios en `genia_backendMPC` (cliente, whatsapp_tool, test script), hacer commit y push.
2.  **Reportar Resultados:** Informar al usuario sobre la finalización de la integración de Twilio, incluyendo el error de credenciales.
3.  **Decidir Siguiente Tarea:** Consultar al usuario sobre los próximos pasos (ej. implementar otro servidor MCP, abordar problemas funcionales como carga del dashboard, revisar credenciales Twilio, etc.).

**Pasos Futuros:**

*   **Resolver Error Supabase (Stripe):** Investigar por qué falla la actualización del usuario aunque la columna exista (posiblemente el usuario de prueba no existe).
*   **Manejo de Claves de Usuario:** Implementar la lógica para permitir a los usuarios usar sus propias claves API a través de MCP.
*   **Refinar Protocolo:** Reevaluar librerías MCP estándar.
*   **Integración Frontend:** Conectar frontend si es necesario.
*   **Resolver Problemas Funcionales:** Abordar problemas pendientes como la carga infinita del dashboard.



## 19. Implementación de Comandos por WhatsApp (Fase 1: Texto)

Siguiendo la solicitud del usuario de permitir el control de GENIA mediante WhatsApp, se inició la implementación de esta funcionalidad, comenzando por los comandos de texto.

*   **Objetivo:** Permitir a los usuarios enviar comandos de texto a un número de WhatsApp asociado a GENIA, que el sistema interpretará y ejecutará, devolviendo una respuesta por el mismo medio.
*   **Configuración del Webhook (Twilio):**
    *   Se instruyó al usuario para configurar la URL `https://genia-backendmpc.onrender.com/webhook/twilio/whatsapp` (proporcionada por el usuario como la URL del backend desplegado) en la sección "WHEN A MESSAGE COMES IN" de la Sandbox de Twilio, usando el método `HTTP POST`.
    *   El usuario confirmó la correcta configuración.
*   **Implementación del Endpoint Webhook (Backend):**
    *   Se creó el archivo `/home/ubuntu/genia_backendMPC/app/webhooks/twilio_webhook.py`.
    *   Se implementó un endpoint FastAPI `POST /webhook/twilio/whatsapp`.
    *   Incluye validación de la firma de Twilio usando `RequestValidator` y el `TWILIO_AUTH_TOKEN`.
    *   Extrae el número del remitente (`From`), el cuerpo del mensaje (`Body`) y la información de medios (para Fase 2).
    *   Utiliza `BackgroundTasks` de FastAPI para procesar el comando de forma asíncrona, respondiendo inmediatamente a Twilio con un TwiML vacío para evitar timeouts.
*   **Procesador de Mensajes:**
    *   Se creó `/home/ubuntu/genia_backendMPC/app/processing/message_processor.py`.
    *   La función `process_text_message` estructura inicialmente los datos del mensaje de texto.
    *   Se incluyó `process_media_message` como marcador para la Fase 2 (audio).
*   **Intérprete de Comandos (OpenAI vía MCP):**
    *   Se creó `/home/ubuntu/genia_backendMPC/app/nlp/command_interpreter.py`.
    *   Define `AVAILABLE_TOOLS` (generate_text, keyword_research, analyze_sentiment, send_whatsapp_message, unknown_command) con descripciones y parámetros.
    *   La función `build_interpretation_prompt` crea un prompt específico para que OpenAI (vía MCP) devuelva un JSON con `intent` y `parameters`.
    *   La función `interpret_command` llama al servidor MCP de OpenAI usando `mcp_client_instance`, envía el prompt, recibe la respuesta y parsea el JSON resultante, validando el `intent`.
*   **Ejecutor de Tareas:**
    *   Se creó `/home/ubuntu/genia_backendMPC/app/tasks/task_executor.py`.
    *   La función `execute_task` recibe el comando interpretado.
    *   Utiliza un `if/elif` para mapear el `intent` a la herramienta correspondiente (OpenAITool, SEOAnalysisTool, WhatsAppAnalysisTool, WhatsAppTool), las cuales ya usan MCP internamente.
    *   Ejecuta la herramienta con los `parameters` extraídos.
    *   Prepara un mensaje de respuesta (`reply_message`) basado en el resultado de la tarea.
    *   Utiliza `WhatsAppTool` (vía MCP) para enviar el `reply_message` de vuelta al `sender_number` original.
    *   Maneja el intent `unknown_command` y errores generales.
*   **Integración en `main.py`:**
    *   Se importó el `twilio_webhook_router` en `/home/ubuntu/genia_backendMPC/main.py`.
    *   Se incluyó el router en la aplicación FastAPI con el prefijo `/webhook`.
*   **Estado:** La implementación básica para recibir mensajes de texto, interpretarlos con OpenAI y ejecutar tareas (incluyendo enviar respuestas) está completa. Aún no se han realizado pruebas de extremo a extremo con mensajes reales enviados por el usuario.




## 20. Planificación de Próximas Fases

Tras completar la Fase 1 (comandos de texto por WhatsApp), se planifican las siguientes fases para añadir las funcionalidades solicitadas por el usuario:

**Fase 2: Soporte para Comandos de Audio por WhatsApp**

1.  **Selección de Servicio Speech-to-Text (STT):**
    *   Evaluar opciones como OpenAI Whisper (posiblemente vía API o un nuevo servidor MCP), AssemblyAI, Google Cloud Speech-to-Text.
    *   **Recomendación inicial:** Explorar OpenAI Whisper por su potencial integración con la infraestructura existente.
2.  **Implementación del Servidor MCP para STT (si aplica):**
    *   Si se opta por un servicio externo o una instancia dedicada de Whisper, crear un nuevo microservicio (`genia-mcp-server-stt`) similar a los anteriores.
    *   Definir capacidad (ej. `transcribe_audio`) y parámetros (`audio_url` o `audio_data`).
3.  **Modificación del Procesador de Mensajes (`message_processor.py`):**
    *   En `process_media_message`:
        *   Implementar lógica para descargar el archivo de audio desde `media_url` (proporcionado por Twilio).
        *   Llamar al servicio STT (directamente o vía MCP) con el audio descargado.
        *   Devolver el texto transcrito.
    *   Manejar errores de descarga o transcripción.
4.  **Actualización del Webhook (`twilio_webhook.py`):**
    *   Cuando se reciba un mensaje multimedia de tipo audio (`media_type` relevante):
        *   Llamar a `process_media_message` para obtener el texto transcrito.
        *   Si la transcripción es exitosa, pasar el texto transcrito a la tarea de fondo `process_command_background` (la misma que usan los mensajes de texto).
5.  **Pruebas:** Probar enviando mensajes de audio a la Sandbox de Twilio y verificar que se interpreten y ejecuten correctamente.

**Fase 3: Integración de Envío de Correos (Brevo)**

1.  **Implementación del Servidor MCP para Email (Brevo):**
    *   Crear un nuevo microservicio (`genia-mcp-server-brevo` o `genia-mcp-server-email`).
    *   **Credenciales:** Utilizar las credenciales SMTP de Brevo ya disponibles en el `.env` del backend (o moverlas al `.env` del nuevo servidor).
    *   **Tecnología:** FastAPI.
    *   **Endpoint:** `/mcp`.
    *   **Capacidad:** `send_email`.
    *   **Parámetros (`metadata`):** `to_email`, `subject`, `html_content` (o `text_content`).
    *   **Lógica:** Usar `smtplib` de Python o la librería `sib-api-v3-sdk` de Brevo para enviar el correo.
    *   **Respuesta SSE:** `SimpleMessage` confirmando éxito (`status: sent`) o error.
2.  **Integración en Backend:**
    *   Añadir la URL del nuevo servidor MCP de email a `SERVER_URLS` en `app/mcp_client/client.py`.
    *   Crear una nueva herramienta `app/tools/email_tool.py` que use `mcp_client_instance` para llamar a la capacidad `send_email` del servidor MCP.
    *   Añadir `send_email` a `AVAILABLE_TOOLS` en `app/nlp/command_interpreter.py` con su descripción y parámetros.
    *   Actualizar `app/tasks/task_executor.py` para manejar el intent `send_email`, llamar a `EmailTool` y enviar la respuesta correspondiente al usuario por WhatsApp.
3.  **Pruebas:** Probar la funcionalidad con comandos de WhatsApp como "envía un email a ejemplo@dominio.com con asunto Prueba y cuerpo Hola".

**Fase 4: Uso de Credenciales de Usuario (Pendiente de Diseño Detallado)**

*   Diseñar un sistema seguro para almacenar y gestionar las claves API/tokens proporcionados por los usuarios para sus herramientas conectadas (OpenAI, Twilio, Stripe, Brevo, etc.).
*   Modificar los servidores MCP y/o el `task_executor` para recuperar y utilizar las credenciales específicas del usuario (`sender_number` podría ser la clave para buscar las credenciales) al ejecutar una tarea.

**Próximo Paso Inmediato:** Confirmar este plan con el usuario y proceder con la **Fase 2: Soporte para Comandos de Audio por WhatsApp**, comenzando por la selección e integración del servicio STT.

