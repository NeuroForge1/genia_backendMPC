from typing import Dict, Any, List
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client
# import openai # Removed direct OpenAI import

# Import the simplified MCP client instance and message structure
from app.mcp_client.client import mcp_client_instance, SimpleMessage, SimpleTextContent

class FunnelsTool(BaseTool):
    """
    Herramienta para crear y gestionar embudos de ventas
    """
    def __init__(self):
        super().__init__(
            name="funnels",
            description="Creación y gestión de embudos de ventas"
        )
        
        # Removed direct OpenAI client configuration
        # openai.api_key = settings.OPENAI_API_KEY
        
        # Registrar capacidades (schemas remain the same)
        self.register_capability(
            name="create_sales_funnel",
            description="Crea un embudo de ventas completo (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "product_description": {"type": "string"},
                    "target_audience": {"type": "string"},
                    "price_point": {"type": "number"},
                    "funnel_stages": {"type": "integer", "default": 3},
                    "include_upsells": {"type": "boolean", "default": True}
                },
                "required": ["product_name", "target_audience"]
            }
        )
        
        self.register_capability(
            name="generate_landing_page",
            description="Genera contenido para una landing page (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "product_description": {"type": "string"},
                    "target_audience": {"type": "string"},
                    "main_benefit": {"type": "string"},
                    "include_testimonials": {"type": "boolean", "default": True},
                    "cta_text": {"type": "string", "default": "¡Compra ahora!"}
                },
                "required": ["product_name", "main_benefit"]
            }
        )
        
        self.register_capability(
            name="create_email_sequence",
            description="Crea una secuencia de emails para un embudo de ventas (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "sequence_goal": {"type": "string", "enum": ["nurture", "launch", "abandoned_cart", "onboarding"]},
                    "number_of_emails": {"type": "integer", "default": 5},
                    "include_subject_lines": {"type": "boolean", "default": True}
                },
                "required": ["product_name", "sequence_goal"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta Funnels
        """
        if capability == "create_sales_funnel":
            return await self._create_sales_funnel_mcp(params)
        elif capability == "generate_landing_page":
            return await self._generate_landing_page_mcp(params)
        elif capability == "create_email_sequence":
            return await self._create_email_sequence_mcp(params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")

    async def _call_mcp_openai(self, prompt: str, system_message: str = "Eres un asistente útil.", model: str = "gpt-4", max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Helper function to call OpenAI via MCP client."""
        mcp_message = SimpleMessage(
            role="user",
            content=SimpleTextContent(text=prompt),
            metadata={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system_message": system_message # Pass system message via metadata if server supports it
            }
        )
        
        response_text = None
        async for response_msg in mcp_client_instance.request_mcp_server("openai", mcp_message):
            if response_msg.role == "assistant" and isinstance(response_msg.content, SimpleTextContent):
                response_text = response_msg.content.text
                break # Stop after getting the first valid message
            elif response_msg.role == "error":
                raise ConnectionError(f"Error recibido del servidor MCP: {response_msg.content.text}")
        
        if response_text is None:
            raise ConnectionError("No se recibió una respuesta válida del servidor MCP de OpenAI.")
            
        return response_text

    async def _create_sales_funnel_mcp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un embudo de ventas completo usando MCP
        """
        try:
            product_name = params["product_name"]
            product_description = params.get("product_description", "")
            target_audience = params["target_audience"]
            price_point = params.get("price_point", 0)
            funnel_stages = params.get("funnel_stages", 3)
            include_upsells = params.get("include_upsells", True)
            
            prompt = f"""
            Crea un embudo de ventas completo para el producto: {product_name}.
            
            Descripción del producto: {product_description}
            Audiencia objetivo: {target_audience}
            Punto de precio: ${price_point}
            Número de etapas: {funnel_stages}
            {	'Incluir upsells/cross-sells' if include_upsells else 'Sin upsells/cross-sells'}
            
            Para cada etapa del embudo, proporciona:
            1. Nombre de la etapa
            2. Objetivo principal
            3. Contenido recomendado
            4. Canales de distribución
            5. Métricas clave a monitorear
            6. Llamada a la acción (CTA)
            
            Además, incluye:
            - Estrategia general del embudo
            - Puntos de fricción potenciales y cómo resolverlos
            - Recomendaciones para optimización
            
            Formatea la respuesta de manera estructurada y clara.
            """
            
            # Generar el embudo con OpenAI via MCP
            funnel_content = await self._call_mcp_openai(
                prompt=prompt,
                system_message="Eres un experto en marketing digital y embudos de ventas con años de experiencia en optimización de conversión.",
                max_tokens=2500
            )
            
            # Generar un diagrama de flujo del embudo (descripción textual) via MCP
            flow_prompt = f"""
            Crea una descripción detallada de un diagrama de flujo para un embudo de ventas de {funnel_stages} etapas para el producto {product_name} dirigido a {target_audience}.
            
            El diagrama debe mostrar:
            - El flujo de usuarios a través de cada etapa
            - Puntos de decisión clave
            - Rutas alternativas
            {	'- Oportunidades de upsell/cross-sell' if include_upsells else ''}
            
            Describe el diagrama de manera que pueda ser implementado fácilmente por un diseñador.
            """
            
            flow_description = await self._call_mcp_openai(
                prompt=flow_prompt,
                system_message="Eres un experto en diagramas de flujo y visualización de procesos de marketing.",
                max_tokens=1000
            )
            
            return {
                "status": "success",
                "product_name": product_name,
                "funnel_stages": funnel_stages,
                "funnel_content": funnel_content,
                "flow_description": flow_description
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _generate_landing_page_mcp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera contenido para una landing page usando MCP
        """
        try:
            product_name = params["product_name"]
            product_description = params.get("product_description", "")
            target_audience = params.get("target_audience", "")
            main_benefit = params["main_benefit"]
            include_testimonials = params.get("include_testimonials", True)
            cta_text = params.get("cta_text", "¡Compra ahora!")
            
            prompt = f"""
            Genera el contenido completo para una landing page de alto rendimiento para el producto: {product_name}.
            
            Descripción del producto: {product_description}
            Audiencia objetivo: {target_audience}
            Beneficio principal: {main_benefit}
            CTA principal: {cta_text}
            
            La landing page debe incluir:
            
            1. Headline principal (atractivo y centrado en beneficios)
            2. Subheadline de apoyo
            3. Introducción breve
            4. 3-5 características principales con sus beneficios
            5. Sección "Cómo funciona" o proceso
            6. Propuesta de valor única
            7. {	'Sección de testimonios (genera 3 testimonios ficticios pero realistas)' if include_testimonials else ''}
            8. Sección de preguntas frecuentes (5 preguntas con respuestas)
            9. Llamada a la acción principal
            10. Garantía o reducción de riesgo
            
            Formatea el contenido en HTML básico (h1, h2, p, ul, etc.) para facilitar su implementación.
            """
            
            # Generar el contenido con OpenAI via MCP
            landing_content = await self._call_mcp_openai(
                prompt=prompt,
                system_message="Eres un copywriter experto en landing pages de alta conversión.",
                max_tokens=2500
            )
            
            # Generar sugerencias de diseño via MCP
            design_prompt = f"""
            Proporciona 5 recomendaciones específicas de diseño para una landing page de {product_name} dirigida a {target_audience} con el beneficio principal de "{main_benefit}".
            
            Incluye sugerencias sobre:
            - Esquema de colores
            - Imágenes recomendadas
            - Disposición de elementos
            - Elementos de confianza
            - Optimización móvil
            """
            
            design_recommendations = await self._call_mcp_openai(
                prompt=design_prompt,
                system_message="Eres un diseñador web especializado en landing pages de conversión.",
                max_tokens=1000
            )
            
            return {
                "status": "success",
                "product_name": product_name,
                "landing_content": landing_content,
                "design_recommendations": design_recommendations,
                "main_cta": cta_text
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _create_email_sequence_mcp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una secuencia de emails para un embudo de ventas usando MCP
        """
        try:
            product_name = params["product_name"]
            sequence_goal = params["sequence_goal"]
            number_of_emails = params.get("number_of_emails", 5)
            include_subject_lines = params.get("include_subject_lines", True)
            
            goal_descriptions = {
                "nurture": "nutrir leads y construir relación antes de vender",
                "launch": "lanzar un nuevo producto o servicio",
                "abandoned_cart": "recuperar carritos abandonados",
                "onboarding": "dar la bienvenida y capacitar a nuevos clientes"
            }
            
            prompt = f"""
            Crea una secuencia de {number_of_emails} emails para {product_name} con el objetivo de {goal_descriptions[sequence_goal]}.
            
            Para cada email en la secuencia, proporciona:
            1. {f'Asunto del email (atractivo y con alta tasa de apertura)' if include_subject_lines else 'Número y propósito del email'}
            2. Objetivo específico del email
            3. Contenido principal (introducción, cuerpo, conclusión)
            4. Llamada a la acción (CTA)
            5. Tiempo recomendado de envío (días después del email anterior)
            
            Además, incluye:
            - Estrategia general de la secuencia
            - Métricas clave a monitorear
            - Recomendaciones para pruebas A/B
            
            Formatea la respuesta de manera estructurada y clara, separando cada email.
            """
            
            # Generar la secuencia con OpenAI via MCP
            sequence_content = await self._call_mcp_openai(
                prompt=prompt,
                system_message="Eres un experto en email marketing con años de experiencia en secuencias automatizadas.",
                max_tokens=3000
            )
            
            # Extraer los asuntos de los emails si se solicitaron
            subjects = []
            if include_subject_lines:
                import re
                # Attempt to find subjects assuming a pattern like "Asunto: ..." or "Subject: ..."
                subjects = re.findall(r'(?:Asunto|Subject)[:\s]+(.*?)(?:\n|$)', sequence_content, re.IGNORECASE)
            
            return {
                "status": "success",
                "product_name": product_name,
                "sequence_goal": sequence_goal,
                "number_of_emails": number_of_emails,
                "sequence_content": sequence_content,
                "email_subjects": subjects
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

