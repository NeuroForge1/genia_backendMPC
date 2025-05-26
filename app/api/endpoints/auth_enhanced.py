from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from app.core.security import create_access_token
from app.db.supabase_manager import get_supabase_client
from pydantic import BaseModel, EmailStr
from datetime import timedelta, datetime
import httpx
from supabase.lib.client_options import ClientOptions
from gotrue.errors import AuthApiError
import logging
import json
import time
import traceback

# Configuración de logging específica para autenticación
auth_logger = logging.getLogger("auth_detailed")
auth_logger.setLevel(logging.DEBUG)

# Aseguramos que los handlers no se dupliquen
if not auth_logger.handlers:
    # Handler para consola con formato detallado
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    auth_logger.addHandler(console_handler)

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr # Use Pydantic's EmailStr for basic validation
    password: str
    name: Optional[str] = None
    referral_code: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

# Función para registrar eventos de autenticación con detalles
def log_auth_event(event_type: str, details: Dict[str, Any], error: Optional[Exception] = None):
    """
    Registra eventos detallados del proceso de autenticación.
    
    Args:
        event_type: Tipo de evento (register_start, register_success, register_error, etc.)
        details: Diccionario con detalles relevantes del evento
        error: Excepción opcional si ocurrió un error
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details
    }
    
    if error:
        log_entry["error"] = {
            "type": type(error).__name__,
            "message": str(error),
            "traceback": traceback.format_exc()
        }
        auth_logger.error(f"AUTH_EVENT: {json.dumps(log_entry, default=str)}")
    else:
        auth_logger.info(f"AUTH_EVENT: {json.dumps(log_entry, default=str)}")

@router.post("/register", response_model=Token, summary="Registrar un nuevo usuario")
async def register_user(request: Request, user_data: UserCreate):
    """
    Registra un nuevo usuario en el sistema.
    
    - **email**: Email del usuario
    - **password**: Contraseña del usuario
    - **name**: Nombre del usuario (opcional)
    - **referral_code**: Código de referido (opcional)
    """
    # Registrar inicio del proceso de registro
    request_info = {
        "client_ip": request.client.host,
        "method": request.method,
        "path": request.url.path,
        "user_agent": request.headers.get("user-agent")
    }
    
    user_info = {
        "email": user_data.email,
        "name": user_data.name,
        "has_referral_code": user_data.referral_code is not None
    }
    
    log_auth_event(
        "register_start",
        {
            "request": request_info,
            "user_data": user_info
        }
    )
    
    start_time = time.time()
    supabase = get_supabase_client()
    auth_user = None
    db_user = None

    try:
        # 1. Verificar si el usuario ya existe en la tabla 'usuarios'
        log_auth_event("check_existing_user_start", {"email": user_data.email})
        existing_db_user = await supabase.get_user_by_email(user_data.email)
        log_auth_event("check_existing_user_complete", {"exists": existing_db_user is not None})
        
        if existing_db_user:
            error_msg = "El email ya está registrado en nuestra base de datos."
            log_auth_event("register_error", {"reason": error_msg})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # 2. Intentar crear usuario en Supabase Auth
        log_auth_event("supabase_auth_signup_start", {"email": user_data.email})
        try:
            auth_response = supabase.client.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {"email_confirm": False} # Desactivar confirmación de email para pruebas
            })
            auth_user = auth_response.user
            log_auth_event("supabase_auth_signup_success", {
                "user_id": auth_user.id if auth_user else None,
                "email": user_data.email
            })
            
            if not auth_user:
                 # Si sign_up no devuelve usuario pero tampoco lanza excepción (poco probable pero posible)
                 error_msg = "Error inesperado durante el registro en Supabase Auth."
                 log_auth_event("register_error", {"reason": error_msg})
                 raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )

        except AuthApiError as e:
            # Capturar errores específicos de Supabase Auth
            error_details = {"error_message": str(e), "error_type": "AuthApiError"}
            log_auth_event("supabase_auth_signup_error", error_details, error=e)
            
            if "User already registered" in str(e):
                 error_msg = "El email ya está registrado en el sistema de autenticación."
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            elif "Unable to validate email address" in str(e):
                 error_msg = "El formato del correo electrónico no es válido según Supabase."
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            elif "Password should be at least 6 characters" in str(e):
                 error_msg = "La contraseña debe tener al menos 6 caracteres."
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            else:
                # Otro error de Supabase Auth
                error_msg = f"Error de Supabase Auth: {str(e)}"
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )
        except Exception as e:
             # Otros errores inesperados durante sign_up
             error_details = {"error_message": str(e), "error_type": type(e).__name__}
             log_auth_event("supabase_auth_signup_error", error_details, error=e)
             
             error_msg = f"Error inesperado al intentar registrar en Supabase Auth: {str(e)}"
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        # 3. Crear usuario en la tabla 'usuarios' de la base de datos
        user_id = auth_user.id
        new_user_data = {
            "id": user_id,
            "email": user_data.email,
            "name": user_data.name or "",
            "plan": "free",
            "creditos": 100,  # Créditos iniciales para plan gratuito
            "modulos_activos": ["openai", "whatsapp_basic"],  # Módulos básicos
            "is_active": True, # O False si requiere verificación de email
            "referral_code": user_data.referral_code
        }
        
        log_auth_event("create_db_user_start", {
            "user_id": user_id,
            "email": user_data.email,
            "user_data": new_user_data
        })
        
        try:
            db_user = await supabase.create_user(new_user_data)
            log_auth_event("create_db_user_success", {
                "user_id": user_id,
                "db_user": db_user
            })
        except Exception as e:
            # Si falla la creación en la tabla 'usuarios', intentar borrar el usuario de Supabase Auth para consistencia
            error_details = {"error_message": str(e), "error_type": type(e).__name__}
            log_auth_event("create_db_user_error", error_details, error=e)
            
            try:
                # Necesitamos el cliente de servicio para borrar usuarios
                log_auth_event("cleanup_auth_user_start", {"user_id": user_id})
                await supabase.service_client.auth.admin.delete_user(user_id)
                log_auth_event("cleanup_auth_user_success", {"user_id": user_id})
            except Exception as delete_error:
                 # Loggear este error, ya que el estado es inconsistente
                 error_details = {"error_message": str(delete_error), "error_type": type(delete_error).__name__}
                 log_auth_event("cleanup_auth_user_error", error_details, error=delete_error)
                 print(f"Error crítico: No se pudo borrar el usuario {user_id} de Supabase Auth después de fallo en creación en DB: {delete_error}")
            
            error_msg = f"Error al guardar datos del usuario en la base de datos: {str(e)}"
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

        # 4. Procesar código de referido si existe
        if user_data.referral_code:
            # Lógica para procesar el código de referido
            log_auth_event("process_referral_code", {"referral_code": user_data.referral_code})
            pass
        
        # 5. Generar token de acceso (Opcional: podrías requerir verificación de email antes)
        log_auth_event("generate_access_token_start", {"user_id": user_id})
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=60 * 24 * 7)  # 7 días
        )
        log_auth_event("generate_access_token_success", {"user_id": user_id})
        
        # Registrar éxito del proceso completo
        execution_time = time.time() - start_time
        log_auth_event(
            "register_success",
            {
                "execution_time_ms": round(execution_time * 1000, 2),
                "user_id": user_id,
                "email": user_data.email
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": db_user # Devolver el usuario de la DB
        }

    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP ya manejadas
        execution_time = time.time() - start_time
        log_auth_event(
            "register_http_exception",
            {
                "execution_time_ms": round(execution_time * 1000, 2),
                "status_code": http_exc.status_code,
                "detail": http_exc.detail
            }
        )
        raise http_exc
    except Exception as e:
        # Capturar cualquier otro error no esperado
        execution_time = time.time() - start_time
        error_details = {
            "execution_time_ms": round(execution_time * 1000, 2),
            "error_message": str(e),
            "error_type": type(e).__name__
        }
        log_auth_event("register_unexpected_error", error_details, error=e)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error general en el proceso de registro: {str(e)}"
        )

@router.post("/login", response_model=Token, summary="Iniciar sesión")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Inicia sesión en el sistema.
    
    - **username**: Email del usuario
    - **password**: Contraseña del usuario
    """
    # Registrar inicio del proceso de login
    request_info = {
        "client_ip": request.client.host,
        "method": request.method,
        "path": request.url.path,
        "user_agent": request.headers.get("user-agent")
    }
    
    log_auth_event(
        "login_start",
        {
            "request": request_info,
            "email": form_data.username
        }
    )
    
    start_time = time.time()
    supabase = get_supabase_client()
    try:
        # 1. Autenticar usuario en Supabase Auth
        log_auth_event("supabase_auth_signin_start", {"email": form_data.username})
        try:
            auth_response = supabase.client.auth.sign_in_with_password({
                "email": form_data.username,
                "password": form_data.password
            })
            log_auth_event("supabase_auth_signin_success", {
                "user_id": auth_response.user.id if auth_response.user else None,
                "email": form_data.username
            })
        except AuthApiError as e:
             error_details = {"error_message": str(e), "error_type": "AuthApiError"}
             log_auth_event("supabase_auth_signin_error", error_details, error=e)
             
             if "Invalid login credentials" in str(e):
                 error_msg = "Credenciales de inicio de sesión incorrectas."
                 raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_msg,
                    headers={"WWW-Authenticate": "Bearer"},
                )
             elif "Email not confirmed" in str(e):
                 error_msg = "Por favor, verifica tu correo electrónico antes de iniciar sesión."
                 raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_msg,
                    headers={"WWW-Authenticate": "Bearer"},
                )
             else:
                error_msg = f"Error de autenticación: {str(e)}"
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=error_msg,
                    headers={"WWW-Authenticate": "Bearer"},
                )

        if not auth_response.user:
            # Si no hay error pero tampoco usuario (poco probable)
            error_msg = "Error inesperado durante el inicio de sesión."
            log_auth_event("login_error", {"reason": error_msg})
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg,
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 2. Obtener datos del usuario desde la tabla 'usuarios'
        user_id = auth_response.user.id
        log_auth_event("get_db_user_start", {"user_id": user_id})
        user = await supabase.get_user(user_id)
        log_auth_event("get_db_user_complete", {"user_id": user_id, "user_found": user is not None})
        
        if not user:
            # Esto indica una inconsistencia: usuario existe en Auth pero no en la tabla 'usuarios'
            error_msg = "No se encontraron los datos del usuario en nuestra base de datos."
            log_auth_event("login_error", {
                "reason": error_msg,
                "user_id": user_id,
                "inconsistency": "User exists in Auth but not in DB"
            })
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # 3. Verificar si el usuario está activo en nuestra tabla
        if not user.get("is_active", True):
            error_msg = "La cuenta de usuario está inactiva."
            log_auth_event("login_error", {
                "reason": error_msg,
                "user_id": user_id,
                "is_active": False
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 4. Generar token de acceso
        log_auth_event("generate_access_token_start", {"user_id": user_id})
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=60 * 24 * 7)  # 7 días
        )
        log_auth_event("generate_access_token_success", {"user_id": user_id})
        
        # Registrar éxito del proceso completo
        execution_time = time.time() - start_time
        log_auth_event(
            "login_success",
            {
                "execution_time_ms": round(execution_time * 1000, 2),
                "user_id": user_id,
                "email": form_data.username
            }
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    except HTTPException as http_exc:
        execution_time = time.time() - start_time
        log_auth_event(
            "login_http_exception",
            {
                "execution_time_ms": round(execution_time * 1000, 2),
                "status_code": http_exc.status_code,
                "detail": http_exc.detail
            }
        )
        raise http_exc
    except Exception as e:
        execution_time = time.time() - start_time
        error_details = {
            "execution_time_ms": round(execution_time * 1000, 2),
            "error_message": str(e),
            "error_type": type(e).__name__
        }
        log_auth_event("login_unexpected_error", error_details, error=e)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error general en el proceso de inicio de sesión: {str(e)}"
        )

