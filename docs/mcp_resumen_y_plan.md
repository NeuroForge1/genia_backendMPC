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
        *   Espera un cuerpo JSON simple: `{"prompt": "texto del usuario"}` (definido como `SimpleMessage`).
        *   Utiliza `openai` (requiere `OPENAI_API_KEY` en `.env`) para llamar a `ChatCompletion.create`.
        *   Devuelve la respuesta usando Server-Sent Events (SSE) con un formato simple: `data: {"response": "texto generado"}\n\n`.
        *   Corre en `http://localhost:8001`.
    *   **Dependencias:** `fastapi`, `uvicorn`, `openai`, `python-dotenv`, `sse-starlette`.

2.  **Cliente MCP Simplificado en Backend:**
    *   **Ubicación:** `/home/ubuntu/genia_backendMPC/app/mcp_client/client.py` (Repositorio: `NeuroForge1/genia_backendMPC`)
    *   **Tecnología:** Python, usando la librería `httpx` para solicitudes HTTP y manejo de SSE.
    *   **Funcionalidad:**
        *   Clase `GeniaMCPClient` con instancia global `mcp_client_instance`.
        *   Método `request_mcp_server(server_name: str, request_message: SimpleMessage)` que devuelve un `AsyncGenerator` de `SimpleMessage`.
        *   Envía una solicitud `POST` al endpoint del servidor MCP correspondiente (configurado en `SERVER_URLS`).
        *   Maneja la respuesta SSE, parsea los mensajes JSON y los valida con Pydantic.
        *   Incluye una función de prueba `_test_client` (ejecutable solo si el script se llama directamente).
    *   **Dependencias:** `httpx`, `pydantic`.

**Decisiones Clave:**

*   **Comunicación:** Se mantuvo SSE sobre HTTP, implementado directamente con `sse-starlette` en el servidor y `httpx` en el cliente.
*   **Formato de Mensaje:** Se usó un JSON simple (`SimpleMessage`) en lugar de la estructura `Message` de MCP para evitar las dependencias problemáticas.
*   **Enfoque:** Priorizar una conexión funcional básica entre cliente y servidor antes de intentar una implementación más apegada al estándar MCP con librerías.

## 5. Prueba de Comunicación Inicial

Se ejecutó la función `_test_client` directamente desde el archivo `client.py`.

*   **Resultado:** La prueba fue **exitosa**. El cliente (temporal) envió una solicitud al servidor, el servidor llamó a OpenAI, y el cliente recibió e imprimió correctamente la respuesta generada por OpenAI a través de la conexión SSE.
*   **Confirmación:** Esto validó que la comunicación básica entre el Cliente MCP simplificado y el Servidor MCP simplificado funciona correctamente.

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
    *   Se añadió el módulo `app/mcp_client/`.
    *   Se actualizó `requirements.txt` (añadiendo `httpx`).
    *   Se añadió este documento de resumen en `docs/mcp_resumen_y_plan.md`.
    *   Los cambios fueron subidos a GitHub.
*   **Servidor MCP OpenAI:** Nuevo repositorio dedicado `NeuroForge1/genia-mcp-server-openai`.
    *   Contiene el código del servidor (`main.py`), `requirements.txt`, `.env.example`, `.gitignore`.
    *   El código fue subido a GitHub.
*   **Futuros Servidores MCP:** Se crearán repositorios separados para cada nuevo servidor (Stripe, Twilio, etc.).

## 8. Pruebas de Integración Inicial y Correcciones (`openai_tool.py`)

Se ejecutó un script de prueba (`test_openai_tool_mcp.py`) para validar la integración de `OpenAITool` con el Cliente MCP.

*   **Error Inicial (`ValidationError`):** La primera ejecución falló debido a la falta de variables de entorno requeridas por la configuración del backend (`app.core.config`).
*   **Solución:** Se creó el archivo `/home/ubuntu/genia_backendMPC/.env` con todas las variables necesarias (SECRET_KEY, SUPABASE_*, OPENAI_API_KEY, STRIPE_*, TWILIO_*, etc.), utilizando los valores proporcionados por el usuario y generando valores aleatorios seguros para las claves secretas faltantes (SECRET_KEY, SUPABASE_JWT_SECRET).
*   **Error Secundario (`Client Closed`):** La segunda ejecución falló porque la instancia global del cliente MCP (`mcp_client_instance`) se cerraba después de una prueba interna que se ejecutaba automáticamente al importar `client.py`.
*   **Solución:** Se modificó `/home/ubuntu/genia_backendMPC/app/mcp_client/client.py` para:
    *   Mover la ejecución de la prueba interna `_test_client` a un bloque `if __name__ == "__main__":`.
    *   Hacer que `_test_client` use una instancia temporal del cliente en lugar de la global.
    *   Mejorar el manejo de errores y el procesamiento SSE en `request_mcp_server`.
