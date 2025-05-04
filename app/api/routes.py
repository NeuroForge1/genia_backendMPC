from fastapi import APIRouter
# Import routers
from app.api.endpoints import auth, genia_ceo, payments, tools, user # Import the new user router

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Include GENIA CEO (MCP) routes
api_router.include_router(genia_ceo.router, prefix="/genia", tags=["GENIA CEO"])

# Include payment routes
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])

# Include tool routes with the correct prefix
api_router.include_router(tools.router, prefix="/tools", tags=["Tools"])

# Include user routes (including tasks)
api_router.include_router(user.router, prefix="/user", tags=["User"]) # Add the user router


