from twilio.rest import Client
from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

class WhatsAppTool(BaseTool):
    """
    Herramienta para enviar y recibir mensajes de WhatsApp usando Twilio
    """
    def __init__(self):
        super().__init__(
            name="whatsapp",
            description="Envío y recepción de mensajes de WhatsApp"
        )
        
        # Registrar capacidades
        self.register_capability(
            name="send_message",
            description="Envía un mensaje de WhatsApp",
            schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "message": {"type": "string"}
                },
                "required": ["to", "message"]
            }
        )
        
        self.register_capability(
            name="send_template",
            description="Envía un mensaje de plantilla de WhatsApp",
            schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "template_name": {"type": "string"},
                    "template_params": {"type": "object"}
                },
                "required": ["to", "template_name"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta WhatsApp
        """
        if capability == "send_message":
            return await self._send_message(user_id, params)
        elif capability == "send_template":
            return await self._send_template(user_id, params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")
    
    async def _send_message(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un mensaje de WhatsApp
        """
        try:
            # Configurar cliente de Twilio
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            # Formatear número de teléfono
            to_number = params["to"]
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            # Enviar mensaje
            message = client.messages.create(
                body=params["message"],
                from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                to=to_number
            )
            
            return {
                "status": "success",
                "message_sid": message.sid,
                "to": params["to"]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _send_template(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un mensaje de plantilla de WhatsApp
        """
        try:
            # Configurar cliente de Twilio
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
            # Formatear número de teléfono
            to_number = params["to"]
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"
            
            # Construir componentes de la plantilla
            components = []
            if "template_params" in params and params["template_params"]:
                for key, value in params["template_params"].items():
                    components.append({"type": "body", "parameters": [{"type": "text", "text": value}]})
            
            # Enviar mensaje de plantilla
            message = client.messages.create(
                content_sid=params["template_name"],
                from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                to=to_number,
                content_variables=components if components else None
            )
            
            return {
                "status": "success",
                "message_sid": message.sid,
                "to": params["to"],
                "template": params["template_name"]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
