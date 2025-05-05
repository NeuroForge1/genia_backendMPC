import os
import httpx
import json
import re
from typing import Dict, Any, Optional, List
from app.tools.base_tool import BaseTool
from app.core.config import settings
from app.db.supabase_manager import get_supabase_client

# Import the simplified MCP client instance and message structure
from app.mcp_client.client import mcp_client_instance, SimpleMessage, SimpleTextContent

class SEOAnalysisTool(BaseTool):
    """
    Herramienta para análisis y optimización SEO
    """
    def __init__(self):
        super().__init__(
            name="seo_analysis",
            description="Análisis y optimización SEO para contenido web"
        )
        
        # Removed direct OpenAI client configuration
        
        # Registrar capacidades
        self.register_capability(
            name="analyze_content",
            description="Analiza contenido para optimización SEO (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "url": {"type": "string"},
                    "locale": {"type": "string", "default": "es-ES"}
                },
                "required": ["content", "keywords"]
            }
        )
        
        self.register_capability(
            name="generate_meta_tags",
            description="Genera meta tags optimizados para SEO (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "locale": {"type": "string", "default": "es-ES"}
                },
                "required": ["title", "content"]
            }
        )
        
        self.register_capability(
            name="keyword_research",
            description="Realiza investigación de palabras clave (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "locale": {"type": "string", "default": "es-ES"},
                    "max_results": {"type": "integer", "default": 10}
                },
                "required": ["topic"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta SEOAnalysis
        """
        if capability == "analyze_content":
            return await self._analyze_content_mcp(user_id, params)
        elif capability == "generate_meta_tags":
            return await self._generate_meta_tags_mcp(user_id, params)
        elif capability == "keyword_research":
            return await self._keyword_research_mcp(user_id, params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")

    async def _call_mcp_openai(self, prompt: str, system_message: str = "Eres un asistente útil.", model: str = "gpt-4", max_tokens: int = 1500, temperature: float = 0.3) -> str:
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

    async def _analyze_content_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza contenido para optimización SEO usando MCP
        """
        try:
            content = params["content"]
            keywords = params["keywords"]
            url = params.get("url", "")
            locale = params.get("locale", "es-ES")
            
            # Preparar prompt para análisis SEO
            prompt = f"""
            Realiza un análisis SEO completo del siguiente contenido. El contenido está dirigido a la audiencia de habla {locale.split('-')[0]}.
            
            URL: {url if url else 'No especificada'}
            
            Palabras clave objetivo: {', '.join(keywords)}
            
            CONTENIDO:
            {content}
            
            Por favor, proporciona un análisis detallado que incluya:
            1. Puntuación general de SEO (0-100)
            2. Densidad de palabras clave y su uso natural
            3. Estructura del contenido (títulos, subtítulos, párrafos)
            4. Legibilidad y facilidad de lectura
            5. Longitud del contenido
            6. Recomendaciones específicas para mejorar el SEO
            7. Sugerencias para optimizar meta tags
            """
            
            # Utilizar OpenAI via MCP para análisis SEO
            analysis = await self._call_mcp_openai(
                prompt=prompt,
                system_message="Eres un experto en SEO con amplia experiencia en optimización de contenido para motores de búsqueda.",
                max_tokens=1000
            )
            
            # Extraer puntuación SEO via MCP
            score_prompt = f"""
            Basado en este contenido y las palabras clave objetivo {', '.join(keywords)}, asigna una puntuación SEO del 0 al 100.
            Responde solo con el número.
            
            CONTENIDO:
            {content}
            """
            
            score_response_text = await self._call_mcp_openai(
                prompt=score_prompt,
                system_message="Eres un evaluador de SEO preciso que solo responde con números.",
                max_tokens=10,
                temperature=0.1
            )
            
            try:
                # Extract number from response, handling potential non-numeric characters
                score_match = re.search(r'\d+', score_response_text)
                seo_score = int(score_match.group(0)) if score_match else 50
            except:
                seo_score = 50  # Valor por defecto
            
            # Analizar densidad de palabras clave (localmente)
            keyword_density = {}
            word_count = len(content.split())
            
            for keyword in keywords:
                # Contar apariciones (simplificado, en una implementación real sería más sofisticado)
                count = content.lower().count(keyword.lower())
                density = (count / word_count) * 100 if word_count > 0 else 0
                keyword_density[keyword] = {
                    "count": count,
                    "density": round(density, 2)
                }
            
            return {
                "status": "success",
                "seo_score": seo_score,
                "word_count": word_count,
                "keyword_density": keyword_density,
                "analysis": analysis
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _generate_meta_tags_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera meta tags optimizados para SEO usando MCP
        """
        try:
            title = params["title"]
            content = params["content"]
            keywords = params.get("keywords", [])
            locale = params.get("locale", "es-ES")
            
            # Preparar prompt para meta tags
            prompt = f"""
            Genera meta tags optimizados para SEO para el siguiente contenido. El contenido está dirigido a la audiencia de habla {locale.split('-')[0]}.
            
            Título: {title}
            
            Palabras clave objetivo: {', '.join(keywords) if keywords else 'No especificadas'}
            
            CONTENIDO:
            {content[:1000]}... (contenido truncado)
            
            Por favor, genera:
            1. Meta title (máximo 60 caracteres)
            2. Meta description (máximo 160 caracteres)
            3. Meta keywords (si aplica)
            4. Open Graph title, description e image suggestion
            5. Twitter card tags
            """
            
            # Utilizar OpenAI via MCP para generar meta tags
            meta_tags_text = await self._call_mcp_openai(
                prompt=prompt,
                system_message="Eres un experto en SEO especializado en la creación de meta tags optimizados.",
                max_tokens=500
            )
            
            # Generar meta tags estructurados via MCP
            structured_prompt = f"""
            Basado en este contenido, genera meta tags en formato JSON:
            
            Título: {title}
            Contenido: {content[:500]}... (truncado)
            Palabras clave: {', '.join(keywords) if keywords else 'No especificadas'}
            
            Devuelve solo un objeto JSON válido y completo con estas propiedades exactas:
            - meta_title (string, max 60 chars)
            - meta_description (string, max 160 chars)
            - meta_keywords (array de strings)
            - og_title (string)
            - og_description (string)
            - og_image_suggestion (string)
            - twitter_title (string)
            - twitter_description (string)
            """
            
            structured_response_text = await self._call_mcp_openai(
                prompt=structured_prompt,
                system_message="Eres un generador de meta tags que devuelve solo JSON válido.",
                max_tokens=500
            )
            
            # Intentar parsear el JSON
            try:
                # Buscar el objeto JSON en la respuesta
                json_match = re.search(r'\{.*\}', structured_response_text, re.DOTALL)
                if json_match:
                    meta_tags = json.loads(json_match.group(0))
                    # Ensure all keys exist, provide defaults if missing
                    meta_tags.setdefault('meta_title', title[:60])
                    meta_tags.setdefault('meta_description', content[:160])
                    meta_tags.setdefault('meta_keywords', keywords)
                    meta_tags.setdefault('og_title', meta_tags['meta_title'])
                    meta_tags.setdefault('og_description', meta_tags['meta_description'])
                    meta_tags.setdefault('og_image_suggestion', "Imagen relacionada con el contenido")
                    meta_tags.setdefault('twitter_title', meta_tags['meta_title'])
                    meta_tags.setdefault('twitter_description', meta_tags['meta_description'])
                else:
                    raise ValueError("No se encontró un objeto JSON válido")
            except Exception as json_error:
                print(f"Error parsing JSON for meta tags: {json_error}. Using defaults.")
                # Si falla, crear una estructura básica
                meta_tags = {
                    "meta_title": title[:60],
                    "meta_description": content[:160],
                    "meta_keywords": keywords,
                    "og_title": title,
                    "og_description": content[:200],
                    "og_image_suggestion": "Imagen relacionada con el contenido",
                    "twitter_title": title[:60],
                    "twitter_description": content[:200]
                }
            
            # Generar HTML para los meta tags
            html_tags = f"""
            <!-- Meta Tags Básicos -->
            <title>{meta_tags.get('meta_title', '')}</title>
            <meta name="description" content="{meta_tags.get('meta_description', '')}">
            <meta name="keywords" content="{', '.join(meta_tags.get('meta_keywords', []))}">
            
            <!-- Open Graph Tags -->
            <meta property="og:title" content="{meta_tags.get('og_title', '')}">
            <meta property="og:description" content="{meta_tags.get('og_description', '')}">
            <meta property="og:type" content="website">
            <meta property="og:locale" content="{locale}">
            
            <!-- Twitter Card Tags -->
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:title" content="{meta_tags.get('twitter_title', '')}">
            <meta name="twitter:description" content="{meta_tags.get('twitter_description', '')}">
            """
            
            return {
                "status": "success",
                "meta_tags": meta_tags,
                "html_tags": html_tags,
                "analysis": meta_tags_text # Return the raw text analysis as well
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _keyword_research_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza investigación de palabras clave usando MCP
        """
        try:
            topic = params["topic"]
            locale = params.get("locale", "es-ES")
            max_results = params.get("max_results", 10)
            
            # Preparar prompt para investigación de palabras clave
            prompt = f"""
            Realiza una investigación de palabras clave para el tema "{topic}" en el idioma {locale.split('-')[0]}.
            
            Por favor, proporciona:
            1. Lista de las {max_results} palabras clave principales relacionadas con este tema
            2. Para cada palabra clave, estima:
               - Volumen de búsqueda (Alto, Medio, Bajo)
               - Dificultad de competencia (Alta, Media, Baja)
               - Intención de búsqueda (Informacional, Transaccional, Navegacional)
            3. Sugerencias de palabras clave de cola larga
            4. Preguntas comunes que los usuarios buscan sobre este tema
            """
            
            # Utilizar OpenAI via MCP para investigación de palabras clave
            research_text = await self._call_mcp_openai(
                prompt=prompt,
                system_message="Eres un experto en SEO especializado en investigación de palabras clave.",
                max_tokens=1000
            )
            
            # Generar datos estructurados via MCP
            structured_prompt = f"""
            Realiza una investigación de palabras clave para "{topic}" en {locale.split('-')[0]}.
            
            Devuelve solo un objeto JSON válido y completo con estas propiedades exactas:
            1. "main_keywords": array de objetos con propiedades:
               - "keyword": string
               - "volume": string (Alto, Medio, Bajo)
               - "competition": string (Alta, Media, Baja)
               - "intent": string (Informacional, Transaccional, Navegacional)
            
            2. "long_tail_keywords": array de strings
            
            3. "questions": array de strings (preguntas comunes)
            
            Limita a {max_results} palabras clave principales.
            """
            
            structured_response_text = await self._call_mcp_openai(
                prompt=structured_prompt,
                system_message="Eres un investigador de palabras clave que devuelve solo JSON válido.",
                max_tokens=1000
            )
            
            # Intentar parsear el JSON
            try:
                # Buscar el objeto JSON en la respuesta
                json_match = re.search(r'\{.*\}', structured_response_text, re.DOTALL)
                if json_match:
                    keyword_data = json.loads(json_match.group(0))
                    # Ensure keys exist
                    keyword_data.setdefault('main_keywords', [])
                    keyword_data.setdefault('long_tail_keywords', [])
                    keyword_data.setdefault('questions', [])
                else:
                    raise ValueError("No se encontró un objeto JSON válido")
            except Exception as json_error:
                print(f"Error parsing JSON for keyword research: {json_error}. Using defaults.")
                # Si falla, crear una estructura básica
                keyword_data = {
                    "main_keywords": [
                        {"keyword": topic, "volume": "Medio", "competition": "Media", "intent": "Informacional"}
                    ],
                    "long_tail_keywords": [f"mejor {topic}", f"{topic} para principiantes", f"cómo usar {topic}"],
                    "questions": [f"¿Qué es {topic}?", f"¿Cómo funciona {topic}?", f"¿Cuánto cuesta {topic}?"]
                }
            
            return {
                "status": "success",
                "topic": topic,
                "locale": locale,
                "keyword_data": keyword_data,
                "research_text": research_text # Return the raw text analysis as well
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

