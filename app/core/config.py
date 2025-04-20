from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv
# Cargar variables de entorno desde .env si existe
load_dotenv()

class Settings(BaseSettings):
    # Configuración general
    PROJECT_NAME: str = "GENIA MCP"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Configuración de seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "supersecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días
    
    # Configuración de CORS
    # Permitir configurar CORS_ORIGINS desde variable de entorno o usar valores predeterminados
    CORS_ORIGINS: List[str] = []
    
    @property
    def get_cors_origins(self) -> List[str]:
        cors_origins_env = os.getenv("CORS_ORIGINS", "")
        if cors_origins_env:
            # Si la variable de entorno existe, dividir por comas
            return [origin.strip() for origin in cors_origins_env.split(",")]
        # Si no hay variable de entorno, usar valores predeterminados
        return [
            "http://localhost:3000",
            "http://localhost:5173",
            "https://genia-frontendmpc.vercel.app",
        ]
    
    # Configuración de Supabase
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # Configuración de OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Configuración de Stripe
    STRIPE_PUBLIC_KEY: str = os.getenv("STRIPE_PUBLIC_KEY", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    
    # Configuración de Twilio
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")
    
    # Configuración de Sentry
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", "")
    
    # Configuración de OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    FACEBOOK_CLIENT_ID: str = os.getenv("FACEBOOK_CLIENT_ID", "")
    FACEBOOK_CLIENT_SECRET: str = os.getenv("FACEBOOK_CLIENT_SECRET", "")
    
    # URLs de redirección para OAuth
    OAUTH_REDIRECT_URL: str = os.getenv("OAUTH_REDIRECT_URL", "http://localhost:5173/auth/callback")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Instancia de configuración global
settings = Settings()

# Asignar CORS_ORIGINS usando el método get_cors_origins
settings.CORS_ORIGINS = settings.get_cors_origins