*   **Prueba Final:** La ejecución final de `test_openai_tool_mcp.py` fue **exitosa**. `OpenAITool` utilizó correctamente `mcp_client_instance` para comunicarse con el servidor MCP de OpenAI y obtener la respuesta.

## 9. Integración Adicional en Backend (Otras Herramientas)

Siguiendo el éxito con `OpenAITool`, se procedió a integrar el `GeniaMCPClient` en las demás herramientas del backend que realizaban llamadas directas a OpenAI.

*   **Archivos Modificados:**
    *   `/home/ubuntu/genia_backendMPC/app/tools/funnels_tool.py`
    *   `/home/ubuntu/genia_backendMPC/app/tools/seo_analysis_tool.py`
    *   `/home/ubuntu/genia_backendMPC/app/tools/whatsapp_analysis_tool.py`
*   **Cambios Realizados (Patrón Común):**
    *   Se importó la instancia global `mcp_client_instance` y las estructuras `SimpleMessage`, `SimpleTextContent`.
    *   Se eliminó la importación directa de `openai` y la configuración de `openai.api_key`.
    *   Se creó un método helper `_call_mcp_openai` dentro de cada clase para encapsular la lógica de llamada al cliente MCP (similar al implementado en `OpenAITool`).
    *   Se modificaron los métodos existentes que llamaban a `openai.ChatCompletion.create` (ej., `_create_sales_funnel`, `_analyze_content`, `_generate_response_suggestions`, etc.) para que utilizaran el nuevo método helper `_call_mcp_openai`.
    *   Se adaptó el manejo de las respuestas recibidas del cliente MCP.
    *   Se renombraron los métodos modificados añadiendo el sufijo `_mcp` (ej., `_create_sales_funnel_mcp`) y se actualizó el método `execute` para llamar a las nuevas versiones.

## 10. Pruebas de Integración Completas

Para verificar que la integración funcionaba correctamente en todas las herramientas modificadas, se creó y ejecutó un script de prueba completo.

*   **Script de Prueba:** `/home/ubuntu/genia_backendMPC/test_mcp_integration_full.py`
*   **Funcionalidad del Script:**
    *   Importó las cuatro herramientas modificadas (`OpenAITool`, `FunnelsTool`, `SEOAnalysisTool`, `WhatsAppAnalysisTool`).
    *   Llamó a una capacidad representativa de cada herramienta, pasando parámetros de ejemplo.
    *   Verificó que cada llamada devolviera un estado `success` y datos válidos.
*   **Corrección de Errores:** Durante la ejecución inicial, se detectó y corrigió un error de sintaxis (`SyntaxError: invalid syntax`) en `whatsapp_analysis_tool.py` causado por caracteres de tabulación incorrectos en expresiones regulares.
*   **Resultado Final:** Tras la corrección, la ejecución del script `test_mcp_integration_full.py` fue **exitosa**. Todas las herramientas pudieron comunicarse correctamente con el servidor MCP de OpenAI a través del `GeniaMCPClient`.

## 11. Estado Actual y Próximos Pasos

**Estado Actual:**

*   Cliente y Servidor MCP simplificados implementados y funcionando.
*   Comunicación básica entre ellos validada.
*   Código del servidor y cambios en backend (cliente MCP, `.env`, correcciones) subidos a sus respectivos repositorios.
*   Integración del Cliente MCP **completada y probada exitosamente** en todas las herramientas identificadas que usaban OpenAI directamente (`OpenAITool`, `FunnelsTool`, `SEOAnalysisTool`, `WhatsAppAnalysisTool`).
*   Las pruebas de integración completas (`test_mcp_integration_full.py`) han validado el funcionamiento correcto.

**Próximos Pasos Inmediatos:**

1.  **Preparar Cambios para GitHub:** Revisar los cambios realizados en el backend (`genia_backendMPC`), añadir los archivos nuevos/modificados al control de versiones (`git add`), y preparar un commit con un mensaje descriptivo.
2.  **Subir Cambios:** Hacer `git push` para subir los cambios al repositorio `NeuroForge1/genia_backendMPC`.
3.  **Reportar Resultados:** Informar al usuario sobre la finalización exitosa de la integración y las pruebas.

**Pasos Futuros (Post-Integración OpenAI):**

*   **Manejo de Claves de Usuario:** Implementar la lógica (descrita previamente al usuario) para permitir a los usuarios usar sus propias claves API a través de MCP.
*   **Implementar Otros Servidores MCP:** Crear servidores MCP para otras herramientas (Stripe, Twilio, etc.) siguiendo el mismo patrón simplificado o reevaluando librerías si se vuelven estables.
*   **Refinar Protocolo:** Eventualmente, si las librerías MCP maduran o se encuentra una solución a los problemas de importación, se podría refactorizar para usar una implementación más apegada al estándar MCP.
*   **Integración Frontend:** Realizar los cambios necesarios en el frontend para funcionalidades avanzadas (streaming, configuración de claves, etc.).

