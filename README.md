# GENIA MCP - Backend

Este repositorio contiene el backend del proyecto GENIA MCP, una plataforma SaaS basada en el Modelo de Cliente Potenciado (MCP) que permite a los usuarios acceder a herramientas de IA y automatización.

## Tecnologías

- **FastAPI** - Framework web rápido para construir APIs con Python
- **Python 3.10+** - Lenguaje de programación
- **Supabase** - Backend as a Service para autenticación y base de datos
- **PostgreSQL** - Sistema de gestión de bases de datos relacional
- **Pydantic** - Validación de datos y configuración
- **JWT** - Autenticación basada en tokens
- **OpenAI API** - Integración con modelos de lenguaje GPT
- **Twilio API** - Integración con WhatsApp
- **Stripe API** - Procesamiento de pagos
- **Gmail API** - Integración con correo electrónico

## Arquitectura MCP

Este backend implementa el Modelo de Cliente Potenciado (MCP) basado en el protocolo de Anthropic, donde:

- **GENIA CEO** actúa como cliente MCP que orquesta las herramientas
- Cada herramienta es un servidor MCP independiente con capacidades específicas
- El sistema de orquestación gestiona la comunicación entre el cliente y los servidores
- Las herramientas exponen sus capacidades a través de un mecanismo de descubrimiento estandarizado

## Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Cuenta en Supabase
- Cuentas en servicios externos (OpenAI, Twilio, Stripe, Google)

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/NeuroForge1/genia_backendMPC.git
cd genia_backendMPC
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Crea un archivo `.env` en la raíz del proyecto basado en `.env.example`:
```bash
cp .env.example .env
```

4. Edita el archivo `.env` con tus credenciales y configuraciones.

## Desarrollo

Para iniciar el servidor de desarrollo:

```bash
uvicorn main:app --reload
```

El servidor estará disponible en `http://localhost:8000`.

## Estructura del Proyecto

```
app/
├── api/                # Definiciones de API
│   ├── endpoints/      # Endpoints de la API
│   └── routes.py       # Configuración de rutas
├── core/               # Núcleo de la aplicación
│   ├── config.py       # Configuración de la aplicación
│   └── security.py     # Funciones de seguridad
├── db/                 # Capa de base de datos
│   └── supabase_manager.py  # Gestión de Supabase
├── services/           # Servicios de la aplicación
│   └── orchestrator.py # Orquestador de herramientas MCP
├── tools/              # Herramientas MCP
│   ├── base_tool.py    # Clase base para herramientas
│   ├── openai_tool.py  # Herramienta de OpenAI
│   ├── whatsapp_tool.py # Herramienta de WhatsApp
│   ├── stripe_tool.py  # Herramienta de Stripe
│   ├── gmail_tool.py   # Herramienta de Gmail
│   └── ...             # Otras herramientas
└── utils/              # Utilidades
tests/                  # Pruebas
docs/                   # Documentación
```

## Herramientas Implementadas

- **OpenAI Tool** - Generación de texto y procesamiento de lenguaje natural
- **WhatsApp Tool** - Envío y recepción de mensajes de WhatsApp
- **Stripe Tool** - Procesamiento de pagos y gestión de suscripciones
- **Gmail Tool** - Envío de correos electrónicos
- **Content Tool** - Generación y gestión de contenido
- **Funnels Tool** - Creación y gestión de embudos de ventas
- **WhatsApp Analysis Tool** - Análisis de conversaciones de WhatsApp
- **AI Assistant Tool** - Creación y gestión de asistentes de IA
- **Webhook Integration Tool** - Gestión de integraciones mediante webhooks
- **SEO Analysis Tool** - Análisis y optimización SEO

## API Endpoints

La documentación de la API está disponible en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Principales Endpoints

- `/api/health` - Verificación de estado del servidor
- `/api/auth/*` - Endpoints de autenticación
- `/api/genia/tools` - Obtener herramientas disponibles
- `/api/genia/execute` - Ejecutar una herramienta
- `/api/payments/*` - Endpoints de pagos
- `/api/user/*` - Endpoints de usuario

## Despliegue

El backend está configurado para ser desplegado en Render. Para desplegar:

1. Conecta tu repositorio de GitHub a Render
2. Configura las variables de entorno en Render según `.env.example`
3. Render automáticamente desplegará la aplicación

## Base de Datos

El esquema de la base de datos se encuentra en `app/db/supabase_schema.md` y el script SQL para inicializar la base de datos en `app/db/supabase_init.sql`.

## Pruebas

Para ejecutar las pruebas:

```bash
pytest
```

O utiliza el script de prueba:

```bash
bash test.sh
```

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Para cualquier consulta o sugerencia, por favor contacta a [tu-email@ejemplo.com](mailto:tu-email@ejemplo.com).
