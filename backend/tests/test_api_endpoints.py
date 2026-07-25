import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["service"] == "RecoverAI API"

@pytest.mark.asyncio
async def test_list_patients_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/caregiver/patients")
    assert response.status_code == 200
    patients = response.json()
    assert isinstance(patients, list)

@pytest.mark.asyncio
async def test_upload_patient_profile_endpoint():
    payload = {
        "full_name": "Test Patient",
        "email": "test.patient@example.com",
        "phone_number": "+15550199999",
        "primary_challenge": "Alcohol Recovery",
        "motivation": "Family and health",
        "triggers": "Work stress",
        "coping_strategies": "Walking",
        "personal_background": "Software engineer"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/v1/caregiver/patient", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "patient_id" in data

@pytest.mark.asyncio
async def test_submit_demo_checkin_endpoint():
    payload = {
        "days_ago": 0,
        "journal_text": "Went for a 20 min walk and felt much calmer."
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/v1/recovery/demo-checkin", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["sentiment_label"] == "Positive"

@pytest.mark.asyncio
async def test_get_demo_history_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/recovery/demo-history")
    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)
