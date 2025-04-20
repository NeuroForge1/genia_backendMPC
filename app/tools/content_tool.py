from typing import Dict, Any, List
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client
import openai

class ContentTool(BaseTool):
    """
    Herramienta para generar contenido optimizado para marketing y comunicación
    """
    def __init__(self):
        super().__init__(
            name="content",
            description="Generación de contenido optimizado para marketing y comunicación"
        )
        
        # Configurar cliente de OpenAI
        openai.api_key = settings.OPENAI_API_KEY
        
        # Registrar capacidades
        self.register_capability(
            name="generate_social_post",
            description="Genera publicaciones para redes sociales",
            schema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "platform": {"type": "string", "enum": ["instagram", "twitter", "facebook", "linkedin"]},
                    "tone": {"type": "string", "enum": ["formal", "casual", "humorous", "inspirational", "educational"]},
                    "include_hashtags": {"type": "boolean", "default": True},
                    "length": {"type": "string", "enum": ["short", "medium", "long"], "default": "medium"}
                },
                "required": ["topic", "platform"]
            }
        )
        
        self.register_capability(
            name="generate_email_campaign",
            description="Genera una campaña de email marketing",
            schema={
                "type": "object",
                "properties": {
                    "product_name": {"type": "string"},
                    "product_description": {"type": "string"},
                    "target_audience": {"type": "string"},
                    "campaign_goal": {"type": "string", "enum": ["awareness", "conversion", "retention"]},
                    "include_cta": {"type": "boolean", "default": True},
                    "cta_text": {"type": "string"}
                },
                "required": ["product_name", "campaign_goal"]
            }
        )
        
        self.register_capability(
            name="generate_blog_post",
            description="Genera un artículo de blog completo",
            schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "tone": {"type": "string", "enum": ["formal", "casual", "technical", "storytelling"]},
                    "word_count": {"type": "integer", "default": 800},
                    "include_seo": {"type": "boolean", "default": True}
                },
                "required": ["title"]
            }
        )
        
        self.register_capability(
            name="analyze_content_sentiment",
            description="Analiza el sentimiento de un texto",
            schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "detailed": {"type": "boolean", "default": False}
                },
                "required": ["text"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta Content
        """
        if capability == "generate_social_post":
            return await self._generate_social_post(params)
        elif capability == "generate_email_campaign":
            return await self._generate_email_campaign(params)
        elif capability == "generate_blog_post":
            return await self._generate_blog_post(params)
        elif capability == "analyze_content_sentiment":
            return await self._analyze_content_sentiment(params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")
    
    async def _generate_social_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera publicaciones para redes sociales
        """
        try:
            # Construir el prompt según la plataforma y tono
            platform = params["platform"]
            tone = params.get("tone", "casual")
            length = params.get("length", "medium")
            include_hashtags = params.get("include_hashtags", True)
            
            length_guide = {
                "short": "no más de 100 caracteres",
                "medium": "entre 100 y 200 caracteres",
                "long": "entre 200 y 280 caracteres"
            }
            
            prompt = f"""
            Genera una publicación para {platform} sobre el tema: {params['topic']}.
            
            Tono: {tone}
            Longitud: {length_guide[length]}
            {f'Incluye hashtags relevantes.' if include_hashtags else 'No incluyas hashtags.'}
            
            La publicación debe ser atractiva, generar engagement y estar optimizada para {platform}.
            """
            
            # Generar el contenido con OpenAI
            response = await openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un experto en marketing de contenidos y redes sociales."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extraer hashtags si están presentes
            hashtags = []
            if include_hashtags:
                import re
                hashtags = re.findall(r'#\w+', content)
            
            return {
                "status": "success",
                "platform": platform,
                "content": content,
                "hashtags": hashtags,
                "character_count": len(content)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _generate_email_campaign(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera una campaña de email marketing
        """
        try:
            product_name = params["product_name"]
            product_description = params.get("product_description", "")
            target_audience = params.get("target_audience", "clientes potenciales")
            campaign_goal = params["campaign_goal"]
            include_cta = params.get("include_cta", True)
            cta_text = params.get("cta_text", "¡Compra ahora!")
            
            goal_guide = {
                "awareness": "dar a conocer el producto y sus beneficios",
                "conversion": "persuadir al lector para que realice una compra",
                "retention": "fidelizar a clientes existentes y fomentar compras recurrentes"
            }
            
            prompt = f"""
            Genera una campaña de email marketing para el producto: {product_name}.
            
            Descripción del producto: {product_description}
            Audiencia objetivo: {target_audience}
            Objetivo de la campaña: {goal_guide[campaign_goal]}
            
            La campaña debe incluir:
            1. Asunto del email (atractivo y con alta tasa de apertura)
            2. Saludo personalizado
            3. Introducción
            4. Cuerpo principal destacando beneficios
            5. {f'Llamada a la acción (CTA): {cta_text}' if include_cta else 'Sin llamada a la acción explícita'}
            6. Despedida
            
            Formatea la respuesta claramente separando cada sección.
            """
            
            # Generar el contenido con OpenAI
            response = await openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un experto en email marketing con alta tasa de conversión."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extraer el asunto del email
            import re
            subject_match = re.search(r'Asunto[:\s]+(.*?)(?:\n|$)', content)
            subject = subject_match.group(1) if subject_match else ""
            
            return {
                "status": "success",
                "campaign_goal": campaign_goal,
                "subject": subject,
                "content": content,
                "word_count": len(content.split())
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _generate_blog_post(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un artículo de blog completo
        """
        try:
            title = params["title"]
            keywords = params.get("keywords", [])
            tone = params.get("tone", "casual")
            word_count = params.get("word_count", 800)
            include_seo = params.get("include_seo", True)
            
            keywords_str = ", ".join(keywords) if keywords else "relevantes al tema"
            
            prompt = f"""
            Genera un artículo de blog completo con el título: "{title}".
            
            Palabras clave: {keywords_str}
            Tono: {tone}
            Extensión aproximada: {word_count} palabras
            
            El artículo debe incluir:
            1. Introducción atractiva
            2. Desarrollo con subtítulos
            3. Conclusión
            4. {f'Optimización SEO para las palabras clave mencionadas' if include_seo else ''}
            
            Estructura el artículo con formato HTML básico (h2, h3, p, ul, etc.).
            """
            
            # Generar el contenido con OpenAI
            response = await openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un redactor profesional especializado en blogs y SEO."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2500,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.strip()
            
            # Generar meta descripción para SEO si se solicita
            meta_description = ""
            if include_seo:
                meta_prompt = f"Genera una meta descripción SEO de 150-160 caracteres para un artículo titulado '{title}' que incluya alguna de estas palabras clave: {keywords_str}."
                
                meta_response = await openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "Eres un experto en SEO."},
                        {"role": "user", "content": meta_prompt}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                
                meta_description = meta_response.choices[0].message.content.strip()
            
            return {
                "status": "success",
                "title": title,
                "content": content,
                "meta_description": meta_description,
                "word_count": len(content.split()),
                "reading_time": round(len(content.split()) / 200)  # Estimación de tiempo de lectura en minutos
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _analyze_content_sentiment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza el sentimiento de un texto
        """
        try:
            text = params["text"]
            detailed = params.get("detailed", False)
            
            prompt = f"""
            Analiza el sentimiento del siguiente texto:
            
            "{text}"
            
            {f'Proporciona un análisis detallado incluyendo emociones detectadas, tono, intención y recomendaciones.' if detailed else 'Proporciona un análisis básico del sentimiento (positivo, negativo o neutral) y su intensidad.'}
            """
            
            # Analizar el sentimiento con OpenAI
            response = await openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de sentimiento y lingüística."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content.strip()
            
            # Determinar el sentimiento general
            sentiment_prompt = f"Basado en este texto: '{text}', clasifica el sentimiento como POSITIVO, NEGATIVO o NEUTRAL. Responde solo con una de estas tres palabras."
            
            sentiment_response = await openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Eres un clasificador de sentimiento preciso."},
                    {"role": "user", "content": sentiment_prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )
            
            sentiment = sentiment_response.choices[0].message.content.strip().upper()
            
            return {
                "status": "success",
                "sentiment": sentiment,
                "analysis": analysis,
                "text_length": len(text)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
