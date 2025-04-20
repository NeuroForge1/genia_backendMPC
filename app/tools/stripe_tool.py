import stripe
from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

class StripeTool(BaseTool):
    """
    Herramienta para procesar pagos y gestionar suscripciones con Stripe
    """
    def __init__(self):
        super().__init__(
            name="stripe",
            description="Procesamiento de pagos y gestión de suscripciones"
        )
        
        # Configurar cliente de Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        # Registrar capacidades
        self.register_capability(
            name="create_payment",
            description="Crea un intento de pago",
            schema={
                "type": "object",
                "properties": {
                    "amount": {"type": "integer"},
                    "currency": {"type": "string", "default": "usd"},
                    "description": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["amount"]
            }
        )
        
        self.register_capability(
            name="create_subscription",
            description="Crea una suscripción",
            schema={
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "price_id": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["customer_id", "price_id"]
            }
        )
        
        self.register_capability(
            name="create_customer",
            description="Crea un cliente en Stripe",
            schema={
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "name": {"type": "string"},
                    "metadata": {"type": "object"}
                },
                "required": ["email"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta Stripe
        """
        if capability == "create_payment":
            return await self._create_payment(user_id, params)
        elif capability == "create_subscription":
            return await self._create_subscription(user_id, params)
        elif capability == "create_customer":
            return await self._create_customer(user_id, params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")
    
    async def _create_payment(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un intento de pago en Stripe
        """
        try:
            # Añadir user_id a los metadatos
            metadata = params.get("metadata", {})
            metadata["user_id"] = user_id
            
            # Crear intento de pago
            payment_intent = stripe.PaymentIntent.create(
                amount=params["amount"],
                currency=params.get("currency", "usd"),
                description=params.get("description", "GENIA Payment"),
                metadata=metadata
            )
            
            return {
                "status": "success",
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _create_subscription(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una suscripción en Stripe
        """
        try:
            # Añadir user_id a los metadatos
            metadata = params.get("metadata", {})
            metadata["user_id"] = user_id
            
            # Crear suscripción
            subscription = stripe.Subscription.create(
                customer=params["customer_id"],
                items=[{"price": params["price_id"]}],
                metadata=metadata
            )
            
            return {
                "status": "success",
                "subscription_id": subscription.id,
                "status": subscription.status
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _create_customer(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un cliente en Stripe
        """
        try:
            # Añadir user_id a los metadatos
            metadata = params.get("metadata", {})
            metadata["user_id"] = user_id
            
            # Crear cliente
            customer = stripe.Customer.create(
                email=params["email"],
                name=params.get("name", ""),
                metadata=metadata
            )
            
            # Guardar el ID del cliente en Supabase
            supabase = get_supabase_client()
            await supabase.update_user(user_id, {"stripe_customer_id": customer.id})
            
            return {
                "status": "success",
                "customer_id": customer.id
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
