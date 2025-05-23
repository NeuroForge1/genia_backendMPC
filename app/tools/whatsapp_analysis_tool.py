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

class WhatsAppAnalysisTool(BaseTool):
    """
    Herramienta para análisis avanzado de conversaciones de WhatsApp
    """
    def __init__(self):
        super().__init__(
            name="whatsapp_analysis",
            description="Análisis avanzado de conversaciones de WhatsApp"
        )
        
        # Removed direct OpenAI client configuration
        
        # Registrar capacidades
        self.register_capability(
            name="analyze_sentiment",
            description="Analiza el sentimiento de una conversación de WhatsApp (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string"},
                    "time_period": {"type": "string", "enum": ["day", "week", "month", "all"], "default": "week"}
                },
                "required": ["chat_id"]
            }
        )
        
        self.register_capability(
            name="extract_topics",
            description="Extrae los temas principales de una conversación de WhatsApp (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string"},
                    "max_topics": {"type": "integer", "default": 5},
                    "time_period": {"type": "string", "enum": ["day", "week", "month", "all"], "default": "week"}
                },
                "required": ["chat_id"]
            }
        )
        
        self.register_capability(
            name="generate_response_suggestions",
            description="Genera sugerencias de respuesta basadas en el historial de chat (vía MCP)",
            schema={
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string"},
                    "last_message": {"type": "string"},
                    "tone": {"type": "string", "enum": ["formal", "casual", "sales", "support"], "default": "casual"},
                    "num_suggestions": {"type": "integer", "default": 3}
                },
                "required": ["chat_id", "last_message"]
            }
        )
    
    async def execute(self, user_id: str, capability: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta una capacidad de la herramienta WhatsAppAnalysis
        """
        if capability == "analyze_sentiment":
            return await self._analyze_sentiment_mcp(user_id, params)
        elif capability == "extract_topics":
            return await self._extract_topics_mcp(user_id, params)
        elif capability == "generate_response_suggestions":
            return await self._generate_response_suggestions_mcp(user_id, params)
        else:
            raise ValueError(f"Capacidad no soportada: {capability}")

    async def _call_mcp_openai(self, prompt: str, system_message: str = "Eres un asistente útil.", model: str = "gpt-4", max_tokens: int = 500, temperature: float = 0.3) -> str:
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

    async def _get_chat_history(self, user_id: str, chat_id: str, time_period: str) -> list:
        """
        Obtiene el historial de chat de WhatsApp (Simulado)
        """
        # En una implementación real, esto obtendría los mensajes de la API de WhatsApp Business
        # o de una base de datos donde se almacenen.
        # Verificar si el usuario tiene acceso a Twilio (o el proveedor de WhatsApp)
        # supabase = get_supabase_client()
        # twilio_tokens = await supabase.get_oauth_tokens(user_id, "twilio")
        # if not twilio_tokens:
        #     raise ValueError("No se encontraron tokens de Twilio/WhatsApp para este usuario")
        
        print(f"Simulando obtención de historial para chat_id: {chat_id}, user_id: {user_id}, period: {time_period}")
        # Simulación de mensajes para el ejemplo
        messages = [
            {"role": "customer", "content": "Hola, tengo una pregunta sobre el producto X", "timestamp": "2025-04-15T10:30:00Z"},
            {"role": "agent", "content": "¡Hola! Claro, ¿en qué puedo ayudarte con el producto X?", "timestamp": "2025-04-15T10:32:00Z"},
            {"role": "customer", "content": "¿Cuánto tiempo dura la batería?", "timestamp": "2025-04-15T10:33:00Z"},
            {"role": "agent", "content": "La batería del producto X dura aproximadamente 8 horas de uso continuo.", "timestamp": "2025-04-15T10:35:00Z"},
            {"role": "customer", "content": "Excelente, eso es justo lo que necesito. ¿Tienen disponibilidad?", "timestamp": "2025-04-15T10:37:00Z"},
            {"role": "agent", "content": "Sí, tenemos disponibilidad inmediata. ¿Te gustaría proceder con la compra?", "timestamp": "2025-04-15T10:39:00Z"},
            {"role": "customer", "content": "Sí, me gustaría comprarlo. ¿Cuál es el siguiente paso?", "timestamp": "2025-04-15T10:41:00Z"}
        ]
        
        return messages
    
    async def _analyze_sentiment_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analiza el sentimiento de una conversación de WhatsApp usando MCP
        """
        try:
            chat_id = params["chat_id"]
            time_period = params.get("time_period", "week")
            
            # Obtener historial de chat (simulado)
            messages = await self._get_chat_history(user_id, chat_id, time_period)
            
            # Extraer solo los mensajes del cliente
            customer_messages = [msg["content"] for msg in messages if msg["role"] == "customer"]
            
            if not customer_messages:
                return {
                    "status": "error",
                    "message": "No se encontraron mensajes del cliente para analizar"
                }
            
            # Concatenar mensajes para análisis
            text_to_analyze = " ".join(customer_messages)
            
            # Utilizar OpenAI via MCP para análisis de sentimiento
            analysis = await self._call_mcp_openai(
                prompt=text_to_analyze,
                system_message="Eres un experto en análisis de sentimiento. Analiza el siguiente texto de una conversación de WhatsApp y proporciona un análisis detallado del sentimiento del cliente, incluyendo: sentimiento general (positivo, negativo, neutral), nivel de satisfacción (1-10), emociones detectadas, y recomendaciones para mejorar la experiencia del cliente."
            )
            
            # Determinar sentimiento general via MCP
            sentiment_prompt = f"Basado en este texto de una conversación de WhatsApp: '{text_to_analyze}', clasifica el sentimiento como POSITIVO, NEGATIVO o NEUTRAL. Responde solo con una de estas tres palabras."
            sentiment_response_text = await self._call_mcp_openai(
                prompt=sentiment_prompt,
                system_message="Eres un clasificador de sentimiento preciso.",
                max_tokens=10,
                temperature=0.1
            )
            sentiment = sentiment_response_text.strip().upper()
            # Basic validation
            if sentiment not in ["POSITIVO", "NEGATIVO", "NEUTRAL"]:
                sentiment = "NEUTRAL" # Default if classification fails

            # Calcular puntuación de satisfacción via MCP
            satisfaction_prompt = f"Basado en este texto de una conversación de WhatsApp: '{text_to_analyze}', asigna una puntuación de satisfacción del cliente del 1 al 10, donde 1 es extremadamente insatisfecho y 10 es extremadamente satisfecho. Responde solo con el número."
            satisfaction_response_text = await self._call_mcp_openai(
                prompt=satisfaction_prompt,
                system_message="Eres un evaluador preciso de satisfacción del cliente.",
                max_tokens=10,
                temperature=0.1
            )
            
            try:
                # Extract number from response, handling potential non-numeric characters
                score_match = re.search(r'\d+', satisfaction_response_text)
                satisfaction_score = int(score_match.group(0)) if score_match else 5
            except:
                satisfaction_score = 5  # Valor por defecto
            
            return {
                "status": "success",
                "sentiment": sentiment,
                "satisfaction_score": satisfaction_score,
                "analysis": analysis,
                "message_count": len(messages),
                "customer_message_count": len(customer_messages)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _extract_topics_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae los temas principales de una conversación de WhatsApp usando MCP
        """
        try:
            chat_id = params["chat_id"]
            max_topics = params.get("max_topics", 5)
            time_period = params.get("time_period", "week")
            
            # Obtener historial de chat (simulado)
            messages = await self._get_chat_history(user_id, chat_id, time_period)
            
            # Concatenar todos los mensajes
            all_text = " ".join([msg["content"] for msg in messages])
            
            if not all_text:
                return {
                    "status": "error",
                    "message": "No se encontraron mensajes para analizar"
                }
            
            # Utilizar OpenAI via MCP para extracción de temas
            topics_analysis = await self._call_mcp_openai(
                prompt=all_text,
                system_message=f"Eres un experto en análisis de conversaciones. Extrae los {max_topics} temas principales de la siguiente conversación de WhatsApp. Para cada tema, proporciona un título corto y una breve descripción."
            )
            
            # Extraer temas en formato estructurado via MCP
            topics_prompt = f"Basado en esta conversación de WhatsApp: '{all_text}', identifica exactamente {max_topics} temas principales. Responde en formato JSON con un array de objetos, cada uno con 'title' y 'description'."
            topics_response_text = await self._call_mcp_openai(
                prompt=topics_prompt,
                system_message="Eres un extractor de temas que responde en formato JSON válido."
            )
            
            # Intentar parsear el JSON
            try:
                # Buscar el objeto JSON en la respuesta
                json_match = re.search(r'\{.*\}', topics_response_text, re.DOTALL) # Try object first
                if not json_match:
                     json_match = re.search(r'\[.*\]', topics_response_text, re.DOTALL) # Then array
                
                if json_match:
                    # Handle potential wrapping in an object like {"topics": [...]} 
                    parsed_json = json.loads(json_match.group(0))
                    if isinstance(parsed_json, dict) and len(parsed_json) == 1:
                         topics = list(parsed_json.values())[0]
                    else:
                         topics = parsed_json
                    
                    if not isinstance(topics, list):
                         raise ValueError("Parsed JSON is not a list")
                    # Ensure structure
                    for topic in topics:
                         topic.setdefault('title', 'Título no encontrado')
                         topic.setdefault('description', 'Descripción no encontrada')

                else:
                    raise ValueError("No se encontró un objeto o array JSON válido")
            except Exception as json_error:
                print(f"Error parsing JSON for topics: {json_error}. Using defaults.")
                # Si falla el parseo, crear una estructura básica
                topics = [{"title": f"Tema {i+1}", "description": "No se pudo extraer correctamente"} for i in range(max_topics)]
            
            return {
                "status": "success",
                "topics": topics,
                "topics_analysis": topics_analysis,
                "message_count": len(messages)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _generate_response_suggestions_mcp(self, user_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera sugerencias de respuesta basadas en el historial de chat usando MCP
        """
        try:
            chat_id = params["chat_id"]
            last_message = params["last_message"]
            tone = params.get("tone", "casual")
            num_suggestions = params.get("num_suggestions", 3)
            
            # Obtener historial de chat (simulado)
            messages = await self._get_chat_history(user_id, chat_id, "week")
            
            # Preparar contexto para OpenAI
            chat_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages[-5:]])  # Últimos 5 mensajes
            
            # Mapeo de tonos
            tone_descriptions = {
                "formal": "formal y profesional",
                "casual": "casual y amigable",
                "sales": "orientado a ventas y persuasivo",
                "support": "servicial y orientado al soporte técnico"
            }
            
            tone_description = tone_descriptions.get(tone, "casual y amigable")
            
            # Utilizar OpenAI via MCP para generar sugerencias
            suggestions_text = await self._call_mcp_openai(
                prompt=f"Contexto de la conversación:\n{chat_context}\n\nÚltimo mensaje del cliente: {last_message}\n\nGenera {num_suggestions} sugerencias de respuesta:",
                system_message=f"Eres un asistente experto en servicio al cliente. Genera {num_suggestions} sugerencias de respuesta con tono {tone_description} para el último mensaje del cliente en esta conversación de WhatsApp. Las respuestas deben ser concisas, útiles y naturales.",
                temperature=0.7
            )
            
            # Extraer sugerencias en formato estructurado via MCP
            suggestions_prompt = f"Basado en esta conversación de WhatsApp y el último mensaje '{last_message}', genera exactamente {num_suggestions} sugerencias de respuesta con tono {tone_description}. Responde en formato JSON con un array de strings."
            suggestions_response_text = await self._call_mcp_openai(
                prompt=f"Contexto de la conversación:\n{chat_context}\n\nÚltimo mensaje: {last_message}\n\nGenera {num_suggestions} sugerencias en JSON:",
                system_message="Eres un generador de respuestas que devuelve solo un array JSON válido de strings.",
                temperature=0.7
            )
            
            # Intentar parsear el JSON
            try:
                # Buscar corchetes para extraer el JSON
                json_match = re.search(r'\[.*\]', suggestions_response_text, re.DOTALL)
                if json_match:
                    suggestions = json.loads(json_match.group(0))
                    if not isinstance(suggestions, list):
                         raise ValueError("Parsed JSON is not a list")
                    # Ensure correct number of suggestions
                    suggestions = suggestions[:num_suggestions]
                    while len(suggestions) < num_suggestions:
                         suggestions.append("Error al generar sugerencia adicional.")
                else:
                    raise ValueError("No se encontró un array JSON válido")
            except Exception as json_error:
                print(f"Error parsing JSON for suggestions: {json_error}. Extracting manually.")
                # Si falla el parseo, extraer manualmente
                suggestions = []
                for i, line in enumerate(suggestions_text.split("\n")):
                    if i < num_suggestions and line.strip():
                        # Eliminar numeración y caracteres especiales
                        clean_line = re.sub(r'^\[\d+\][\.\)]\s*', '', line).strip()
                        if clean_line:
                            suggestions.append(clean_line)
                
                # Si aún no tenemos suficientes sugerencias
                while len(suggestions) < num_suggestions:
                    suggestions.append(f"Gracias por tu mensaje. ¿En qué más puedo ayudarte?")
            
            return {
                "status": "success",
                "suggestions": suggestions,
                "raw_suggestions_text": suggestions_text # Return raw text as well
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

