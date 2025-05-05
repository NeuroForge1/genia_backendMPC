# /home/ubuntu/genia_backendMPC/simulate_twilio_webhook.py

import httpx
import asyncio
import hmac
import hashlib
import os
from urllib.parse import urlencode

# --- Configuración ---
# Asegúrate de que esta URL coincida con donde corres el backend localmente
BACKEND_URL = "http://localhost:8000/webhook/twilio/whatsapp"
# Usa el MISMO Auth Token que configurarías en las variables de entorno del backend
# ¡ESTO ES SOLO PARA PRUEBAS LOCALES! No expongas tu Auth Token real.
# Intenta obtenerlo del .env si existe, si no, usa un placeholder.
try:
    with open(".env", "r") as f:
        for line in f:
            if line.startswith("TWILIO_AUTH_TOKEN="):
                TWILIO_AUTH_TOKEN = line.strip().split("=", 1)[1]
                break
        else:
            TWILIO_AUTH_TOKEN = "TU_TWILIO_AUTH_TOKEN_AQUI" # Placeholder
except FileNotFoundError:
    TWILIO_AUTH_TOKEN = "TU_TWILIO_AUTH_TOKEN_AQUI" # Placeholder

# --- Datos de Ejemplo (Simulando mensaje de texto) ---
# Puedes modificar estos valores para tus pruebas
EXAMPLE_PAYLOAD = {
    "SmsMessageSid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "NumMedia": "0",
    "ProfileName": "Usuario Prueba",
    "SmsSid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "WaId": "16575143018", # Número del remitente (tu número)
    "SmsStatus": "received",
    "Body": "Genera un poema corto sobre el sol", # El comando a probar
    "To": "whatsapp:+14155238886", # Número de la Sandbox de Twilio
    "NumSegments": "1",
    "MessageSid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", # Tu Account SID
    "From": "whatsapp:+16575143018", # Número del remitente (tu número)
    "ApiVersion": "2010-04-01"
}

# --- Función para generar firma Twilio (Necesaria si el webhook la valida) ---
def generate_twilio_signature(url: str, params: dict, auth_token: str) -> str:
    """Genera la firma X-Twilio-Signature para validar la solicitud."""
    # Ordenar parámetros alfabéticamente
    sorted_params = sorted(params.items())
    # Concatenar URL y parámetros ordenados
    data_string = url + "".join([f"{k}{v}" for k, v in sorted_params])
    # Calcular HMAC-SHA1
    signature = hmac.new(
        auth_token.encode("utf-8"),
        data_string.encode("utf-8"),
        hashlib.sha1
    ).digest()
    # Codificar en Base64
    import base64
    return base64.b64encode(signature).decode("utf-8")

# --- Función Principal Asíncrona ---
async def send_simulated_request():
    print(f"Simulando solicitud POST a: {BACKEND_URL}")
    print(f"Payload: {EXAMPLE_PAYLOAD}")

    if TWILIO_AUTH_TOKEN == "TU_TWILIO_AUTH_TOKEN_AQUI":
        print("\nADVERTENCIA: TWILIO_AUTH_TOKEN no encontrado en .env. La validación de firma fallará si está activa en el webhook.")
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    else:
        # Generar firma
        signature = generate_twilio_signature(BACKEND_URL, EXAMPLE_PAYLOAD, TWILIO_AUTH_TOKEN)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Twilio-Signature": signature
        }
        print(f"Firma generada: {signature}")

    # Codificar payload para x-www-form-urlencoded
    encoded_payload = urlencode(EXAMPLE_PAYLOAD)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(BACKEND_URL, content=encoded_payload, headers=headers)
            print(f"\nRespuesta recibida:")
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {response.headers}")
            print(f"Body: {response.text}")
        except httpx.RequestError as e:
            print(f"\nError al enviar la solicitud: {e}")
            print("Asegúrate de que el backend esté corriendo en http://localhost:8000")

# --- Ejecutar la simulación ---
if __name__ == "__main__":
    asyncio.run(send_simulated_request())

