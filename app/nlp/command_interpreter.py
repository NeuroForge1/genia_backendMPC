# /home/ubuntu/genia_backendMPC/app/nlp/command_interpreter.py

import json
from typing import Dict, Any
# Importar la clase MCPClient, no la instancia global
from app.mcp_client.client import MCPClient, SimpleMessage, SimpleTextContent

class CommandInterpreter:
    """Interpreta el texto del usuario para determinar el comando y los parámetros."""

    def __init__(self, mcp_client: MCPClient):
        """Inicializa el intérprete con una instancia del cliente MCP."""
        self.mcp_client = mcp_client
        print("CommandInterpreter inicializado con cliente MCP.")

    async def interpret_command(self, user_text: str) -> Dict[str, Any]:
        """Usa OpenAI (vía MCP) para interpretar el comando del usuario."""
        print(f"CommandInterpreter: Interpretando texto: 	'{user_text}'")

        # TODO: Mejorar el prompt para extraer comando y parámetros de forma estructurada (JSON)
        prompt = f"""
Dada la siguiente solicitud del usuario, identifica el comando principal y cualquier parámetro relevante. Responde SOLO con un objeto JSON con las claves 'command' (string) y 'parameters' (objeto con parámetros específicos del comando).

Comandos posibles y sus parámetros:
- generate_text: {{"topic": "string"}}
- search_keywords: {{"topic": "string"}}
- send_whatsapp: {{"recipient_number": "string", "message_text": "string"}}
- transcribe_audio: (sin parámetros explícitos, se asume que el audio ya está disponible)
- unknown: (si no se reconoce ningún comando)

Solicitud del usuario: "{user_text}"

JSON de respuesta:
"""

        request_message = SimpleMessage(
            role="user",
            content=SimpleTextContent(text=prompt),
            metadata={"model": "gpt-3.5-turbo"} # O el modelo que prefieras
        )

        interpreted_command = {"command": "unknown", "parameters": {}}

        try:
            # Usar la instancia del cliente MCP guardada en self.mcp_client
            async for response in self.mcp_client.request_mcp_server("openai", request_message):
                if response.role == "assistant" and response.content.text:
                    try:
                        # Intenta parsear la respuesta JSON de OpenAI
                        command_data = json.loads(response.content.text.strip())
                        if isinstance(command_data, dict) and 'command' in command_data:
                            interpreted_command = command_data
                            print(f"CommandInterpreter: Comando interpretado: {interpreted_command}")
                        else:
                            print(f"CommandInterpreter: Respuesta de OpenAI no es un JSON válido de comando: {response.content.text}")
                        break # Asumimos que OpenAI da la respuesta completa en un mensaje
                    except json.JSONDecodeError:
                        print(f"CommandInterpreter: Error al decodificar JSON de OpenAI: {response.content.text}")
                        # Mantener comando como 'unknown'
                        break
                elif response.role == "error":
                    print(f"CommandInterpreter: Error recibido del servidor MCP OpenAI: {response.content.text}")
                    break

        except ConnectionError as e:
            print(f"CommandInterpreter: Error de conexión al servidor MCP OpenAI: {e}")
        except Exception as e:
            print(f"CommandInterpreter: Error inesperado al interpretar comando: {e}")

        # Asegurarse de que siempre haya una clave 'parameters' aunque sea vacía
        if "parameters" not in interpreted_command:
             interpreted_command["parameters"] = {}

        return interpreted_command

