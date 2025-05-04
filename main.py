import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk
from app.api.routes import api_router
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

# Configurar CORS usando la variable global CORS_ORIGINS
# Asegurarse de que CORS_ORIGINS se procesa correctamente en config.py
print(f"[DEBUG] Configurando CORS con orígenes: {CORS_ORIGINS}") # Log para verificar
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS, # Revertir al uso de la configuración
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas de la API
app.include_router(api_router, prefix=settings.API_V1_STR)

# Ruta de verificación de salud
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

