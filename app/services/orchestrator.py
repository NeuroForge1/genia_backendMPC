from typing import Dict, Any, List, Optional
from app.db.supabase_manager import get_supabase_client

class ToolOrchestrator:
    """
    Orquestador central para gestionar las herramientas del sistema MCP
    """
    def __init__(self):
        self.supabase = get_supabase_client()
        self.tools_registry = {}
        self.load_tools()
    
    def load_tools(self):
        """
        Carga todas las herramientas disponibles en el registro
        """
        from app.tools.openai_tool import OpenAITool
        from app.tools.whatsapp_tool import WhatsAppTool
        from app.tools.stripe_tool import StripeTool
        from app.tools.gmail_tool import GmailTool
        from app.tools.funnels_tool import FunnelsTool
        from app.tools.content_tool import ContentTool
        
        # Registrar todas las herramientas disponibles
        self.register_tool("openai", OpenAITool())
        self.register_tool("whatsapp", WhatsAppTool())
        self.register_tool("stripe", StripeTool())
        self.register_tool("gmail", GmailTool())
        self.register_tool("funnels", FunnelsTool())
        self.register_tool("content", ContentTool())
    
    def register_tool(self, name: str, tool_instance: Any):
        """
        Registra una herramienta en el orquestador
        """
        self.tools_registry[name] = tool_instance
    
    async def get_available_tools(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene las herramientas disponibles para un usuario
        """
        # Obtener el usuario y su plan
        user = await self.supabase.get_user(user_id)
        if not user:
            return []
        
        # Obtener herramientas disponibles según el plan
        available_tools = await self.supabase.get_available_tools(user_id)
        
        # Formatear la respuesta para incluir capacidades
        formatted_tools = []
        for tool_data in available_tools:
            tool_name = tool_data.get("nombre")
            if tool_name in self.tools_registry:
                tool_instance = self.tools_registry[tool_name]
                formatted_tools.append({
                    "name": tool_name,
                    "description": tool_data.get("descripcion"),
                    "credit_cost": tool_data.get("coste_creditos"),
                    "capabilities": tool_instance.get_capabilities()
                })
        
        return formatted_tools
    
    async def map_intent_to_tool(self, intent: str) -> Optional[str]:
        """
        Mapea una intención a una herramienta
        """
        intent_map = {
            "enviar_mensaje": "whatsapp",
            "procesar_pago": "stripe",
            "generar_contenido": "content",
            "crear_embudo": "funnels",
            "enviar_email": "gmail",
            "generar_texto": "openai",
            "transcribir_audio": "openai"
        }
        return intent_map.get(intent, "openai")  # Default a OpenAI
    
    async def process_request(self, user_id: str, intent: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud del usuario
        """
        # 1. Verificar permisos del usuario
        user = await self.supabase.get_user(user_id)
        if not user:
            return {"error": "Usuario no encontrado"}
        
        # 2. Determinar la herramienta adecuada para el intent
        tool_name = await self.map_intent_to_tool(intent)
        
        # 3. Verificar si el usuario tiene acceso a esta herramienta
        available_tools = await self.supabase.get_available_tools(user_id)
        if not any(t.get("nombre") == tool_name for t in available_tools):
            return {"error": f"Herramienta {tool_name} no disponible en tu plan"}
        
        # 4. Obtener la herramienta del registro
        if tool_name not in self.tools_registry:
            return {"error": f"Herramienta {tool_name} no encontrada"}
        
        tool = self.tools_registry[tool_name]
        
        # 5. Verificar créditos
        tool_cost = next((t.get("coste_creditos", 0) for t in available_tools if t.get("nombre") == tool_name), 0)
        user_credits = user.get("creditos", 0)
        
        if user_credits < tool_cost:
            return {"error": "Créditos insuficientes"}
        
        # 6. Ejecutar la herramienta
        try:
            capability = params.pop("capability", "default")
            result = await tool.execute(user_id, capability, params)
            
            # 7. Registrar uso y descontar créditos
            await self.supabase.register_task(
                user_id=user_id,
                tool=tool_name,
                capability=capability,
                params=params,
                result=result,
                credits_used=tool_cost
            )
            
            await self.supabase.deduct_credits(user_id, tool_cost)
            
            return {
                "status": "success",
                "tool": tool_name,
                "capability": capability,
                "credits_used": tool_cost,
                "result": result
            }
        except Exception as e:
            # Registrar el error pero no descontar créditos
            return {"error": str(e)}

# Singleton para el orquestador
_orchestrator = None

def get_orchestrator() -> ToolOrchestrator:
    """
    Devuelve una instancia del orquestador de herramientas
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ToolOrchestrator()
    return _orchestrator
