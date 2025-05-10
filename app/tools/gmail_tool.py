import httpx
from typing import Dict, Any, List # Agregado List
from app.tools.base_tool import BaseTool

GENIA_EMAIL_SERVICE_URL = "https://genia-mcp-server-email.onrender.com/mcp/send_email"
DEFAULT_SENDER_EMAIL_GENIA = "mendezchristhian1@gmail.com"
DEFAULT_SENDER_NAME_GENIA = "GENIA Plataforma"

class GmailTool(BaseTool):
    """
    Herramienta para enviar correos electrónicos a través del servicio de correo GENIA.
    """
    def __init__(self):
        super().__init__(
            name="email_tool",
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
                    "from_address": {"type": "string", "description": "(Opcional) Dirección de correo del remitente. Si no se provee, se usará el remitente por defecto del sistema."},
                    "from_name": {"type": "string", "description": "(Opcional) Nombre del remitente. Si no se provee, se usará el nombre por defecto del sistema."}
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
                    "from_address": {"type": "string", "description": "(Opcional) Dirección de correo del remitente. Si no se provee, se usará el remitente por defecto del sistema."},
                    "from_name": {"type": "string", "description": "(Opcional) Nombre del remitente. Si no se provee, se usará el nombre por defecto del sistema."}
                },
                "required": ["to_list", "subject", "body_text"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if capability == "send_email":
            return await self._send_email(params)
        elif capability == "send_bulk_email":
            return await self._send_bulk_email(params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")

    async def _send_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un correo electrónico utilizando el servicio de correo GENIA, 
        ajustando el payload al formato esperado por el servidor MCP de correo.
        """
        try:
            # Construir el objeto 'content' según SendEmailParams del servidor
            email_content = {
                "to_recipients": [{"email": params["to_address"]}], # Convertir to_address a List[EmailRecipient]
                "subject": params["subject"],
                "body_text": params["body_text"]
            }
            if params.get("body_html"):
                email_content["body_html"] = params["body_html"]
            if params.get("from_address"):
                email_content["from_address"] = params["from_address"]
            else:
                email_content["from_address"] = DEFAULT_SENDER_EMAIL_GENIA
            if params.get("from_name"):
                email_content["from_name"] = params["from_name"]
            else:
                email_content["from_name"] = DEFAULT_SENDER_NAME_GENIA

            # Construir el payload completo según EmailRequest del servidor
            request_payload = {
                "role": "user", # O un rol más específico si es necesario
                "content": email_content,
                "metadata": {} # Puede incluirse información adicional si es útil
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(GENIA_EMAIL_SERVICE_URL, json=request_payload)
                response.raise_for_status()
                result = response.json()
                
                return {
                    "status": result.get("status", "success"),
                    "message": result.get("message", "Correo enviado exitosamente."),
                    "message_id": result.get("message_id"), # El servidor de correo no devuelve esto actualmente, pero lo mantenemos por si acaso
                    "to": params["to_address"]
                }

        except httpx.HTTPStatusError as e:
            error_detail = "Error desconocido del servidor de correo."
            try:
                error_response = e.response.json()
                error_detail = error_response.get("detail", {}).get("error", {}).get("msg", str(e)) if isinstance(error_response.get("detail"), dict) else error_response.get("detail", str(e))
                if isinstance(error_detail, list) and error_detail: # Manejar el caso de lista de errores de Pydantic
                    error_detail = error_detail[0].get("msg", str(e)) if isinstance(error_detail[0], dict) else str(error_detail[0])

            except Exception:
                error_detail = e.response.text or str(e)
            return {"status": "error", "message": f"Error al enviar el correo ({e.response.status_code}): {error_detail}"}
        except Exception as e:
            return {"status": "error", "message": f"Error inesperado al enviar el correo: {str(e)}"}
    
    async def _send_bulk_email(self, params: Dict[str, Any]) -> Dict[str, Any]:
        results = []
        errors = []
        
        for to_email_address in params["to_list"]:
            single_params = {
                "to_address": to_email_address,
                "subject": params["subject"],
                "body_text": params["body_text"],
            }
            if params.get("body_html"):
                single_params["body_html"] = params["body_html"]
            if params.get("from_address"):
                single_params["from_address"] = params["from_address"]
            if params.get("from_name"):
                single_params["from_name"] = params["from_name"]
            
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