# --- Rutas de OAuth (Google / Facebook) --- 
# (Se mantienen igual por ahora, pero podrían necesitar ajustes similares en manejo de errores)

@router.get("/google", summary="Iniciar autenticación con Google")
async def login_google(request: Request):
    from app.core.config import settings
    redirect_uri = f"{settings.OAUTH_REDIRECT_URL}/google"
    auth_url = f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={settings.GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&scope=email%20profile&access_type=offline"
    return {"auth_url": auth_url}

@router.get("/google/callback", response_model=Token, summary="Callback de autenticación con Google")
async def google_callback(code: str):
    try:
        from app.core.config import settings
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
            supabase = get_supabase_client()
            existing_user = await supabase.get_user_by_email(user_info["email"])
            
            if existing_user:
                user_id = existing_user["id"]
                user = existing_user
            else:
                # Crear nuevo usuario via OAuth
                try:
                    auth_response = supabase.client.auth.sign_up({
                        "email": user_info["email"],
                        "password": None, # No password needed for OAuth
                        "options": {
                            "data": {
                                "name": user_info.get("name", ""),
                                "avatar_url": user_info.get("picture", "")
                            }
                        }
                    })
                    if not auth_response.user:
                         raise HTTPException(status_code=500, detail="Error inesperado al crear usuario OAuth en Supabase Auth")
                    user_id = auth_response.user.id
                except AuthApiError as e:
                     # Handle potential errors like email already exists (maybe link accounts?)
                     raise HTTPException(status_code=400, detail=f"Error al registrar usuario OAuth: {e}")
                
                # Crear en tabla 'usuarios'
                new_user_data = {
                    "id": user_id,
                    "email": user_info["email"],
                    "name": user_info.get("name", ""),
                    "plan": "free",
                    "creditos": 100,
                    "modulos_activos": ["openai", "whatsapp_basic"],
                    "is_active": True,
                    "avatar_url": user_info.get("picture", "")
                }
                try:
                    user = await supabase.create_user(new_user_data)
                except Exception as e:
                    # Attempt to clean up Auth user if DB insert fails
                    try:
                        await supabase.service_client.auth.admin.delete_user(user_id)
                    except Exception as delete_error:
                        print(f"Error crítico al limpiar usuario OAuth {user_id}: {delete_error}")
                    raise HTTPException(status_code=500, detail=f"Error al guardar usuario OAuth en DB: {e}")

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
            
            access_token = create_access_token(
                data={"sub": user_id},
                expires_delta=timedelta(minutes=60 * 24 * 7)
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": user
            }
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error general en callback de Google: {str(e)}"
        )

@router.get("/facebook", summary="Iniciar autenticación con Facebook")
async def login_facebook(request: Request):
    from app.core.config import settings
    redirect_uri = f"{settings.OAUTH_REDIRECT_URL}/facebook"
    auth_url = f"https://www.facebook.com/v12.0/dialog/oauth?client_id={settings.FACEBOOK_CLIENT_ID}&redirect_uri={redirect_uri}&scope=email,public_profile"
    return {"auth_url": auth_url}

@router.get("/facebook/callback", response_model=Token, summary="Callback de autenticación con Facebook")
async def facebook_callback(code: str):
    # Placeholder - Implementación similar a Google callback necesaria
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Autenticación con Facebook no implementada aún"
    )
