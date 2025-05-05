# /home/ubuntu/genia_backendMPC/main.py
import uvicorn
import os # Added os import for getenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Re-añadir importación de JSONResponse para el handler OPTIONS
from fastapi.responses import JSONResponse 
import sentry_sdk
from app.api.routes import api_router
# Importar el router del webhook de Twilio
from app.webhooks.twilio_webhook import router as twilio_webhook_router
# Importar settings y la variable CORS_ORIGINS parseada
from app.core.config import settings, CORS_ORIGINS

# Configurar Sentry para monitoreo de errores
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT
    )

app = FastAPI(
    title="GENIA MCP API",
    description="API para la plataforma GENIA basada en el Modelo de Cliente Potenciado (MCP)",
    version="1.0.0",
)

# --- TEMPORARILY COMMENTED OUT FOR DEBUGGING 405 ERROR ---
# # --- Configuración CORS Corregida (Usando Variable parseada del módulo config) ---
# # Usar la variable CORS_ORIGINS importada directamente desde config
# if CORS_ORIGINS:
#     print(f"[DEBUG] Configurando CORS con orígenes parseados: {CORS_ORIGINS}") # Log para verificar
#     app.add_middleware(
#         CORSMiddleware, # Middleware de FastAPI
#         allow_origins=CORS_ORIGINS, # Usar la lista ya parseada
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
# else:
#     print("[WARN] CORS_ORIGINS no está configurado o parseado correctamente. CORS no habilitado.")
# # --- Fin Configuración CORS Corregida ---

# # --- TEMPORARILY COMMENTED OUT FOR DEBUGGING 405 ERROR ---
# # --- RE-AÑADIDO Manejador Explícito OPTIONS ---
# @app.options("/{rest_of_path:path}")
# async def preflight_handler(rest_of_path: str):
#     print(f"[DEBUG] Manejando solicitud OPTIONS explícita para: /{rest_of_path}")
#     # Devolver cabeceras CORS necesarias para la solicitud preflight
#     # Asegurarse de que CORS_ORIGINS se use correctamente aquí también
#     origin_header = ",".join(CORS_ORIGINS) if CORS_ORIGINS else "*"
#     return JSONResponse(
#         content={"message": "Preflight check successful"},
#         headers={
#             "Access-Control-Allow-Origin": origin_header, # Usar la variable global parseada
#             "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
#             "Access-Control-Allow-Headers": "*", # Permitir todas las cabeceras solicitadas
#             "Access-Control-Allow-Credentials": "true",
#         }
#     )
# # --- Fin RE-AÑADIDO Manejador Explícito OPTIONS ---

# Incluir rutas de la API (después de CORS y OPTIONS handler)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Incluir el router del webhook de Twilio
app.include_router(twilio_webhook_router, prefix="/webhook", tags=["Webhooks"])

# Ruta de verificación de salud
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    # Asegúrate de que las URLs de los servidores MCP estén configuradas correctamente
    # (pueden necesitar ser accesibles desde donde corre el backend)
    # Por ahora, asumimos que corren en localhost si el backend corre localmente.
    # Si el backend corre en Render, los MCP servers también deberían correr allí o ser accesibles públicamente.
    # ¡IMPORTANTE! Para Render, el host debe ser 0.0.0.0 y el puerto lo define Render (usualmente 10000 o variable PORT).
    port = int(os.getenv("PORT", 8000)) # Usar variable PORT si existe (común en Render), sino 8000
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.ENVIRONMENT == "development") # Desactivar reload en producción

