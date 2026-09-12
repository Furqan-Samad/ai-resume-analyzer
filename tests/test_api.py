import os

os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("ACCESS_CODE", "test-code")

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_analyze_rejects_missing_access_code():
    files = {"resume": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")}
    data = {"job_description": "Looking for a Python developer."}
    response = client.post("/api/analyze", files=files, data=data)
    assert response.status_code == 401


def test_analyze_rejects_non_pdf_file():
    files = {"resume": ("resume.txt", b"not a pdf", "text/plain")}
    data = {"job_description": "Looking for a Python developer."}
    headers = {"X-Access-Code": "test-code"}
    response = client.post("/api/analyze", files=files, data=data, headers=headers)
    assert response.status_code == 400


def test_analyze_rejects_wrong_access_code():
    files = {"resume": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")}
    data = {"job_description": "Looking for a Python developer."}
    headers = {"X-Access-Code": "wrong-code"}
    response = client.post("/api/analyze", files=files, data=data, headers=headers)
    assert response.status_code == 401
