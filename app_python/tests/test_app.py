from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_read_root():
    """Test the root endpoint /"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    
    # Check top-level keys
    assert "service" in data
    assert "system" in data
    assert "runtime" in data
    assert "request" in data
    assert "endpoints" in data
    
    # Check service specific values
    assert data["service"]["name"] == "devops-info-service"
    assert data["service"]["framework"] == "FastAPI"

def test_health_check():
    """Test the health check endpoint /health"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)

def test_root_not_found():
    """Test a non-existent endpoint"""
    response = client.get("/non-existent")
    assert response.status_code == 404
