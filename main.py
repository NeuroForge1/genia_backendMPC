import uvicorn
from fastapi import FastAPI
# Se cambia la importación a Starlette
from starlette.middleware.cors import CORSMiddleware
import sentry_sdk
from app.api.routes import api_router
from app.core.config import settings

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

# --- Configuración CORS con Starlette Middleware (Prueba) ---
# Se usa una lista fija y el middleware de Starlette
FIXED_ALLOWED_ORIGINS = ["https://genia-frontend-mpc.vercel.app", "http://localhost:5173"]
print(f"[DEBUG] Configurando CORS con Starlette Middleware y orígenes FIJOS: {FIXED_ALLOWED_ORIGINS}") # Log para verificar
app.add_middleware(
    CORSMiddleware, # Ahora es de Starlette
    allow_origins=FIXED_ALLOWED_ORIGINS, # Usar lista fija
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- Fin Configuración CORS con Starlette ---

# Incluir rutas de la API
app.include_router(api_router, prefix=settings.API_V1_STR)

# Ruta de verificación de salud
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


