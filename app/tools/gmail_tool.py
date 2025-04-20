import httpx
from typing import Dict, Any, Optional
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

class GmailTool(BaseTool):
    """
    Herramienta para enviar correos electrónicos a través de Gmail
    """
    def __init__(self):
        super().__init__(
            name="gmail",
            description="Envío de correos electrónicos a través de Gmail"
        )
        
        # Registrar capacidades
        self.register_capability(
            name="send_email",
            description="Envía un correo electrónico",
            schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "html": {"type": "boolean", "default": False}
                },
                "required": ["to", "subject", "body"]
            }
        )
        
        self.register_capability(
            name="send_bulk_email",
            description="Envía correos electrónicos a múltiples destinatarios",
            schema={
                "type": "object",
                "properties": {
                    "to_list": {"type": "array", "items": {"type": "string"}},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                    "html": {"type": "boolean", "default": False}
                },
                "required": ["to_list", "subject", "body"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta Gmail
        """
        if capability == "send_email":
            return await self._send_email(user_id, params)
        elif capability == "send_bulk_email":
            return await self._send_bulk_email(user_id, params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")
    
    async def _get_gmail_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene los tokens de Gmail para el usuario
        """
        supabase = get_supabase_client()
        tokens = await supabase.get_oauth_tokens(user_id, "gmail")
        
        if not tokens:
            raise ValueError("No se encontraron tokens de Gmail para este usuario. Por favor, conecta tu cuenta de Gmail primero.")
        
        # Verificar si el token ha expirado y renovarlo si es necesario
        # (Esta lógica se implementaría aquí)
        
        return tokens
    
    async def _send_email(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía un correo electrónico utilizando la API de Gmail
        """
        try:
            # Obtener tokens de Gmail
            tokens = await self._get_gmail_tokens(user_id)
            access_token = tokens.get("access_token")
            
            # Preparar el mensaje
            message = {
                "to": params["to"],
                "subject": params["subject"],
                "body": params["body"],
                "isHtml": params.get("html", False)
            }
            
            # Enviar el correo utilizando la API de Gmail
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://www.googleapis.com/gmail/v1/users/me/messages/send",
                    headers={"Authorization": f"Bearer {access_token}"},
                    json=message
                )
                
                if response.status_code != 200:
                    raise ValueError(f"Error al enviar el correo: {response.text}")
                
                result = response.json()
                
                return {
                    "status": "success",
                    "message_id": result.get("id"),
                    "to": params["to"]
                }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _send_bulk_email(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envía correos electrónicos a múltiples destinatarios
        """
        try:
            results = []
            errors = []
            
            # Enviar correo a cada destinatario
            for to_email in params["to_list"]:
                single_params = {
                    "to": to_email,
                    "subject": params["subject"],
                    "body": params["body"],
                    "html": params.get("html", False)
                }
                
                result = await self._send_email(user_id, single_params)
                
                if result.get("status") == "success":
                    results.append({"email": to_email, "status": "success", "message_id": result.get("message_id")})
                else:
                    errors.append({"email": to_email, "error": result.get("message")})
            
            return {
                "status": "success",
                "total_sent": len(results),
                "total_failed": len(errors),
                "results": results,
                "errors": errors
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
