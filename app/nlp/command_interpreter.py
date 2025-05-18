# /home/ubuntu/genia_backendMPC/app/nlp/command_interpreter.py
import json
import logging
import re
from app.mcp_client.client import MCPClient, SimpleMessage, SimpleTextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandInterpreter:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client

    async def interpret_command(self, text: str) -> dict:
        """Interpreta el texto del usuario para identificar un comando y sus parámetros usando el MCP de OpenAI."""
        logger.info(f"CommandInterpreter: Interpretando texto: 	'{text[:50]}...'" )

        # Prompt mejorado: Ahora incluye detección de acciones secundarias como envío de correo
        prompt = f"""
Dada la siguiente solicitud del usuario, identifica el comando principal, sus parámetros, y cualquier acción secundaria solicitada. Responde SOLO con un objeto JSON con las siguientes claves:
- 'command' (string): El comando principal solicitado
- 'parameters' (objeto): Parámetros específicos del comando principal
- 'secondary_action' (string, opcional): Una acción secundaria como enviar el resultado por correo
- 'secondary_parameters' (objeto, opcional): Parámetros para la acción secundaria

Comandos principales posibles:
- generate_text: {{"topic": "string"}}
- search_keywords: {{"topic": "string"}}
- send_whatsapp: {{"recipient_number": "string", "message_text": "string"}}
- unknown: (si no se reconoce ningún comando de los anteriores)

Acciones secundarias posibles:
- send_email: {{"to_address": "string", "subject": "string (opcional)"}}

Ejemplos:
1. "Crea un poema sobre la amistad y envíalo a usuario@ejemplo.com" →
   {{"command": "generate_text", "parameters": {{"topic": "poema sobre la amistad"}}, "secondary_action": "send_email", "secondary_parameters": {{"to_address": "usuario@ejemplo.com"}}}}

2. "Busca palabras clave para marketing digital" →
   {{"command": "search_keywords", "parameters": {{"topic": "marketing digital"}}}}

Solicitud del usuario: "{text}"

JSON de respuesta:
"""
        # Prepare request for MCP OpenAI (assuming default capability is text generation/interpretation)
        request_message = SimpleMessage(
            role="user",
            content=SimpleTextContent(text=prompt),
            metadata={"model": "gpt-4o"} # Usar GPT-4o para mejor interpretación de comandos compuestos
        )

        interpreted_command = {"command": "unknown", "parameters": {}}
        try:
            async for response in self.mcp_client.request_mcp_server("openai", request_message):
                if response.role == "assistant" and response.content.text:
                    try:
                        # Parse the JSON response from OpenAI
                        command_data = json.loads(response.content.text.strip())
                        # Basic validation
                        if "command" in command_data and isinstance(command_data["command"], str):
                             interpreted_command["command"] = command_data["command"]
                        if "parameters" in command_data and isinstance(command_data["parameters"], dict):
                             interpreted_command["parameters"] = command_data["parameters"]
                        # Añadir soporte para acciones secundarias
                        if "secondary_action" in command_data and isinstance(command_data["secondary_action"], str):
                             interpreted_command["secondary_action"] = command_data["secondary_action"]
                        if "secondary_parameters" in command_data and isinstance(command_data["secondary_parameters"], dict):
                             interpreted_command["secondary_parameters"] = command_data["secondary_parameters"]
                        
                        logger.info(f"CommandInterpreter: Comando interpretado: {interpreted_command}")
                        break # Got the interpretation
                    except json.JSONDecodeError as json_err:
                        logger.error(f"CommandInterpreter: Error al parsear JSON de OpenAI: {json_err} - Respuesta: {response.content.text}")
                        interpreted_command["error"] = f"Invalid JSON response from interpreter: {response.content.text}"
                        break
                elif response.role == "error":
                    error_message = response.content.text
                    logger.error(f"CommandInterpreter: Error recibido del servidor MCP OpenAI: {error_message}")
                    interpreted_command["error"] = f"Interpreter service error: {error_message}"
                    break
            else: # If loop finishes without break (no assistant/error message)
                 logger.warning("CommandInterpreter: No se recibió respuesta válida del servidor MCP OpenAI.")
                 interpreted_command["error"] = "No response from interpreter service."

        except ConnectionError as conn_err:
            logger.error(f"CommandInterpreter: Error de conexión al servidor MCP OpenAI: {conn_err}")
            interpreted_command["error"] = f"Connection error to interpreter service: {conn_err}"
        except Exception as e:
            logger.exception(f"CommandInterpreter: Error inesperado durante la interpretación: {e}")
            interpreted_command["error"] = f"Unexpected error during interpretation: {e}"

        # Fallback: Intentar extraer dirección de correo si OpenAI no la detectó
        if "secondary_action" not in interpreted_command:
            email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
            if email_match:
                email = email_match.group(0)
                logger.info(f"CommandInterpreter: Detectada dirección de correo mediante regex: {email}")
                interpreted_command["secondary_action"] = "send_email"
                interpreted_command["secondary_parameters"] = {"to_address": email}

        # Return the dictionary (including potential error key)
        return interpreted_command
