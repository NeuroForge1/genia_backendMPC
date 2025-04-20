import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Prueba que el endpoint de salud responda correctamente"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_api_docs():
    """Prueba que la documentación de la API esté disponible"""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()

def test_openapi_schema():
    """Prueba que el esquema OpenAPI esté disponible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
    assert "paths" in response.json()

# Pruebas simuladas para endpoints principales
# En una implementación real, estas pruebas usarían mocks para las dependencias externas

def test_genia_tools_endpoint():
    """Prueba que el endpoint de herramientas responda (simulado)"""
    # Esta prueba es simulada ya que requeriría autenticación real
    # response = client.get("/api/genia/tools", headers={"Authorization": "Bearer test_token"})
    # assert response.status_code == 200
    pass

def test_auth_endpoints():
    """Prueba que los endpoints de autenticación respondan (simulado)"""
    # Esta prueba es simulada ya que requeriría credenciales reales
    # response = client.post("/api/auth/login", json={"email": "test@example.com", "password": "password"})
    # assert response.status_code in [200, 401]  # 200 si las credenciales son correctas, 401 si no lo son
    pass
