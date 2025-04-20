#!/bin/bash

# Script de prueba para el backend de GENIA MCP
# Este script ejecuta pruebas básicas para verificar que el backend funciona correctamente

echo "Iniciando pruebas del backend GENIA MCP..."

# Verificar instalación de dependencias
echo "Verificando dependencias..."
pip install -r requirements.txt

# Ejecutar pruebas unitarias si existen
if [ -d "tests" ]; then
    echo "Ejecutando pruebas unitarias..."
    pytest -xvs
else
    echo "No se encontraron pruebas unitarias."
fi

# Iniciar el servidor en segundo plano para pruebas de API
echo "Iniciando servidor para pruebas de API..."
uvicorn main:app --port 8000 &
SERVER_PID=$!

# Esperar a que el servidor esté listo
echo "Esperando a que el servidor esté listo..."
sleep 5

# Realizar pruebas de API básicas
echo "Realizando pruebas de API..."
curl -s http://localhost:8000/api/health | grep -q "status" && echo "✅ Endpoint de salud funcionando correctamente" || echo "❌ Error en endpoint de salud"

# Verificar documentación de la API
curl -s http://localhost:8000/docs | grep -q "Swagger" && echo "✅ Documentación Swagger disponible" || echo "❌ Error en documentación Swagger"

# Detener el servidor
echo "Deteniendo servidor..."
kill $SERVER_PID

echo "Pruebas completadas."
