import uvicorn
from fastapi import FastAPI
# Revertir a la importación original de FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Importar JSONResponse para el handler OPTIONS
from fastapi.responses import JSONResponse
import sentry_sdk
from app.api.routes import api_router
# Asegurarse de que settings se importa para leer CORS_ORIGINS
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

# --- Configuración CORS Original (Usando Variable de Entorno) ---
if settings.CORS_ORIGINS:
    print(f"[DEBUG] Configurando CORS con orígenes desde Env Var: {settings.CORS_ORIGINS}") # Log para verificar
    app.add_middleware(
        CORSMiddleware, # Middleware de FastAPI
        allow_origins=[str(origin).strip() for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    print("[WARN] CORS_ORIGINS no está configurado. CORS no habilitado.")
# --- Fin Configuración CORS Original ---

# --- Manejador Explícito OPTIONS (Paso 3 Prueba) ---
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    print(f"[DEBUG] Manejando solicitud OPTIONS explícita para: /{rest_of_path}")
    # Devolver una respuesta simple con cabeceras CORS permisivas
    # Nota: El middleware CORS debería añadir las cabeceras correctas si está configurado
    # Esta ruta es más un 'catch-all' para asegurar que OPTIONS no falle con 404 o 405
    return JSONResponse(content={"message": "Preflight check successful"})
# --- Fin Manejador Explícito OPTIONS ---

# Incluir rutas de la API (después de CORS y OPTIONS handler)
app.include_router(api_router, prefix=settings.API_V1_STR)

# Ruta de verificación de salud
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


