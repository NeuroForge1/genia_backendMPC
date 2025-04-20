# Implementación de Integraciones Externas para GENIA MCP

Este documento detalla la implementación de las integraciones externas para el proyecto GENIA MCP, incluyendo OpenAI, Twilio (WhatsApp), Stripe y Gmail.

## 1. Integración con OpenAI

La integración con OpenAI ya está implementada en el archivo `app/tools/openai_tool.py` y permite:

- Generación de texto utilizando GPT-4
- Transcripción de audio utilizando Whisper

### Configuración

1. Obtener una API key de OpenAI desde [OpenAI Platform](https://platform.openai.com/api-keys)
2. Configurar la variable de entorno `OPENAI_API_KEY` en el archivo `.env`

### Ejemplo de Uso

```python
from app.tools.openai_tool import OpenAITool

# Inicializar la herramienta
openai_tool = OpenAITool()

# Generar texto
result = await openai_tool.execute(
    user_id="user123",
    capability="generate_text",
    params={
        "prompt": "Explica el concepto de inteligencia artificial en términos simples",
        "max_tokens": 500,
        "temperature": 0.7
    }
)

# Transcribir audio
result = await openai_tool.execute(
    user_id="user123",
    capability="transcribe_audio",
    params={
        "audio_url": "https://example.com/audio.mp3"
    }
)
```

## 2. Integración con Twilio (WhatsApp)

La integración con Twilio para WhatsApp está implementada en el archivo `app/tools/whatsapp_tool.py` y permite:

- Envío de mensajes de WhatsApp
- Envío de mensajes de plantilla de WhatsApp

### Configuración

1. Crear una cuenta en [Twilio](https://www.twilio.com/)
2. Configurar un número de WhatsApp en Twilio
3. Configurar las siguientes variables de entorno en el archivo `.env`:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_NUMBER`

### Configuración de Webhook para Recepción de Mensajes

Para recibir mensajes de WhatsApp, es necesario configurar un webhook en Twilio:

1. En el panel de Twilio, ir a "Messaging" > "Settings" > "WhatsApp Sandbox"
2. Configurar el webhook URL: `https://[TU-BACKEND].render.com/api/webhooks/twilio`
3. Implementar el endpoint en el backend:

```python
@router.post("/webhooks/twilio")
async def twilio_webhook(request: Request):
    form_data = await request.form()
    
    # Extraer información del mensaje
    message_sid = form_data.get("MessageSid")
    from_number = form_data.get("From")
    to_number = form_data.get("To")
    body = form_data.get("Body")
    
    # Procesar el mensaje (ejemplo)
    # Aquí se podría implementar lógica para responder automáticamente
    # o para enviar el mensaje a un sistema de procesamiento
    
    return {"status": "success"}
```

### Ejemplo de Uso

```python
from app.tools.whatsapp_tool import WhatsAppTool

# Inicializar la herramienta
whatsapp_tool = WhatsAppTool()

# Enviar mensaje
result = await whatsapp_tool.execute(
    user_id="user123",
    capability="send_message",
    params={
        "to": "+1234567890",
        "message": "Hola, este es un mensaje de prueba desde GENIA MCP."
    }
)

# Enviar mensaje de plantilla
result = await whatsapp_tool.execute(
    user_id="user123",
    capability="send_template",
    params={
        "to": "+1234567890",
        "template_name": "appointment_reminder",
        "template_params": {
            "name": "Juan",
            "date": "20 de abril de 2025",
            "time": "15:00"
        }
    }
)
```

## 3. Integración con Stripe

La integración con Stripe está implementada en el archivo `app/tools/stripe_tool.py` y permite:

- Creación de intentos de pago
- Creación de suscripciones
- Creación de clientes

### Configuración

1. Crear una cuenta en [Stripe](https://stripe.com/)
2. Obtener las claves API desde el panel de Stripe
3. Configurar las siguientes variables de entorno en el archivo `.env`:
   - `STRIPE_PUBLIC_KEY`
   - `STRIPE_SECRET_KEY`
   - `STRIPE_WEBHOOK_SECRET`

### Configuración de Webhook para Eventos de Stripe

Para recibir eventos de Stripe (como pagos exitosos o suscripciones canceladas), es necesario configurar un webhook:

1. En el panel de Stripe, ir a "Developers" > "Webhooks"
2. Añadir un endpoint: `https://[TU-BACKEND].render.com/api/payments/webhook`
3. Seleccionar los eventos a escuchar (por ejemplo, `checkout.session.completed`, `customer.subscription.updated`, etc.)
4. Obtener el webhook secret y configurarlo en la variable de entorno `STRIPE_WEBHOOK_SECRET`

El endpoint para procesar los webhooks ya está implementado en `app/api/endpoints/payments.py`.

### Ejemplo de Uso

```python
from app.tools.stripe_tool import StripeTool

# Inicializar la herramienta
stripe_tool = StripeTool()

# Crear intento de pago
result = await stripe_tool.execute(
    user_id="user123",
    capability="create_payment",
    params={
        "amount": 2500,  # en centavos (25.00 USD)
        "currency": "usd",
        "description": "Compra de créditos GENIA",
        "metadata": {
            "product_id": "credits_500"
        }
    }
)

# Crear suscripción
result = await stripe_tool.execute(
    user_id="user123",
    capability="create_subscription",
    params={
        "customer_id": "cus_123456789",
        "price_id": "price_1234567890",
        "metadata": {
            "plan": "pro"
        }
    }
)

# Crear cliente
result = await stripe_tool.execute(
    user_id="user123",
    capability="create_customer",
    params={
        "email": "usuario@ejemplo.com",
        "name": "Usuario Ejemplo",
        "metadata": {
            "referral_code": "REF123"
        }
    }
)
```

## 4. Integración con Gmail

La integración con Gmail está implementada en el archivo `app/tools/gmail_tool.py` y permite:

- Envío de correos electrónicos
- Envío de correos electrónicos a múltiples destinatarios

### Configuración

1. Crear un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
2. Habilitar la API de Gmail
3. Configurar OAuth 2.0 (como se detalla en el documento de autenticación OAuth)
4. Configurar las siguientes variables de entorno en el archivo `.env`:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

### Flujo de Autorización

Para que un usuario pueda enviar correos a través de su cuenta de Gmail, debe autorizar la aplicación:

1. El usuario inicia el flujo de autorización desde la interfaz de usuario
2. Es redirigido a la página de consentimiento de Google
3. Después de autorizar, los tokens se almacenan en la tabla `herramientas_conectadas` en Supabase
4. Estos tokens se utilizan para enviar correos en nombre del usuario

### Ejemplo de Uso

```python
from app.tools.gmail_tool import GmailTool

# Inicializar la herramienta
gmail_tool = GmailTool()

# Enviar correo
result = await gmail_tool.execute(
    user_id="user123",
    capability="send_email",
    params={
        "to": "destinatario@ejemplo.com",
        "subject": "Prueba desde GENIA MCP",
        "body": "Este es un correo de prueba enviado desde GENIA MCP.",
        "html": False
    }
)

# Enviar correo a múltiples destinatarios
result = await gmail_tool.execute(
    user_id="user123",
    capability="send_bulk_email",
    params={
        "to_list": [
            "destinatario1@ejemplo.com",
            "destinatario2@ejemplo.com",
            "destinatario3@ejemplo.com"
        ],
        "subject": "Anuncio importante",
        "body": "<h1>Nuevo lanzamiento</h1><p>Estamos emocionados de anunciar...</p>",
        "html": True
    }
)
```

## 5. Integración con Herramientas Adicionales

Además de las integraciones principales, el sistema incluye herramientas adicionales:

### Content Tool

Implementada en `app/tools/content_tool.py`, permite:

- Generación de publicaciones para redes sociales
- Generación de campañas de email marketing
- Generación de artículos de blog
- Análisis de sentimiento de textos

### Funnels Tool

Implementada en `app/tools/funnels_tool.py`, permite:

- Creación de embudos de ventas completos
- Generación de contenido para landing pages
- Creación de secuencias de emails para embudos de ventas

## Consideraciones de Seguridad

1. **Almacenamiento de Tokens**: Los tokens de acceso y actualización se almacenan de forma segura en Supabase con políticas RLS.
2. **Renovación de Tokens**: Se implementa lógica para renovar tokens expirados automáticamente.
3. **Limitación de Acceso**: Las herramientas verifican que el usuario tenga acceso según su plan.
4. **Auditoría**: Todas las acciones se registran en la tabla `tareas_generadas` para seguimiento y auditoría.
5. **Manejo de Errores**: Se implementa manejo de errores robusto para evitar exposición de información sensible.

## Pruebas de Integración

Para probar las integraciones:

1. Configurar todas las variables de entorno necesarias
2. Ejecutar el backend en modo desarrollo:
   ```
   cd genia_backendMPC
   uvicorn main:app --reload
   ```
3. Utilizar herramientas como Postman o la interfaz Swagger de FastAPI para probar los endpoints
4. Verificar que las integraciones funcionen correctamente y manejen los errores adecuadamente

## Documentación de APIs

La documentación completa de las APIs está disponible en:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Estas interfaces proporcionan documentación interactiva de todos los endpoints, incluyendo los relacionados con las integraciones externas.
