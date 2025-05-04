from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator, EmailStr
from typing import List, Optional, Union, Any
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()

class Settings(BaseSettings):
    # Configuración general
    APP_NAME: str = Field(default="GENIA_MCP", alias="APP_NAME")
    PROJECT_NAME: str = Field(default="GENIA MCP") # Mantenido por si se usa en otro lado
    DEBUG: bool = Field(default=False, alias="DEBUG")
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")
    API_V1_STR: str = "/api/v1"
    
    # Configuración de seguridad
    SECRET_KEY: str = Field(..., alias="SECRET_KEY") # Hacerla requerida
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días
    ALLOWED_HOSTS: List[str] = Field(default=["localhost", "127.0.0.1"], alias="ALLOWED_HOSTS")
    CORS_ALLOWED_ORIGINS: List[str] = Field(default=["http://localhost:5173"], alias="CORS_ALLOWED_ORIGINS")

    # Validadores para convertir strings CSV a listas
    @validator("ALLOWED_HOSTS", "CORS_ALLOWED_ORIGINS", pre=True)
    def _split_str(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v

    # Configuración de Supabase
    SUPABASE_URL: str = Field(..., alias="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(..., alias="SUPABASE_KEY") # Alias para coincidir con .env
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_JWT_SECRET: str = Field(..., alias="SUPABASE_JWT_SECRET")
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str = Field(..., alias="OPENAI_API_KEY")
    OPENAI_ORG_ID: Optional[str] = Field(default=None, alias="OPENAI_ORG_ID")
    
    # Configuración de Stripe
    STRIPE_PUBLIC_KEY: Optional[str] = Field(default=None, alias="STRIPE_PUBLIC_KEY") # Clave pública no siempre necesaria en backend
    STRIPE_SECRET_KEY: str = Field(..., alias="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(..., alias="STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID_BASIC: Optional[str] = Field(default=None, alias="STRIPE_PRICE_ID_BASIC")
    STRIPE_PRICE_ID_PRO: Optional[str] = Field(default=None, alias="STRIPE_PRICE_ID_PRO")
    STRIPE_PRICE_ID_ENTERPRISE: Optional[str] = Field(default=None, alias="STRIPE_PRICE_ID_ENTERPRISE")
    
    # Configuración de Twilio
    TWILIO_ACCOUNT_SID: str = Field(..., alias="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(..., alias="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: Optional[str] = Field(default=None, alias="TWILIO_PHONE_NUMBER") # Alias para coincidir con .env
    
    # Configuración de Sentry
    SENTRY_DSN: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    
    # Configuración de OAuth
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, alias="GOOGLE_CLIENT_SECRET")
    FACEBOOK_CLIENT_ID: Optional[str] = Field(default=None, alias="FACEBOOK_CLIENT_ID")
    FACEBOOK_CLIENT_SECRET: Optional[str] = Field(default=None, alias="FACEBOOK_CLIENT_SECRET")
    OAUTH_REDIRECT_URL: str = Field(default="http://localhost:5173/auth/callback", alias="OAUTH_REDIRECT_URL")

    # Configuración de Gmail (si se usa para SMTP u OAuth)
    GMAIL_CLIENT_ID: Optional[str] = Field(default=None, alias="GMAIL_CLIENT_ID")
    GMAIL_CLIENT_SECRET: Optional[str] = Field(default=None, alias="GMAIL_CLIENT_SECRET")
    GMAIL_REDIRECT_URI: Optional[str] = Field(default=None, alias="GMAIL_REDIRECT_URI")

    # Configuración SMTP (Ejemplo, ajustar según necesidad)
    SMTP_HOST: Optional[str] = Field(default=None, alias="SMTP_HOST")
    SMTP_PORT: Optional[int] = Field(default=None, alias="SMTP_PORT")
    SMTP_USERNAME: Optional[EmailStr] = Field(default=None, alias="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")

    # Pydantic V2 model_config replaces Config class
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore' # Ignorar campos extra en .env que no estén en el modelo
    )

# Instancia de configuración global
settings = Settings()

# Exportar CORS_ORIGINS basado en la configuración cargada
CORS_ORIGINS = settings.CORS_ALLOWED_ORIGINS

