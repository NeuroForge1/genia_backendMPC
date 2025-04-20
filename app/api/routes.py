from fastapi import APIRouter
from app.api.endpoints import auth, genia_ceo, payments

api_router = APIRouter()

# Incluir rutas de autenticación
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])

# Incluir rutas de GENIA CEO (MCP)
api_router.include_router(genia_ceo.router, prefix="/genia", tags=["GENIA CEO"])

# Incluir rutas de pagos
api_router.include_router(payments.router, prefix="/payments", tags=["Pagos"])
