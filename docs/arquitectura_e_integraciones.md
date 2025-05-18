# Arquitectura Actual del Sistema GENIA e Integraciones Posibles

Este documento describe la arquitectura actual del sistema GENIA, sus componentes principales y las posibles integraciones con servidores MCP (Model Context Protocol) para expandir sus capacidades como orquestador central de herramientas externas.

## 1. Arquitectura Actual

### 1.1 Visión General

GENIA es un sistema de automatización con IA que permite a los usuarios ejecutar tareas a través de diferentes canales de comunicación (principalmente WhatsApp) y orquestar herramientas externas. El sistema está diseñado con una arquitectura modular que facilita la integración de nuevos servicios y capacidades.

### 1.2 Componentes Principales

#### 1.2.1 Backend (genia_backendMPC)

El backend de GENIA está implementado como una aplicación FastAPI que gestiona la lógica de negocio, la interpretación de comandos y la orquestación de servicios externos. Sus componentes principales son:

**Módulo de Webhooks (`app/webhooks/`)**
- `twilio_webhook.py`: Recibe y procesa mensajes de WhatsApp a través de Twilio, validando la autenticidad de las solicitudes y delegando el procesamiento a tareas en segundo plano.

**Módulo NLP (`app/nlp/`)**
- `command_interpreter.py`: Interpreta los comandos de texto de los usuarios utilizando el servidor MCP de OpenAI, identificando el comando principal, sus parámetros y posibles acciones secundarias como el envío de correos electrónicos.

**Módulo de Tareas (`app/tasks/`)**
- `task_executor.py`: Ejecuta las tareas identificadas por el CommandInterpreter, gestionando el flujo de trabajo y las respuestas a los usuarios.
- `task_executor_direct.py`: Implementación alternativa que envía correos directamente al MCP de Email sin pasar por el scheduler.

**Módulo de Cliente MCP (`app/mcp_client/`)**
- `client.py`: Cliente para comunicarse con servidores MCP externos (OpenAI, Twilio, Email) mediante el protocolo SSE (Server-Sent Events).

**Módulo de Herramientas (`app/tools/`)**
- `whatsapp_tool.py`: Funciones para enviar mensajes de WhatsApp a través del servidor MCP de Twilio.

**Módulo de Procesamiento (`app/processing/`)**
- Gestiona el procesamiento de mensajes multimedia, como la transcripción de mensajes de audio.

#### 1.2.2 Servidores MCP

GENIA utiliza varios servidores MCP para interactuar con servicios externos:

**MCP de OpenAI**
- URL: https://genia-mcp-server-openai.onrender.com
- Funcionalidad: Proporciona capacidades de procesamiento de lenguaje natural, generación de texto y transcripción de audio.

**MCP de Twilio**
- URL: https://genia-mcp-server-twilio.onrender.com
- Funcionalidad: Permite enviar mensajes de WhatsApp a través de la API de Twilio.

**MCP de Email**
- URL: https://genia-mcp-server-email.onrender.com
- Funcionalidad: Gestiona el envío de correos electrónicos utilizando Gmail como proveedor.

**MCP Scheduler**
- URL: https://genia-mcp-scheduler.onrender.com
- Funcionalidad: Programa tareas para su ejecución posterior, aunque actualmente se prefiere el envío directo para correos electrónicos debido a problemas de entregabilidad.

### 1.3 Flujos de Trabajo Principales

#### 1.3.1 Flujo de WhatsApp a Respuesta de Texto

1. El usuario envía un mensaje de texto a través de WhatsApp.
2. Twilio reenvía el mensaje al webhook de GENIA.
3. El webhook valida la solicitud y delega el procesamiento a una tarea en segundo plano.
4. El CommandInterpreter utiliza el MCP de OpenAI para interpretar el comando.
5. El TaskExecutor ejecuta la tarea correspondiente (por ejemplo, generación de texto).
6. La respuesta se envía de vuelta al usuario a través del MCP de Twilio.

#### 1.3.2 Flujo de WhatsApp a Correo Electrónico

1. El usuario envía un mensaje solicitando generar contenido y enviarlo por correo.
2. El CommandInterpreter identifica el comando principal y la acción secundaria de envío de correo.
3. El TaskExecutor genera el contenido utilizando el MCP de OpenAI.
4. El contenido generado se envía por correo electrónico utilizando el MCP de Email.
5. Se notifica al usuario sobre el envío exitoso a través de WhatsApp.

#### 1.3.3 Flujo de Procesamiento de Audio

1. El usuario envía un mensaje de audio a través de WhatsApp.
2. El webhook identifica el tipo de contenido como audio y lo procesa.
3. El audio se transcribe utilizando el MCP de OpenAI.
4. El texto transcrito se procesa como un comando normal.
5. La respuesta se envía de vuelta al usuario a través de WhatsApp.

## 2. Oportunidades de Mejora Identificadas

### 2.1 Mejoras en el Procesamiento de Comandos

1. **Parseo Robusto de Respuestas JSON**
   - Implementar limpieza de formato markdown en respuestas de OpenAI antes de parsear JSON.
   - Añadir validación más estricta de la estructura de comandos interpretados.

2. **Detección Mejorada de Acciones Secundarias**
   - Ampliar el soporte para múltiples acciones secundarias en un solo comando.
   - Implementar priorización de acciones cuando se detectan múltiples.

3. **Manejo de Mensajes Largos**
   - Dividir automáticamente mensajes largos de WhatsApp para evitar errores de límite de caracteres.
   - Implementar compresión de contenido cuando sea apropiado.

### 2.2 Mejoras en la Integración de Servicios

1. **Gestión Centralizada de Credenciales**
   - Implementar un sistema seguro para almacenar y gestionar credenciales de servicios externos.
   - Añadir rotación automática de credenciales y monitoreo de uso.

