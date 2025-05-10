# /home/ubuntu/genia_backendMPC/app/nlp/command_interpreter.py
import json
import logging
from app.mcp_client.client import MCPClient, SimpleMessage, SimpleTextContent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommandInterpreter:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client

    async def interpret_command(self, text: str) -> dict:
        """Interpreta el texto del usuario para identificar un comando principal, una posible acción secundaria de envío de correo y sus parámetros usando el MCP de OpenAI."""
        logger.info(f"CommandInterpreter: Interpretando texto: \t'{text[:50]}...'" )

        prompt = f"""
Dada la siguiente solicitud del usuario, identifica un comando principal y sus parámetros, Y TAMBIÉN una posible acción secundaria de "send_email" con sus parámetros si se menciona explícitamente enviar un correo.
Responde SOLO con un objeto JSON con las siguientes claves:
- "main_command": (string) El comando principal identificado.
- "main_parameters": (object) Parámetros para el comando principal.
- "secondary_action": (string, opcional) Si se detecta una solicitud de envío de correo, debe ser "send_email".
- "secondary_parameters": (object, opcional) Parámetros para la acción secundaria "send_email", que debe incluir "to_address" (string, la dirección de correo del destinatario) y opcionalmente "subject" (string, si el usuario lo especifica).

Comandos principales posibles y sus parámetros:
- generate_text: {{"topic": "string"}}
- search_keywords: {{"topic": "string"}}
- send_whatsapp: {{"recipient_number": "string", "message_text": "string"}}
- unknown: (si no se reconoce ningún comando principal de los anteriores)

Acción secundaria posible y sus parámetros:
- send_email: {{"to_address": "string", "subject": "string"}} (El cuerpo del correo será el resultado del comando principal. El "subject" es opcional y puede ser inferido o genérico si no se especifica).

Ejemplos de interpretación:
1. Solicitud: "Crea un poema sobre la luna y envíalo a juan@example.com"
   Respuesta JSON: {{"main_command": "generate_text", "main_parameters": {{"topic": "poema sobre la luna"}}, "secondary_action": "send_email", "secondary_parameters": {{"to_address": "juan@example.com"}}}}
2. Solicitud: "Resume este artículo y manda el resumen a maria@test.com con asunto 'Resumen del Artículo'"
   Respuesta JSON: {{"main_command": "generate_text", "main_parameters": {{"topic": "resumen de este artículo"}}, "secondary_action": "send_email", "secondary_parameters": {{"to_address": "maria@test.com", "subject": "Resumen del Artículo"}}}}
3. Solicitud: "Busca información sobre el clima actual"
   Respuesta JSON: {{"main_command": "search_keywords", "main_parameters": {{"topic": "clima actual"}}}}
4. Solicitud: "Dime una broma"
   Respuesta JSON: {{"main_command": "generate_text", "main_parameters": {{"topic": "una broma"}}}}

Solicitud del usuario: "{text}"

JSON de respuesta:
"""
        request_message = SimpleMessage(
            role="user",
            content=SimpleTextContent(text=prompt),
            metadata={"model": "gpt-4o"} # Usar un modelo más capaz para esta tarea compleja
        )

        # Default a no reconocer nada o un comando desconocido
        interpreted_result = {
            "main_command": "unknown", 
            "main_parameters": {},
            # No incluimos secondary_action ni secondary_parameters por defecto
        }

        try:
            async for response in self.mcp_client.request_mcp_server("openai", request_message):
                if response.role == "assistant" and response.content.text:
                    try:
                        raw_response_text = response.content.text.strip()
                        logger.info(f"CommandInterpreter: Respuesta cruda de OpenAI: {raw_response_text}")
                        command_data = json.loads(raw_response_text)
                        
                        # Validar y asignar comando principal
                        if "main_command" in command_data and isinstance(command_data["main_command"], str):
                            interpreted_result["main_command"] = command_data["main_command"]
                        if "main_parameters" in command_data and isinstance(command_data["main_parameters"], dict):
                            interpreted_result["main_parameters"] = command_data["main_parameters"]
                        
                        # Validar y asignar acción secundaria si existe
                        if "secondary_action" in command_data and command_data["secondary_action"] == "send_email":
                            interpreted_result["secondary_action"] = "send_email"
                            if "secondary_parameters" in command_data and isinstance(command_data["secondary_parameters"], dict):
                                interpreted_result["secondary_parameters"] = command_data["secondary_parameters"]
                            else:
                                # Si la acción es send_email pero faltan parámetros, es un problema
                                logger.warning("CommandInterpreter: 'send_email' detectado pero faltan 'secondary_parameters' o no es un diccionario.")
                                interpreted_result["secondary_parameters"] = {{}} # Dejarlo vacío para indicar problema

                        logger.info(f"CommandInterpreter: Comando interpretado: {interpreted_result}")
                        break # Got the interpretation
                    except json.JSONDecodeError as json_err:
                        logger.error(f"CommandInterpreter: Error al parsear JSON de OpenAI: {json_err} - Respuesta: {raw_response_text}")
                        interpreted_result["error"] = f"Invalid JSON response from interpreter: {raw_response_text}"
                        break
                elif response.role == "error":
                    error_message = response.content.text
                    logger.error(f"CommandInterpreter: Error recibido del servidor MCP OpenAI: {error_message}")
                    interpreted_result["error"] = f"Interpreter service error: {error_message}"
                    break
            else: # If loop finishes without break (no assistant/error message)
                 logger.warning("CommandInterpreter: No se recibió respuesta válida del servidor MCP OpenAI.")
                 interpreted_result["error"] = "No response from interpreter service."

        except ConnectionError as conn_err:
            logger.error(f"CommandInterpreter: Error de conexión al servidor MCP OpenAI: {conn_err}")
            interpreted_result["error"] = f"Connection error to interpreter service: {conn_err}"
        except Exception as e:
            logger.exception(f"CommandInterpreter: Error inesperado durante la interpretación: {e}")
            interpreted_result["error"] = f"Unexpected error during interpretation: {e}"

        return interpreted_result

