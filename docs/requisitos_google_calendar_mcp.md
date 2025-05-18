# Requisitos y Limitaciones del Servidor MCP de Google Calendar

## Introducción

Este documento detalla los requisitos técnicos y limitaciones identificadas durante la integración del servidor MCP de Google Calendar en la arquitectura GENIA. Es fundamental tener en cuenta estos requisitos para garantizar un despliegue exitoso en entornos de producción.

## Requisitos Técnicos

### 1. Python 3.13+

El servidor MCP de Google Calendar requiere **Python 3.13 o superior**. Esta es una limitación crítica, ya que:

- El archivo `pyproject.toml` especifica explícitamente `requires-python = ">=3.13"`
- Las pruebas de validación confirman que versiones anteriores de Python (como 3.11) no son compatibles
- Algunas características del código pueden depender de funcionalidades introducidas en Python 3.13

**Solución para producción:**
- Asegurar que el entorno de Render tenga Python 3.13+ instalado
- Configurar el archivo `runtime.txt` para especificar la versión de Python requerida
- Alternativamente, utilizar contenedores Docker con la versión correcta de Python

### 2. UV Package Manager

El servidor MCP de Google Calendar utiliza **UV Package Manager** para la gestión de dependencias, en lugar de pip tradicional. Esto implica:

- UV debe estar instalado en el entorno de ejecución
- Los comandos de instalación y ejecución utilizan UV en lugar de pip/python
- El archivo `uv.lock` contiene las dependencias exactas requeridas

**Solución para producción:**
- Instalar UV Package Manager en el entorno de Render
- Incluir la instalación de UV en el script de inicio
- Configurar los comandos de ejecución para utilizar UV

### 3. Supabase para Gestión de Tokens

La integración requiere **Supabase** para el almacenamiento seguro de tokens y credenciales de usuario:

- Se necesita una instancia de Supabase configurada y accesible
- Las tablas necesarias (`user_tokens`) deben estar creadas
- Las variables de entorno `SUPABASE_URL`, `SUPABASE_KEY` y `SUPABASE_JWT_SECRET` deben estar configuradas

**Solución para producción:**
- Configurar las variables de entorno en Render
- Ejecutar las migraciones SQL necesarias para crear las tablas
- Verificar la conectividad con Supabase antes de iniciar el servidor

### 4. Credenciales OAuth de Google Cloud

Para que el servidor funcione, se requieren **credenciales OAuth de Google Cloud**:

- Proyecto en Google Cloud con la API de Google Calendar habilitada
- Credenciales OAuth configuradas para aplicación de escritorio
- Archivo `credentials.json` con las credenciales del proyecto

**Solución para producción:**
- Crear un proyecto en Google Cloud y habilitar la API de Google Calendar
- Configurar credenciales OAuth para aplicación de escritorio
- Almacenar el archivo `credentials.json` en un lugar seguro y accesible por el servidor

### 5. Permisos de Sistema de Archivos

El servidor requiere permisos para:

- Crear y modificar archivos en el directorio de credenciales
- Ejecutar comandos del sistema operativo
- Acceder a recursos de red

**Solución para producción:**
- Configurar los directorios con los permisos adecuados
- Utilizar un usuario con privilegios suficientes para la ejecución
- Verificar que el directorio base sea accesible y modificable

## Limitaciones Identificadas

### 1. Compatibilidad con Entornos Actuales

La principal limitación es la **incompatibilidad con entornos Python 3.11 o anteriores**, lo que puede requerir:

- Actualización de entornos existentes
- Uso de contenedores Docker específicos
- Configuración especial en Render para soportar Python 3.13+

### 2. Dependencia de UV Package Manager

La dependencia de UV Package Manager puede ser problemática en entornos que utilizan exclusivamente pip:

- Requiere instalación adicional
- Puede complicar la integración con sistemas CI/CD existentes
- Introduce una herramienta adicional en el flujo de trabajo

### 3. Simulación vs. Ejecución Real

Durante la validación, se identificó que:

- La ejecución real del servidor MCP requiere un entorno completo con todas las dependencias
- En entornos limitados, solo es posible simular las operaciones
- Las pruebas completas deben realizarse en un entorno de producción o similar

## Recomendaciones para Despliegue

1. **Entorno Aislado**: Utilizar un contenedor Docker con Python 3.13+ y UV preinstalados
2. **Validación Progresiva**: Implementar pruebas en etapas, verificando cada componente individualmente
3. **Monitoreo Detallado**: Configurar logging exhaustivo para detectar problemas durante la ejecución
4. **Fallback Automático**: Implementar mecanismos de fallback para operaciones críticas
5. **Documentación Clara**: Mantener actualizada la documentación de requisitos y procedimientos

## Conclusión

El servidor MCP de Google Calendar ofrece una integración potente con GENIA, pero requiere un entorno específico y configuración cuidadosa. Siguiendo las recomendaciones de este documento, es posible superar las limitaciones identificadas y lograr una implementación exitosa en producción.
