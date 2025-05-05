import json
from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

# Import the simplified MCP client instance and message structure
from app.mcp_client.client import mcp_client_instance, SimpleMessage, SimpleTextContent

class StripeTool(BaseTool):
    """
    Herramienta para procesar pagos y gestionar suscripciones con Stripe (vía MCP)
    """
    def __init__(self):
        super().__init__(
            name="stripe",
            description="Procesamiento de pagos y gestión de suscripciones (vía MCP)"
        )
        
        # Removed direct Stripe client configuration
        
        # Registrar capacidades (mantener la misma interfaz externa)
        self.register_capability(
            name="create_payment",
            description="Crea un intento de pago (vía MCP)",
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
            description="Crea una suscripción (vía MCP)",
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
            description="Crea un cliente en Stripe (vía MCP)",
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
        Ejecuta una capacidad de la herramienta Stripe usando MCP
        """
        if capability == "create_payment":
            return await self._create_payment_mcp(user_id, params)
        elif capability == "create_subscription":
            return await self._create_subscription_mcp(user_id, params)
        elif capability == "create_customer":
            return await self._create_customer_mcp(user_id, params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")

    async def _call_mcp_stripe(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Helper function to call Stripe via MCP client."""
        mcp_message = SimpleMessage(
            role="user",
            content=SimpleTextContent(text=f"Execute Stripe capability: {capability}"), # Content text is less relevant here
            metadata={
                "capability": capability,
                "params": params,
                "user_id": user_id # Pass user_id for potential use in server metadata
            }
        )
        
        response_data = None
        async for response_msg in mcp_client_instance.request_mcp_server("stripe", mcp_message):
            if response_msg.role == "assistant" and isinstance(response_msg.content, SimpleTextContent):
                try:
                    # The actual result data is expected as JSON string in the text content
                    response_data = json.loads(response_msg.content.text)
                    break # Stop after getting the first valid message
                except json.JSONDecodeError as json_err:
                     raise ConnectionError(f"Error al decodificar JSON de respuesta del servidor MCP Stripe: {json_err} - Data: {response_msg.content.text}")
            elif response_msg.role == "error" and isinstance(response_msg.content, SimpleTextContent): # Assuming error content is text for now
                raise ConnectionError(f"Error recibido del servidor MCP Stripe: {response_msg.content.text}")
        
        if response_data is None:
            raise ConnectionError("No se recibió una respuesta válida del servidor MCP de Stripe.")
            
        return response_data

    async def _create_payment_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un intento de pago en Stripe via MCP
        """
        try:
            result_data = await self._call_mcp_stripe(user_id, "create_payment", params)
            return {
                "status": "success",
                "client_secret": result_data.get("client_secret"),
                "payment_intent_id": result_data.get("payment_intent_id")
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _create_subscription_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una suscripción en Stripe via MCP
        """
        try:
            result_data = await self._call_mcp_stripe(user_id, "create_subscription", params)
            return {
                "status": "success",
                "subscription_id": result_data.get("subscription_id"),
                "status": result_data.get("status") # Stripe status from server
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _create_customer_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un cliente en Stripe via MCP y actualiza Supabase
        """
        try:
            # Call MCP server to create customer in Stripe
            result_data = await self._call_mcp_stripe(user_id, "create_customer", params)
            customer_id = result_data.get("customer_id")
            
            if not customer_id:
                 raise ValueError("No se recibió customer_id del servidor MCP Stripe")

            # Guardar el ID del cliente en Supabase (esta lógica permanece aquí)
            try:
                supabase = get_supabase_client()
                await supabase.update_user(user_id, {"stripe_customer_id": customer_id})
                print(f"Stripe customer_id {customer_id} guardado en Supabase para user {user_id}")
            except Exception as db_error:
                 # Log the error but potentially continue, as Stripe customer was created
                 print(f"Error al guardar stripe_customer_id en Supabase para user {user_id}: {db_error}")
                 # Consider how critical this update is. Maybe return a partial success?
                 return {
                    "status": "partial_success",
                    "customer_id": customer_id,
                    "message": f"Cliente creado en Stripe ({customer_id}) pero hubo un error al guardar en Supabase: {db_error}"
                 }

            return {
                "status": "success",
                "customer_id": customer_id
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

