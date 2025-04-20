import os
import httpx
from typing import Dict, Any, Optional, List
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

class WebhookIntegrationTool(BaseTool):
    """
    Herramienta para gestionar integraciones mediante webhooks
    """
    def __init__(self):
        super().__init__(
            name="webhook_integration",
            description="Gestión de integraciones mediante webhooks"
        )
        
        # Registrar capacidades
        self.register_capability(
            name="create_webhook",
            description="Crea un nuevo webhook para integraciones",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "target_url": {"type": "string"},
                    "events": {"type": "array", "items": {"type": "string"}},
                    "secret_key": {"type": "string"}
                },
                "required": ["name", "target_url", "events"]
            }
        )
        
        self.register_capability(
            name="trigger_webhook",
            description="Dispara manualmente un webhook con datos personalizados",
            schema={
                "type": "object",
                "properties": {
                    "webhook_id": {"type": "string"},
                    "event": {"type": "string"},
                    "payload": {"type": "object"}
                },
                "required": ["webhook_id", "event", "payload"]
            }
        )
        
        self.register_capability(
            name="list_webhooks",
            description="Lista los webhooks configurados por el usuario",
            schema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["active", "inactive", "all"], "default": "all"}
                }
            }
        )
        
        self.register_capability(
            name="delete_webhook",
            description="Elimina un webhook configurado",
            schema={
                "type": "object",
                "properties": {
                    "webhook_id": {"type": "string"}
                },
                "required": ["webhook_id"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta WebhookIntegration
        """
        if capability == "create_webhook":
            return await self._create_webhook(user_id, params)
        elif capability == "trigger_webhook":
            return await self._trigger_webhook(user_id, params)
        elif capability == "list_webhooks":
            return await self._list_webhooks(user_id, params)
        elif capability == "delete_webhook":
            return await self._delete_webhook(user_id, params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")
    
    async def _create_webhook(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo webhook para integraciones
        """
        try:
            # Generar un ID único para el webhook
            import uuid
            webhook_id = str(uuid.uuid4())
            
            # Generar una clave secreta si no se proporciona
            secret_key = params.get("secret_key")
            if not secret_key:
                import secrets
                secret_key = secrets.token_hex(16)
            
            # Crear el webhook en Supabase
            supabase = get_supabase_client()
            webhook_data = {
                "id": webhook_id,
                "user_id": user_id,
                "name": params["name"],
                "description": params.get("description", ""),
                "target_url": params["target_url"],
                "events": params["events"],
                "secret_key": secret_key,
                "is_active": True,
                "created_at": "now()",
                "updated_at": "now()"
            }
            
            # Insertar en una tabla de webhooks (que debería existir en Supabase)
            response = supabase.client.table("webhooks").insert(webhook_data).execute()
            
            return {
                "status": "success",
                "webhook_id": webhook_id,
                "name": params["name"],
                "target_url": params["target_url"],
                "events": params["events"],
                "secret_key": secret_key
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _trigger_webhook(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispara manualmente un webhook con datos personalizados
        """
        try:
            webhook_id = params["webhook_id"]
            event = params["event"]
            payload = params["payload"]
            
            # Verificar que el webhook pertenece al usuario
            supabase = get_supabase_client()
            response = supabase.client.table("webhooks").select("*").eq("id", webhook_id).eq("user_id", user_id).execute()
            
            if not response.data:
                return {"status": "error", "message": "Webhook no encontrado o no pertenece al usuario"}
            
            webhook = response.data[0]
            
            # Verificar que el webhook está activo
            if not webhook.get("is_active", False):
                return {"status": "error", "message": "El webhook está inactivo"}
            
            # Verificar que el evento está permitido
            if event not in webhook["events"]:
                return {"status": "error", "message": f"El evento '{event}' no está configurado para este webhook"}
            
            # Preparar la firma HMAC para verificación
            import hmac
            import hashlib
            import time
            import json
            
            timestamp = int(time.time())
            payload_str = json.dumps(payload)
            
            # Crear la firma
            signature_message = f"{webhook_id}.{timestamp}.{payload_str}"
            signature = hmac.new(
                webhook["secret_key"].encode(),
                signature_message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Preparar los headers
            headers = {
                "Content-Type": "application/json",
                "X-GENIA-Webhook-ID": webhook_id,
                "X-GENIA-Event": event,
                "X-GENIA-Timestamp": str(timestamp),
                "X-GENIA-Signature": signature
            }
            
            # Enviar la solicitud al webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook["target_url"],
                    headers=headers,
                    json={
                        "event": event,
                        "webhook_id": webhook_id,
                        "timestamp": timestamp,
                        "data": payload
                    },
                    timeout=10.0
                )
            
            # Registrar el intento de webhook
            webhook_log = {
                "webhook_id": webhook_id,
                "event": event,
                "payload": payload,
                "status_code": response.status_code,
                "response": response.text if len(response.text) < 1000 else response.text[:1000] + "...",
                "timestamp": "now()"
            }
            
            supabase.client.table("webhook_logs").insert(webhook_log).execute()
            
            return {
                "status": "success",
                "webhook_id": webhook_id,
                "event": event,
                "target_url": webhook["target_url"],
                "response_status": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        except Exception as e:
            # Registrar el error en los logs
            try:
                webhook_log = {
                    "webhook_id": webhook_id,
                    "event": event,
                    "payload": payload,
                    "status_code": 0,
                    "response": f"Error: {str(e)}",
                    "timestamp": "now()"
                }
                supabase.client.table("webhook_logs").insert(webhook_log).execute()
            except:
                pass
            
            return {"status": "error", "message": str(e)}
    
    async def _list_webhooks(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lista los webhooks configurados por el usuario
        """
        try:
            status = params.get("status", "all")
            
            # Consultar webhooks en Supabase
            supabase = get_supabase_client()
            query = supabase.client.table("webhooks").select("*").eq("user_id", user_id)
            
            if status == "active":
                query = query.eq("is_active", True)
            elif status == "inactive":
                query = query.eq("is_active", False)
            
            response = query.execute()
            
            # Formatear la respuesta
            webhooks = []
            for webhook in response.data:
                webhooks.append({
                    "id": webhook["id"],
                    "name": webhook["name"],
                    "description": webhook.get("description", ""),
                    "target_url": webhook["target_url"],
                    "events": webhook["events"],
                    "is_active": webhook.get("is_active", True),
                    "created_at": webhook.get("created_at", "")
                })
            
            return {
                "status": "success",
                "webhooks": webhooks,
                "count": len(webhooks)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _delete_webhook(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Elimina un webhook configurado
        """
        try:
            webhook_id = params["webhook_id"]
            
            # Verificar que el webhook pertenece al usuario
            supabase = get_supabase_client()
            response = supabase.client.table("webhooks").select("*").eq("id", webhook_id).eq("user_id", user_id).execute()
            
            if not response.data:
                return {"status": "error", "message": "Webhook no encontrado o no pertenece al usuario"}
            
            # Eliminar el webhook
            supabase.client.table("webhooks").delete().eq("id", webhook_id).execute()
            
            return {
                "status": "success",
                "webhook_id": webhook_id,
                "message": "Webhook eliminado correctamente"
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
