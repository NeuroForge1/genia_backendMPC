from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

class TokenData(BaseModel):
    user_id: str
    email: Optional[str] = None

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un token JWT para autenticación
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Verifica el token JWT de Supabase y devuelve el usuario actual.
    """
    print("[DEBUG] get_current_user: Iniciando validación de token") # Log inicio
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"[DEBUG] get_current_user: Token recibido: {token[:10]}...") # Log token recibido
        # Validar el token JWT de Supabase
        # Nota: Usamos la clave secreta JWT de Supabase para la validación
        print("[DEBUG] get_current_user: Intentando decodificar JWT...") # Log antes de decode
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated" # Audiencia estándar para tokens de Supabase
        )
        print("[DEBUG] get_current_user: JWT decodificado exitosamente.") # Log después de decode
        user_id: str = payload.get("sub")
        print(f"[DEBUG] get_current_user: User ID extraído (sub): {user_id}") # Log user_id
        if user_id is None:
            print("[ERROR] get_current_user: User ID (sub) no encontrado en payload.") # Log error sub
            raise credentials_exception
        
        token_data = TokenData(user_id=user_id, email=payload.get("email"))
        print(f"[DEBUG] get_current_user: TokenData creado: {token_data}") # Log token_data
    except JWTError as e:
        print(f"[ERROR] get_current_user: Error JWT: {e}") # Log para depuración JWT
        raise credentials_exception
    except Exception as e:
        print(f"[ERROR] get_current_user: Error inesperado durante validación de token: {e}") # Log para depuración general
        raise credentials_exception
    
    # Obtener el usuario de la base de datos (tabla usuarios)
    print(f"[DEBUG] get_current_user: Intentando obtener detalles de DB para user_id: {token_data.user_id}") # Log antes de DB
    supabase_db = get_supabase_client()
    try:
        user_details = await supabase_db.get_user(token_data.user_id)
        print(f"[DEBUG] get_current_user: Detalles de DB obtenidos: {user_details is not None}") # Log después de DB
        if user_details is None:
            print(f"[ERROR] get_current_user: Detalles de usuario no encontrados en DB para user_id: {token_data.user_id}") # Log error DB
            raise credentials_exception
        
        # Devolver los detalles del usuario de nuestra tabla
        print("[DEBUG] get_current_user: Devolviendo user_details.") # Log éxito
        return user_details 
    except Exception as e:
        print(f"[ERROR] get_current_user: Error al obtener detalles de usuario de DB: {e}") # Log error DB general
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener detalles del usuario"
        )

async def get_current_active_user(current_user = Depends(get_current_user)):
    """
    Verifica que el usuario actual esté activo
    """
    if not current_user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user
