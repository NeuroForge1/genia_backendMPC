from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

class BaseTool(ABC):
    """
    Clase base para todas las herramientas del sistema MCP
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.capabilities = []
    
    def register_capability(self, name: str, description: str, schema: Dict[str, Any]):
        """
        Registra una capacidad de la herramienta
        """
        self.capabilities.append({
            "name": name,
            "description": description,
            "schema": schema
        })
    
    def get_capabilities(self) -> List[Dict[str, Any]]:
        """
        Devuelve las capacidades de la herramienta
        """
        return self.capabilities
    
    @abstractmethod
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta
        """
        pass
