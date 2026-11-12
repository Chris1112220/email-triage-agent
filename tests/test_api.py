from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_triage_never_approves():
    r = client.post("/triage", json={"sender": "noreply@shop.com", "subject": "Big sale", "body": "50% off"})
    assert r.status_code == 200
    assert r.json()["approved"] is False  # guardrail holds through the API too
    assert r.json()["draft"] is None  # no drafts to automated senders


def test_triage_rejects_bad_request():
    assert client.post("/triage", json={"subject": "missing sender"}).status_code == 422
