from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from app.core.security import create_access_token
from app.db.supabase_manager import get_supabase_client
from pydantic import BaseModel
from datetime import timedelta
import httpx

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None
    referral_code: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

@router.post("/register", response_model=Token, summary="Registrar un nuevo usuario")
async def register_user(user_data: UserCreate):
    """
    Registra un nuevo usuario en el sistema.
    
    - **email**: Email del usuario
    - **password**: Contraseña del usuario
    - **name**: Nombre del usuario (opcional)
    - **referral_code**: Código de referido (opcional)
    """
    try:
        supabase = get_supabase_client()
        
        # Verificar si el usuario ya existe
        existing_user = await supabase.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
        
        # Crear usuario en Supabase Auth
        auth_response = supabase.client.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error al crear el usuario"
            )
        
        # Crear usuario en la tabla usuarios
        user_id = auth_response.user.id
        new_user = {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name or "",
            "plan": "free",
            "creditos": 100,  # Créditos iniciales para plan gratuito
            "modulos_activos": ["openai", "whatsapp_basic"],  # Módulos básicos
            "is_active": True,
            "referral_code": user_data.referral_code
        }
        
        user = await supabase.create_user(new_user)
        
        # Procesar código de referido si existe
        if user_data.referral_code:
            # Lógica para procesar el código de referido
            # (Buscar usuario referente, otorgar bonificaciones, etc.)
            pass
        
        # Generar token de acceso
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=60 * 24 * 7)  # 7 días
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/login", response_model=Token, summary="Iniciar sesión")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Inicia sesión en el sistema.
    
    - **username**: Email del usuario
    - **password**: Contraseña del usuario
    """
    try:
        supabase = get_supabase_client()
        
        # Autenticar usuario en Supabase Auth
        auth_response = supabase.client.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Obtener datos del usuario
        user_id = auth_response.user.id
        user = await supabase.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        # Verificar si el usuario está activo
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Usuario inactivo"
            )
        
        # Generar token de acceso
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=60 * 24 * 7)  # 7 días
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/google", summary="Iniciar autenticación con Google")
async def login_google(request: Request):
    """
    Inicia el flujo de autenticación con Google OAuth.
    """
    from app.core.config import settings
    
    # Construir URL de autorización de Google
    redirect_uri = f"{settings.OAUTH_REDIRECT_URL}/google"
    auth_url = f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&scope=email%20profile&access_type=offline"
    
    return {"auth_url": auth_url}

@router.get("/google/callback", response_model=Token, summary="Callback de autenticación con Google")
async def google_callback(code: str):
    """
    Procesa el callback de autenticación con Google OAuth.
    
    - **code**: Código de autorización de Google
    """
    try:
        from app.core.config import settings
        
        # Intercambiar código por token
        redirect_uri = f"{settings.OAUTH_REDIRECT_URL}/google"
        token_url = "https://oauth2.googleapis.com/token"
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error al obtener token de Google"
                )
            
            token_data = token_response.json()
            
            # Obtener información del usuario
            user_info_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            
            if user_info_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Error al obtener información del usuario de Google"
                )
            
            user_info = user_info_response.json()
            
            # Verificar si el usuario ya existe
            supabase = get_supabase_client()
            existing_user = await supabase.get_user_by_email(user_info["email"])
            
            if existing_user:
                # Usuario existente, generar token
                user_id = existing_user["id"]
                user = existing_user
            else:
                # Crear nuevo usuario
                auth_response = supabase.client.auth.sign_up({
                    "email": user_info["email"],
                    "password": None,  # No se requiere contraseña para OAuth
                    "options": {
                        "data": {
                            "name": user_info.get("name", ""),
                            "avatar_url": user_info.get("picture", "")
                        }
                    }
                })
                
                if not auth_response.user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Error al crear el usuario"
                    )
                
                # Crear usuario en la tabla usuarios
                user_id = auth_response.user.id
                new_user = {
                    "id": user_id,
                    "email": user_info["email"],
                    "name": user_info.get("name", ""),
                    "plan": "free",
                    "creditos": 100,  # Créditos iniciales para plan gratuito
                    "modulos_activos": ["openai", "whatsapp_basic"],  # Módulos básicos
                    "is_active": True,
                    "avatar_url": user_info.get("picture", "")
                }
                
                user = await supabase.create_user(new_user)
            
            # Almacenar tokens de OAuth
            await supabase.store_oauth_tokens(
                user_id=user_id,
                service="google",
                tokens={
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token", ""),
                    "expires_at": token_data.get("expires_in", 3600)
                }
            )
            
            # Generar token de acceso
            access_token = create_access_token(
                data={"sub": user_id},
                expires_delta=timedelta(minutes=60 * 24 * 7)  # 7 días
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/facebook", summary="Iniciar autenticación con Facebook")
async def login_facebook(request: Request):
    """
    Inicia el flujo de autenticación con Facebook OAuth.
    """
    from app.core.config import settings
    
    # Construir URL de autorización de Facebook
    redirect_uri = f"{settings.OAUTH_REDIRECT_URL}/facebook"
    auth_url = f"https://www.facebook.com/v12.0/dialog/oauth?client_id={settings.FACEBOOK_CLIENT_ID}&redirect_uri={redirect_uri}&scope=email,public_profile"
    
    return {"auth_url": auth_url}

@router.get("/facebook/callback", response_model=Token, summary="Callback de autenticación con Facebook")
async def facebook_callback(code: str):
    """
    Procesa el callback de autenticación con Facebook OAuth.
    
    - **code**: Código de autorización de Facebook
    """
    # Implementación similar a Google callback
    # ...
    
    # Placeholder para no extender demasiado el código
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Autenticación con Facebook en desarrollo"
    )
