import httpx
from typing import Dict, Any, Optional
from app.tools.base_tool import BaseTool
# from app.core.config import settings # settings.DEFAULT_FROM_EMAIL might be useful if defined
# from app.db.supabase_manager import get_supabase_client # No longer needed for Gmail tokens

# Define la URL del servidor MCP de correo electrónico de GENIA
GENIA_EMAIL_SERVICE_URL = "https://genia-mcp-server-email.onrender.com/send-email"
DEFAULT_SENDER_EMAIL_GENIA = "mendezchristhian1@gmail.com" # Remitente por defecto, como se configuró en Render

class GmailTool(BaseTool): # Renombrar la clase podría ser una opción, pero por ahora modificamos la existente
    """
    Herramienta para enviar correos electrónicos a través del servicio de correo GENIA.
    (Anteriormente usaba Gmail directamente)
    """
    def __init__(self):
        super().__init__(
            name="email_tool", # Cambiado de "gmail" para reflejar un uso más genérico
            description="Envío de correos electrónicos a través del servicio de correo GENIA"
        )
        
        self.register_capability(
            name="send_email",
            description="Envía un correo electrónico utilizando el servicio de correo GENIA",
            schema={
                "type": "object",
                "properties": {
                    "to_address": {"type": "string", "description": "Dirección de correo del destinatario."},
                    "subject": {"type": "string", "description": "Asunto del correo."},
                    "body_text": {"type": "string", "description": "Cuerpo del correo en formato texto plano."},
                    "body_html": {"type": "string", "description": "(Opcional) Cuerpo del correo en formato HTML."},
                    "from_address": {"type": "string", "description": "(Opcional) Dirección de correo del remitente. Si no se provee, se usará el remitente por defecto del sistema."}
                },
                "required": ["to_address", "subject", "body_text"]
            }
        )
        
        self.register_capability(
            name="send_bulk_email",
            description="Envía correos electrónicos a múltiples destinatarios utilizando el servicio de correo GENIA",
            schema={
                "type": "object",
                "properties": {
                    "to_list": {"type": "array", "items": {"type": "string"}, "description": "Lista de direcciones de correo de los destinatarios."},
                    "subject": {"type": "string", "description": "Asunto del correo."},
                    "body_text": {"type": "string", "description": "Cuerpo del correo en formato texto plano."},
                    "body_html": {"type": "string", "description": "(Opcional) Cuerpo del correo en formato HTML."},
                    "from_address": {"type": "string", "description": "(Opcional) Dirección de correo del remitente. Si no se provee, se usará el remitente por defecto del sistema."}
                },
                "required": ["to_list", "subject", "body_text"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta de correo GENIA
        """
        # user_id ya no es estrictamente necesario para la lógica de envío aquí, 
        # ya que no obtenemos tokens específicos del usuario para el envío.
        # Podría usarse para logging o si el remitente dependiera del usuario.
        if capability == "send_email":
            return await self._send_email(params) # user_id eliminado como argumento directo
        elif capability == "send_bulk_email":
            return await self._send_bulk_email(params) # user_id eliminado como argumento directo
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")
    
    # _get_gmail_tokens ya no es necesario y se elimina.

    async def _send_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un correo electrónico utilizando el servicio de correo GENIA.
        """
        try:
            payload = {
                "from_address": params.get("from_address", DEFAULT_SENDER_EMAIL_GENIA),
                "to_address": params["to_address"],
                "subject": params["subject"],
                "body_text": params["body_text"],
            }
            if "body_html" in params and params["body_html"]:
                payload["body_html"] = params["body_html"]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(GENIA_EMAIL_SERVICE_URL, json=payload)
                
                response.raise_for_status() # Lanza una excepción para códigos de estado HTTP 4xx/5xx
                
                result = response.json()
                
                # Asumimos que el servidor MCP devuelve un JSON con "status" y "message" o "message_id"
                return {
                    "status": result.get("status", "success"), # Asumir éxito si el status no está, pero el MCP debería enviarlo
                    "message": result.get("message", "Correo enviado exitosamente."),
                    "message_id": result.get("message_id"),
                    "to": params["to_address"]
                }

        except httpx.HTTPStatusError as e:
            # Intentar obtener más detalles del error desde la respuesta del servidor MCP
            error_detail = "Error desconocido del servidor de correo."
            try:
                error_response = e.response.json()
                error_detail = error_response.get("detail", error_response.get("message", str(e)))
            except Exception:
                error_detail = e.response.text or str(e)
            return {"status": "error", "message": f"Error al enviar el correo ({e.response.status_code}): {error_detail}"}
        except Exception as e:
            return {"status": "error", "message": f"Error inesperado al enviar el correo: {str(e)}"}
    
    async def _send_bulk_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía correos electrónicos a múltiples destinatarios utilizando el servicio de correo GENIA.
        """
        results = []
        errors = []
        
        for to_email_address in params["to_list"]:
            single_params = {
                "from_address": params.get("from_address", DEFAULT_SENDER_EMAIL_GENIA),
                "to_address": to_email_address,
                "subject": params["subject"],
                "body_text": params["body_text"],
            }
            if "body_html" in params and params["body_html"]:
                single_params["body_html"] = params["body_html"]
            
            result = await self._send_email(single_params)
            
            if result.get("status") == "success":
                results.append({"email": to_email_address, "status": "success", "message_id": result.get("message_id")})
            else:
                errors.append({"email": to_email_address, "error": result.get("message")})
        
        return {
            "status": "success" if not errors else "partial_failure",
            "total_sent": len(results),
            "total_failed": len(errors),
            "results": results,
            "errors": errors
        }

