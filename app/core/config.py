#!/usr/bin/env python3
import os
import json
from typing import List, Optional, Union, Any
from dotenv import load_dotenv
from pydantic import Field, validator, EmailStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Cargar variables de entorno desde .env si existe
load_dotenv()

# --- Manual CORS Parsing (Moved BEFORE Settings class) ---
def parse_cors_origins(origins_str: str) -> List[str]:
    """Parses CORS origins from a string (JSON array or CSV)."""
    if not origins_str:
        return []
    origins_str = origins_str.strip()
    if not origins_str:
        return []
    
    # Try parsing as JSON first
    if origins_str.startswith("[") and origins_str.endswith("]"):
        try:
            parsed = json.loads(origins_str)
            if isinstance(parsed, list):
                # Ensure all items are strings and stripped
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            # If JSON parsing fails, fall through to CSV parsing
            pass # Intentional fall-through
            
    # Fallback to CSV parsing (or if JSON parsing failed)
    return [item.strip() for item in origins_str.split(",") if item.strip()]

# Read raw env var BEFORE Pydantic tries to parse it
CORS_ALLOWED_ORIGINS_RAW = os.getenv("CORS_ALLOWED_ORIGINS", "")
# Parse it using our function
CORS_ORIGINS_LIST = parse_cors_origins(CORS_ALLOWED_ORIGINS_RAW)
# --- End Manual CORS Parsing ---

class Settings(BaseSettings):
    # Configuración general
    APP_NAME: str = Field(default="GENIA_MCP", alias="APP_NAME")
    PROJECT_NAME: str = Field(default="GENIA MCP")
    DEBUG: bool = Field(default=False, alias="DEBUG")
    ENVIRONMENT: str = Field(default="development", alias="ENVIRONMENT")
    API_V1_STR: str = "/api/v1"
    
    # Configuración de seguridad
    SECRET_KEY: str = Field(..., alias="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días
    ALLOWED_HOSTS: Union[str, List[str]] = Field(default="localhost,127.0.0.1", alias="ALLOWED_HOSTS") # Keep as string initially
    # REMOVED CORS_ALLOWED_ORIGINS from here to prevent Pydantic parsing error

    @validator("ALLOWED_HOSTS", pre=True)
    def _split_allowed_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v

    # Configuración de Supabase
    SUPABASE_URL: str = Field(..., alias="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(..., alias="SUPABASE_KEY")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(..., alias="SUPABASE_SERVICE_ROLE_KEY")
    SUPABASE_JWT_SECRET: str = Field(..., alias="SUPABASE_JWT_SECRET")
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str = Field(..., alias="OPENAI_API_KEY")
    OPENAI_ORG_ID: Optional[str] = Field(default=None, alias="OPENAI_ORG_ID")
    
    # Configuración de Stripe
    STRIPE_PUBLIC_KEY: Optional[str] = Field(default=None, alias="STRIPE_PUBLIC_KEY")
    STRIPE_SECRET_KEY: str = Field(..., alias="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: str = Field(..., alias="STRIPE_WEBHOOK_SECRET")
    STRIPE_PRICE_ID_BASIC: Optional[str] = Field(default=None, alias="STRIPE_PRICE_ID_BASIC")
    STRIPE_PRICE_ID_PRO: Optional[str] = Field(default=None, alias="STRIPE_PRICE_ID_PRO")
    STRIPE_PRICE_ID_ENTERPRISE: Optional[str] = Field(default=None, alias="STRIPE_PRICE_ID_ENTERPRISE")
    
    # Configuración de Twilio
    TWILIO_ACCOUNT_SID: str = Field(..., alias="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: str = Field(..., alias="TWILIO_AUTH_TOKEN")
    TWILIO_WHATSAPP_NUMBER: Optional[str] = Field(default=None, alias="TWILIO_PHONE_NUMBER")
    
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

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore' # Corrected quote type
    )

# Instancia de configuración global (Pydantic will now ignore CORS_ALLOWED_ORIGINS)
settings = Settings()

# Ensure ALLOWED_HOSTS is also a list if it was loaded as a string
# This logic remains as it doesn't cause startup errors
if isinstance(settings.ALLOWED_HOSTS, str):
    ALLOWED_HOSTS_LIST = [item.strip() for item in settings.ALLOWED_HOSTS.split(",")]
else:
    ALLOWED_HOSTS_LIST = settings.ALLOWED_HOSTS # Already a list

# Note: CORS_ORIGINS_LIST is now defined at the top from os.getenv
# The old parsing logic after settings instantiation is removed.