2. **Registro y Monitoreo Mejorados**
   - Implementar logging estructurado para facilitar el análisis y la depuración.
   - Añadir métricas de rendimiento y disponibilidad para cada servicio MCP.

3. **Manejo de Errores y Recuperación**
   - Implementar reintentos inteligentes para operaciones fallidas.
   - Añadir circuitos de protección para evitar sobrecarga de servicios externos.

## 3. Plan de Integración de Servidores MCP

### 3.1 Arquitectura de Integración Propuesta

Para convertir a GENIA en un orquestador central de herramientas externas, se propone la siguiente arquitectura de integración:

1. **Capa de Orquestación MCP**
   - Implementar un módulo central que gestione la comunicación con los servidores MCP.
   - Desarrollar un registro dinámico de servidores MCP disponibles.
   - Crear un sistema de enrutamiento de comandos a los servidores MCP apropiados.

2. **Capa de Autenticación y Gestión de Credenciales**
   - Implementar almacenamiento seguro de credenciales para cada servicio.
   - Desarrollar flujos de autenticación para cada tipo de servidor MCP.
   - Crear un sistema de gestión de permisos y capacidades.

3. **Capa de Interpretación de Comandos Mejorada**
   - Ampliar el CommandInterpreter para reconocer comandos específicos para cada servicio.
   - Implementar mapeo de comandos en lenguaje natural a operaciones MCP.
   - Desarrollar un sistema de fallback y manejo de errores.

4. **Capa de Ejecución y Respuesta**
   - Adaptar el TaskExecutor para manejar múltiples servidores MCP.
   - Implementar gestión de respuestas y formateo según el tipo de servicio.
   - Desarrollar sistema de notificaciones y seguimiento de tareas.

### 3.2 Integraciones Prioritarias

Basado en el análisis de los servidores MCP disponibles y las necesidades del sistema, se recomienda la siguiente priorización de integraciones:

1. **Notion MCP Server**
   - Valor: Gestión de conocimiento y documentación.
   - Casos de uso: Creación y actualización de documentación mediante comandos de WhatsApp.
   - Integración: Añadir comandos específicos para Notion en el CommandInterpreter y funciones correspondientes en el TaskExecutor.

2. **GitHub MCP Server**
   - Valor: Automatización de desarrollo y gestión de código.
   - Casos de uso: Gestión de issues y pull requests mediante comandos de WhatsApp.
   - Integración: Implementar comandos para operaciones de GitHub y funciones de ejecución en el TaskExecutor.

3. **Slack MCP Server**
   - Valor: Comunicación y colaboración de equipo.
   - Casos de uso: Monitoreo y respuesta a conversaciones en Slack.
   - Integración: Añadir comandos para interactuar con canales de Slack y funciones correspondientes en el TaskExecutor.

4. **Google Workspace MCP Server**
   - Valor: Gestión de documentos y datos.
   - Casos de uso: Automatización de hojas de cálculo y gestión de documentos.
   - Integración: Implementar comandos para operaciones en Google Drive y Sheets.

5. **Instagram MCP Server**
   - Valor: Marketing y comunicación social.
   - Casos de uso: Automatización de respuestas a mensajes de Instagram.
   - Integración: Añadir comandos para interactuar con mensajes directos de Instagram.

## 4. Consideraciones Técnicas para la Implementación

### 4.1 Gestión de Dependencias

- Cada servidor MCP tiene sus propias dependencias y requisitos.
- Se recomienda utilizar contenedores Docker para aislar entornos.
- Implementar sistema de verificación de dependencias y autoinstalación.

### 4.2 Seguridad y Privacidad

- Almacenamiento seguro de credenciales (no en texto plano).
- Implementación de cifrado para comunicaciones.
- Gestión granular de permisos y capacidades.
- Auditoría y logging de operaciones sensibles.

### 4.3 Escalabilidad

- Diseñar para soportar múltiples instancias de servidores MCP.
- Implementar balanceo de carga y recuperación ante fallos.
- Considerar límites de API y estrategias de rate limiting.

### 4.4 Mantenibilidad

- Documentación exhaustiva de integraciones.
- Pruebas automatizadas para cada servidor MCP.
- Monitoreo de salud y disponibilidad.
- Estrategia de actualización y versionado.

## 5. Próximos Pasos Recomendados

1. **Corto Plazo**
   - Implementar las correcciones identificadas en el CommandInterpreter y el WhatsappTool.
   - Desarrollar pruebas automatizadas para validar el flujo completo de WhatsApp a correo.
   - Crear entorno de desarrollo para pruebas de integración con servidores MCP.

2. **Medio Plazo**
   - Implementar sistema de gestión de credenciales.
   - Desarrollar prueba de concepto con Notion MCP Server.
   - Adaptar CommandInterpreter para reconocer comandos de Notion.
   - Implementar flujo completo de WhatsApp a Notion.

3. **Largo Plazo**
   - Desarrollar la capa de orquestación central.
   - Implementar integraciones con los demás servidores MCP según priorización.
   - Crear sistema de gestión de sesiones y contexto para interacciones complejas.
   - Implementar monitoreo y logging avanzado para todas las integraciones.

## 6. Conclusiones

La arquitectura actual de GENIA proporciona una base sólida para la integración de servidores MCP adicionales. Con las mejoras propuestas y el plan de integración detallado, GENIA puede evolucionar hacia un orquestador central de herramientas externas, alineándose con la visión del proyecto.

La implementación gradual y modular permitirá obtener valor rápidamente mientras se construye una base sólida para futuras integraciones. Es fundamental mantener un enfoque en la seguridad, la escalabilidad y la mantenibilidad durante todo el proceso de integración.
