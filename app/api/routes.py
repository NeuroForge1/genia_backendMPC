from fastapi import APIRouter
# Import the new tools router
from app.api.endpoints import auth, genia_ceo, payments, tools

api_router = APIRouter()

# Incluir rutas de autenticación
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])

# Incluir rutas de GENIA CEO (MCP)
api_router.include_router(genia_ceo.router, prefix="/genia", tags=["GENIA CEO"])

# Incluir rutas de pagos
api_router.include_router(payments.router, prefix="/payments", tags=["Pagos"])

# Incluir rutas de herramientas con el prefijo correcto
api_router.include_router(tools.router, prefix="/api/v1/tools", tags=["Herramientas"])


