import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Eliminar importación innecesaria de JSONResponse
# from fastapi.responses import JSONResponse 
import sentry_sdk
from app.api.routes import api_router
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

# --- Configuración CORS Corregida (Usando Variable parseada del módulo config) ---
# Usar la variable CORS_ORIGINS importada directamente desde config
if CORS_ORIGINS:
    print(f"[DEBUG] Configurando CORS con orígenes parseados: {CORS_ORIGINS}") # Log para verificar
    app.add_middleware(
        CORSMiddleware, # Middleware de FastAPI
        allow_origins=CORS_ORIGINS, # Usar la lista ya parseada
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    print("[WARN] CORS_ORIGINS no está configurado o parseado correctamente. CORS no habilitado.")
# --- Fin Configuración CORS Corregida ---

# --- ELIMINADO Manejador Explícito OPTIONS ---
# @app.options("/{rest_of_path:path}")
# async def preflight_handler(rest_of_path: str):
#     print(f"[DEBUG] Manejando solicitud OPTIONS explícita para: /{rest_of_path}")
#     return JSONResponse(content={"message": "Preflight check successful"})
# --- Fin ELIMINADO Manejador Explícito OPTIONS ---

# Incluir rutas de la API (después de CORS)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Ruta de verificación de salud
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


