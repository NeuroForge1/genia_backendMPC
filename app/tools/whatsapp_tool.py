# /home/ubuntu/genia_backendMPC/app/tools/whatsapp_tool.py
import json
from typing import Dict, Any
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

# Import the simplified MCP client instance and message structure
from app.mcp_client.client import mcp_client_instance, SimpleMessage, SimpleTextContent

class WhatsAppTool(BaseTool):
    """
    Herramienta para enviar mensajes de WhatsApp usando Twilio (vía MCP)
    """
    def __init__(self):
        super().__init__(
            name="whatsapp",
            description="Envío de mensajes de WhatsApp (vía MCP)"
        )
        
        # Registrar capacidades (mantener la misma interfaz externa)
        self.register_capability(
            name="send_message",
            description="Envía un mensaje de WhatsApp (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"}, # Número de destino (ej: +1234567890)
                    "body": {"type": "string"} # Contenido del mensaje
                },
                "required": ["to", "body"]
            }
        )
        
        # Nota: La capacidad send_template no se migrará a MCP por ahora,
        # ya que el servidor MCP de Twilio solo implementa send_whatsapp_message.
        # Si se necesita en el futuro, se deberá ampliar el servidor MCP.
        # self.register_capability(
        #     name="send_template",
        #     description="Envía un mensaje de plantilla de WhatsApp",
        #     schema={...}
        # )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta WhatsApp usando MCP
        """
        if capability == "send_message":
            return await self._send_message_mcp(user_id, params)
        # elif capability == "send_template":
        #     return await self._send_template(user_id, params) # Mantener la lógica original si se necesita
        else:
            raise ValueError(f"Capacidad no soportada por MCP en WhatsAppTool: {capability}")

    async def _call_mcp_twilio(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Helper function to call Twilio via MCP client."""
        mcp_message = SimpleMessage(
            role="user",
            content=SimpleTextContent(text=f"Execute Twilio capability: {capability}"),
            metadata={
                "capability": capability,
                "params": params,
                "user_id": user_id
            }
        )
        
        response_data = None
        async for response_msg in mcp_client_instance.request_mcp_server("twilio", mcp_message):
            if response_msg.role == "assistant" and isinstance(response_msg.content, SimpleTextContent):
                try:
                    response_data = json.loads(response_msg.content.text)
                    break
                except json.JSONDecodeError as json_err:
                     raise ConnectionError(f"Error al decodificar JSON de respuesta del servidor MCP Twilio: {json_err} - Data: {response_msg.content.text}")
            elif response_msg.role == "error" and isinstance(response_msg.content, SimpleTextContent):
                raise ConnectionError(f"Error recibido del servidor MCP Twilio: {response_msg.content.text}")
        
        if response_data is None:
            raise ConnectionError("No se recibió una respuesta válida del servidor MCP de Twilio.")
            
        return response_data

    async def _send_message_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un mensaje de WhatsApp via MCP
        """
        try:
            # Los parámetros 'to' y 'body' se pasan directamente al servidor MCP
            # La validación y el formateo del número (añadir whatsapp:) se hacen en el servidor MCP
            result_data = await self._call_mcp_twilio(user_id, "send_whatsapp_message", params)
            return {
                "status": "success",
                "message_sid": result_data.get("message_sid"),
                "twilio_status": result_data.get("status"), # Status devuelto por Twilio
                "to": params.get("to") # Devolver el número original para referencia
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # --- Lógica Original (Conservada por si se necesita send_template sin MCP) ---
    # async def _send_template(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    #     """
    #     Envía un mensaje de plantilla de WhatsApp (usando cliente Twilio directo)
    #     """
    #     try:
    #         from twilio.rest import Client # Importar aquí si solo se usa en esta función
    #         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            
    #         to_number = params["to"]
    #         if not to_number.startswith("whatsapp:"):
    #             to_number = f"whatsapp:{to_number}"
            
    #         components = []
    #         if "template_params" in params and params["template_params"]:
    #             for key, value in params["template_params"].items():
    #                 components.append({"type": "body", "parameters": [{"type": "text", "text": value}]})
            
    #         message = client.messages.create(
    #             content_sid=params["template_name"],
    #             from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
    #             to=to_number,
    #             content_variables=components if components else None
    #         )
            
    #         return {
    #             "status": "success",
    #             "message_sid": message.sid,
    #             "to": params["to"],
    #             "template": params["template_name"]
    #         }
    #     except Exception as e:
    #         return {"status": "error", "message": str(e)}

