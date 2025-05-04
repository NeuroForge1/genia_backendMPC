from pydantic import BaseModel, Field
from typing import Optional, List

class Tool(BaseModel):
    id: str = Field(..., description="Identificador único de la herramienta")
    name: str = Field(..., description="Nombre de la herramienta")
    description: str = Field(..., description="Descripción de la herramienta")
    icon: Optional[str] = Field(default=None, description="Icono representativo (emoji o URL)")
    category: Optional[str] = Field(default=None, description="Categoría a la que pertenece la herramienta")
    endpoint: Optional[str] = Field(default=None, description="Endpoint de la API para usar la herramienta, si aplica")
    # Puedes añadir más campos según sea necesario, como:
    # required_plan: Optional[str] = Field(default=None, description="Plan mínimo requerido para usar la herramienta")
    # input_schema: Optional[dict] = Field(default=None, description="Esquema de los datos de entrada esperados")
    # output_schema: Optional[dict] = Field(default=None, description="Esquema de los datos de salida generados")

