#!/usr/bin/env python3
"""
Script de prueba para comparar los headers y formato de correo entre el método directo y el automatizado.
Este script simula ambos métodos de envío y captura los headers generados para comparación.
"""

import os
import json
import asyncio
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración SMTP de Brevo
SMTP_CONFIG = {
    "host": "smtp-relay.brevo.com",
    "port": 587,
    "username": "8a2c1a001@smtp-brevo.com",
    "password": "f0h8ELCZnH32sWcFmaestra",
    "use_tls": True
}

# Dirección de correo para pruebas
TEST_EMAIL = "geniaecosystem@gmail.com"  # Reemplazar con tu dirección de correo para pruebas

async def test_direct_method():
    """Simula el método directo de envío de correo (como en main_server.py)"""
    logger.info("Probando método directo de envío...")
    
    # Crear mensaje MIME
    msg = MIMEMultipart("alternative")
    from_name = "GENIA Systems"
    from_address = "noreply_whatsapp@genia.systems"
    msg["From"] = f"{from_name} <{from_address}>"
    msg["To"] = TEST_EMAIL
    msg["Subject"] = "Prueba de Método Directo - GENIA"
    
    # Contenido del correo
    text_content = "Este es un correo de prueba enviado usando el método directo."
    html_content = "<h1>Prueba de Método Directo</h1><p>Este es un correo de prueba enviado usando el método directo.</p>"
    
    msg.attach(MIMEText(text_content, "plain"))
    msg.attach(MIMEText(html_content, "html"))
    
    # Guardar los headers para comparación
    headers_direct = {}
    for key, value in msg.items():
        headers_direct[key] = value
    
    logger.info(f"Headers del método directo: {headers_direct}")
    
    # Enviar correo
    try:
        server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"])
        server.set_debuglevel(1)  # Para ver la conversación SMTP
        
        if SMTP_CONFIG["use_tls"]:
            logger.info("Ejecutando STARTTLS...")
            server.starttls()
        
        logger.info(f"Autenticando con usuario: {SMTP_CONFIG['username']}")
        server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
        
        logger.info("Enviando correo (método directo)...")
        server.sendmail(from_address, [TEST_EMAIL], msg.as_string())
        server.quit()
        logger.info("Correo enviado exitosamente (método directo).")
        return headers_direct
    except Exception as e:
        logger.error(f"Error al enviar correo (método directo): {e}")
        return headers_direct

async def test_automated_method():
    """Simula el método automatizado de envío de correo (como en task_executor.py con las mejoras)"""
    logger.info("Probando método automatizado de envío...")
    
    # Simular la construcción del payload como en task_executor.py (con las mejoras)
    result_text = "Este es un contenido de prueba generado por GENIA."
    email_subject = "Prueba de Método Automatizado - GENIA"
    
    formatted_email_body_content = result_text.replace('\n', '<br>')
    email_html_body = f"<h1>{email_subject}</h1><p>{formatted_email_body_content}</p><p><br>---<br>Este correo fue generado y programado por GENIA a través de una solicitud de WhatsApp.</p>"
    
    # MEJORA: Añadir headers adicionales para mejorar la entregabilidad
    email_headers = {
        "X-Priority": "1",
        "X-MSMail-Priority": "High",
        "Importance": "High"
    }
    
    email_content_details = {
        "to_recipients": [
            {"email": TEST_EMAIL, "name": TEST_EMAIL}
        ],
        "subject": email_subject,
        "body_html": email_html_body,
        "from_address": "noreply_whatsapp@genia.systems",
        "from_name": "GENIA Systems",  # MEJORA: Añadir nombre de remitente reconocible
        "headers": email_headers  # MEJORA: Incluir los headers adicionales
    }
    
    # Simular la construcción del mensaje MIME como lo haría el MCP de correo
    msg = MIMEMultipart("alternative")
    
    # Aplicar From con nombre si está disponible
    if email_content_details.get("from_name"):
        msg["From"] = f"{email_content_details['from_name']} <{email_content_details['from_address']}>"
    else:
        msg["From"] = email_content_details["from_address"]
    
    # Destinatarios
    recipient_emails = [r["email"] for r in email_content_details["to_recipients"]]
    msg["To"] = ", ".join(recipient_emails)
    
    # Asunto
    msg["Subject"] = email_content_details["subject"]
    
    # Añadir headers personalizados
    if email_content_details.get("headers"):
        for header_name, header_value in email_content_details["headers"].items():
            msg[header_name] = header_value
    
    # Añadir contenido
    if email_content_details.get("body_html"):
        msg.attach(MIMEText(email_content_details["body_html"], "html"))
    
    # Guardar los headers para comparación
    headers_automated = {}
    for key, value in msg.items():
        headers_automated[key] = value
    
    logger.info(f"Headers del método automatizado: {headers_automated}")
    
    # Enviar correo
    try:
        server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"])
        server.set_debuglevel(1)  # Para ver la conversación SMTP
        
        if SMTP_CONFIG["use_tls"]:
            logger.info("Ejecutando STARTTLS...")
            server.starttls()
        
        logger.info(f"Autenticando con usuario: {SMTP_CONFIG['username']}")
        server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
        
        logger.info("Enviando correo (método automatizado)...")
        server.sendmail(email_content_details["from_address"], recipient_emails, msg.as_string())
        server.quit()
        logger.info("Correo enviado exitosamente (método automatizado).")
        return headers_automated
    except Exception as e:
        logger.error(f"Error al enviar correo (método automatizado): {e}")
        return headers_automated

async def main():
    """Función principal para ejecutar las pruebas"""
    logger.info("Iniciando pruebas de comparación de métodos de envío de correo...")
    
    # Ejecutar ambos métodos
    headers_direct = await test_direct_method()
    logger.info("Esperando 5 segundos entre envíos...")
    await asyncio.sleep(5)  # Esperar un poco entre envíos
    headers_automated = await test_automated_method()
    
    # Comparar headers
    logger.info("\n\n=== COMPARACIÓN DE HEADERS ===")
    logger.info(f"Headers método directo: {json.dumps(headers_direct, indent=2)}")
    logger.info(f"Headers método automatizado: {json.dumps(headers_automated, indent=2)}")
    
    # Verificar diferencias clave
    diff_keys = set(headers_automated.keys()) - set(headers_direct.keys())
    if diff_keys:
        logger.info(f"Headers adicionales en método automatizado: {diff_keys}")
    
    diff_keys = set(headers_direct.keys()) - set(headers_automated.keys())
    if diff_keys:
        logger.info(f"Headers adicionales en método directo: {diff_keys}")
    
    # Verificar valores diferentes para las mismas claves
    common_keys = set(headers_direct.keys()) & set(headers_automated.keys())
    for key in common_keys:
        if headers_direct[key] != headers_automated[key]:
            logger.info(f"Diferencia en '{key}': Directo='{headers_direct[key]}', Automatizado='{headers_automated[key]}'")
    
    logger.info("\nPruebas completadas. Por favor, verifica tu bandeja de entrada para confirmar la recepción de ambos correos.")
    logger.info("Compara especialmente si uno de los métodos llega a la bandeja principal y el otro a spam.")

if __name__ == "__main__":
    asyncio.run(main())
