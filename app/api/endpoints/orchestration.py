from fastapi import APIRouter, HTTPException
import uuid
import datetime
import json # For logs or debugging if es necesario
import logging

from app.mcp_client.client import mcp_client_instance, SimpleMessage, SimpleTextContent
from app.schemas.orchestration_schemas import GenerateAndScheduleEmailRequest

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate-and-schedule-email",
             summary="Orchestrates content generation with OpenAI and schedules email delivery",
             response_description="Confirmation of orchestration and task scheduling")
async def orchestrate_generate_and_schedule_email(request_data: GenerateAndScheduleEmailRequest):
    """
    Endpoint de orquestación:
    1. Recibe un prompt y detalles del destinatario.
    2. Llama al MCP de OpenAI para generar contenido (ej. un poema).
    3. Llama al MCP de Programación para agendar el envío del contenido generado por correo.
    """
    logger.info(f"Iniciando orquestación: generar y programar email para: {request_data.recipient_email} con prompt: \t'{request_data.prompt[:50]}...\t'")

    # Paso 1: Llamar al MCP de OpenAI para generar contenido
    generated_content_text = "Contenido no generado (error o default)."
    try:
        openai_request_message = SimpleMessage(
            role="user",
            content=SimpleTextContent(text=request_data.prompt),
            metadata={"capability_name": "generate_text", "model": "gpt-3.5-turbo"} # Ajusta el modelo si es necesario
        )
        
        logger.info(f"Enviando solicitud al MCP de OpenAI: {openai_request_message.model_dump_json()}")
        
        async for response_msg in mcp_client_instance.request_mcp_server("openai", openai_request_message):
            if response_msg.role == "assistant" and response_msg.content and response_msg.content.text:
                generated_content_text = response_msg.content.text
                logger.info(f"Contenido generado por OpenAI: \t'{generated_content_text[:100]}...\t'")
                break 
            elif response_msg.role == "error":
                logger.error(f"Error recibido del MCP de OpenAI: {response_msg.content.text}")
                raise HTTPException(status_code=502, detail=f"Error del MCP de OpenAI: {response_msg.content.text}")
        
        if generated_content_text == "Contenido no generado (error o default).":
             logger.error("No se recibió contenido válido del MCP de OpenAI.")
             raise HTTPException(status_code=502, detail="No se recibió contenido válido del MCP de OpenAI.")

    except ConnectionError as ce:
        logger.error(f"Error de conexión con MCP de OpenAI: {ce}")
        raise HTTPException(status_code=503, detail=f"Error de comunicación con el MCP de OpenAI: {str(ce)}")
    except Exception as e:
        logger.exception("Error inesperado durante la llamada al MCP de OpenAI")
        raise HTTPException(status_code=500, detail=f"Error interno al contactar MCP de OpenAI: {str(e)}")

    # Paso 2: Preparar y programar la tarea de envío de correo
    try:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        scheduled_time_dt = now_utc + datetime.timedelta(minutes=2) # Programar para 2 mins en el futuro
        scheduled_at_utc_iso = scheduled_time_dt.isoformat()

        # Corregir el f-string problemático
        formatted_generated_content = generated_content_text.replace('\\n', '<br>')
        email_html_body = f"<h1>{request_data.email_subject}</h1><p>{formatted_generated_content}</p><p><br>---<br>Este correo fue generado y programado por GENIA.</p>"

        email_content_details = {
            "to_recipients": [
                {"email": str(request_data.recipient_email), "name": request_data.recipient_name or str(request_data.recipient_email)}
            ],
            "subject": request_data.email_subject,
            "body_html": email_html_body,
            "from_address": str(request_data.email_from_address) 
        }
        mcp_email_request_body = {
            "role": "user",
            "content": email_content_details,
            "metadata": {"source": "genia_backendMPC_orchestration"}
        }
        
        task_data_to_schedule = {
            "genia_user_id": str(uuid.uuid4()), 
            "platform_identifier": {
                "platform_name": "email",
                "account_id": "orchestrated_email_task"
            },
            "scheduled_at_utc": scheduled_at_utc_iso,
            "task_payload": {
                "mcp_target_endpoint": "/mcp/send_email", 
                "mcp_request_body": mcp_email_request_body,
                "user_platform_tokens": { "service_auth_key": "email_mcp_internal_key_placeholder"}
            },
            "task_type": "orchestrated_email_generation_and_send"
        }

        scheduler_response = await mcp_client_instance.schedule_task(task_data_to_schedule)
        
        return {
            "message": "Orquestación completada: Contenido generado y tarea de email programada.",
            "generated_content_preview": generated_content_text[:200] + "...",
            "scheduled_task_info": task_data_to_schedule,
            "scheduler_mcp_response": scheduler_response
        }

    except ConnectionError as ce:
        logger.error(f"Error de conexión con MCP de Programación durante orquestación: {ce}")
        raise HTTPException(status_code=503, detail=f"Error de comunicación con el MCP de Programación: {str(ce)}")
    except ValueError as ve: 
        logger.error(f"Error de configuración interna para el MCP de Programación: {ve}")
        raise HTTPException(status_code=500, detail=f"Error de configuración interna para el MCP de Programación: {str(ve)}")
    except Exception as e:
        logger.exception("Error inesperado durante la programación de la tarea de email")
        raise HTTPException(status_code=500, detail=f"Error interno al programar la tarea de email: {str(e)}")

