from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from app.core.security import create_access_token
from app.db.supabase_manager import get_supabase_client
from pydantic import BaseModel, EmailStr
from datetime import timedelta
import httpx
from supabase.lib.client_options import ClientOptions
from gotrue.errors import AuthApiError

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

@router.post("/register", response_model=Token, summary="Registrar un nuevo usuario")
async def register_user(user_data: UserCreate):
    """
    Registra un nuevo usuario en el sistema.
    
    - **email**: Email del usuario
    - **password**: Contraseña del usuario
    - **name**: Nombre del usuario (opcional)
    - **referral_code**: Código de referido (opcional)
    """
    supabase = get_supabase_client()
    auth_user = None
    db_user = None

    try:
        # 1. Verificar si el usuario ya existe en la tabla 'usuarios'
        existing_db_user = await supabase.get_user_by_email(user_data.email)
        if existing_db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado en nuestra base de datos."
            )

        # 2. Intentar crear usuario en Supabase Auth
        try:
            auth_response = supabase.client.auth.sign_up({
                "email": user_data.email,
                "password": user_data.password,
                "options": {"email_confirm": False} # Desactivar confirmación de email para pruebas
            })
            auth_user = auth_response.user
            if not auth_user:
                 # Si sign_up no devuelve usuario pero tampoco lanza excepción (poco probable pero posible)
                 raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error inesperado durante el registro en Supabase Auth."
                )

        except AuthApiError as e:
            # Capturar errores específicos de Supabase Auth
            if "User already registered" in str(e):
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El email ya está registrado en el sistema de autenticación."
                )
            elif "Unable to validate email address" in str(e):
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El formato del correo electrónico no es válido según Supabase."
                )
            elif "Password should be at least 6 characters" in str(e):
                 raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="La contraseña debe tener al menos 6 caracteres."
                )
            else:
                # Otro error de Supabase Auth
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error de Supabase Auth: {str(e)}"
                )
        except Exception as e:
             # Otros errores inesperados durante sign_up
             raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error inesperado al intentar registrar en Supabase Auth: {str(e)}"
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
        
        try:
            db_user = await supabase.create_user(new_user_data)
        except Exception as e:
            # Si falla la creación en la tabla 'usuarios', intentar borrar el usuario de Supabase Auth para consistencia
            try:
                # Necesitamos el cliente de servicio para borrar usuarios
                await supabase.service_client.auth.admin.delete_user(user_id)
            except Exception as delete_error:
                 # Loggear este error, ya que el estado es inconsistente
                 print(f"Error crítico: No se pudo borrar el usuario {user_id} de Supabase Auth después de fallo en creación en DB: {delete_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al guardar datos del usuario en la base de datos: {str(e)}"
            )

        # 4. Procesar código de referido si existe
        if user_data.referral_code:
            # Lógica para procesar el código de referido
            pass
        
        # 5. Generar token de acceso (Opcional: podrías requerir verificación de email antes)
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=60 * 24 * 7)  # 7 días
        )
        
        # Nota: Supabase por defecto requiere verificación de email. 
        # El usuario no podrá hacer login hasta verificar. Considera informar esto.
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": db_user # Devolver el usuario de la DB
        }

    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP ya manejadas
        raise http_exc
    except Exception as e:
        # Capturar cualquier otro error no esperado
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error general en el proceso de registro: {str(e)}"
        )

@router.post("/login", response_model=Token, summary="Iniciar sesión")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Inicia sesión en el sistema.
    
    - **username**: Email del usuario
    - **password**: Contraseña del usuario
    """
    supabase = get_supabase_client()
    try:
        # 1. Autenticar usuario en Supabase Auth
        try:
            auth_response = supabase.client.auth.sign_in_with_password({
                "email": form_data.username,
                "password": form_data.password
            })
        except AuthApiError as e:
             if "Invalid login credentials" in str(e):
                 raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales de inicio de sesión incorrectas.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
             elif "Email not confirmed" in str(e):
                 raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Por favor, verifica tu correo electrónico antes de iniciar sesión.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
             else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Error de autenticación: {str(e)}",
                    headers={"WWW-Authenticate": "Bearer"},
                )

        if not auth_response.user:
            # Si no hay error pero tampoco usuario (poco probable)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Error inesperado durante el inicio de sesión.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 2. Obtener datos del usuario desde la tabla 'usuarios'
        user_id = auth_response.user.id
        user = await supabase.get_user(user_id)
        
        if not user:
            # Esto indica una inconsistencia: usuario existe en Auth pero no en la tabla 'usuarios'
            # Podrías intentar crearlo aquí o simplemente denegar el acceso
            print(f"Advertencia: Usuario {user_id} existe en Supabase Auth pero no en la tabla 'usuarios'.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontraron los datos del usuario en nuestra base de datos."
            )
        
        # 3. Verificar si el usuario está activo en nuestra tabla
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La cuenta de usuario está inactiva."
            )
        
        # 4. Generar token de acceso
        access_token = create_access_token(
            data={"sub": user_id},
            expires_delta=timedelta(minutes=60 * 24 * 7)  # 7 días
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
        detail="Autenticación con Facebook aún no implementada completamente."
    )

# --- Endpoint para Recuperación de Contraseña --- 

class PasswordRecoveryRequest(BaseModel):
    email: EmailStr

@router.post("/password-recovery", status_code=status.HTTP_200_OK, summary="Solicitar recuperación de contraseña")
async def request_password_recovery(data: PasswordRecoveryRequest):
    """
    Inicia el flujo de recuperación de contraseña para el email proporcionado.
    Supabase enviará un email al usuario con instrucciones.
    """
    supabase = get_supabase_client()
    try:
        # Verificar si el usuario existe (opcional, Supabase puede manejarlo)
        # existing_user = await supabase.get_user_by_email(data.email)
        # if not existing_user:
        #     # Podrías devolver un 200 OK para no revelar si el email existe
        #     return {"message": "Si el correo está registrado, recibirás instrucciones."}
        
        await supabase.client.auth.reset_password_for_email(data.email)
        # Siempre devolver éxito para no revelar si un email está registrado
        return {"message": "Si tu correo electrónico está registrado, recibirás un enlace para restablecer tu contraseña."}
    except AuthApiError as e:
        # Loggear el error pero no exponer detalles al cliente
        print(f"Error en Supabase al solicitar recuperación de contraseña para {data.email}: {e}")
        return {"message": "Si tu correo electrónico está registrado, recibirás un enlace para restablecer tu contraseña."}
    except Exception as e:
        print(f"Error inesperado al solicitar recuperación de contraseña para {data.email}: {e}")
        # Aún así, devolver mensaje genérico
        return {"message": "Si tu correo electrónico está registrado, recibirás un enlace para restablecer tu contraseña."}

# Nota: Falta el endpoint para *actualizar* la contraseña una vez que el usuario sigue el enlace del email.
# Supabase maneja esto redirigiendo a una URL especificada en tu configuración de Supabase,
# donde tu frontend debe capturar el token y permitir al usuario establecer una nueva contraseña.
# Necesitarás una página en el frontend para esto y posiblemente un endpoint en el backend 
# que llame a `supabase.client.auth.update_user` con la nueva contraseña.

