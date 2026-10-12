import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app import app

client = TestClient(app)

MOCK_TOKEN = "mock.jwt.token"
MOCK_USER_ID = "test-user-123"
AUTH_HEADER = {"Authorization": f"Bearer {MOCK_TOKEN}"}


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_me_no_token():
    response = client.get("/me")
    assert response.status_code == 401


def test_get_me_invalid_token():
    with patch.dict("os.environ", {}, clear=True):
        response = client.get("/me", headers=AUTH_HEADER)
    assert response.status_code == 401


@patch("app.get_user_context", return_value="Acme Corp")
@patch("app.get_user_id", return_value=MOCK_USER_ID)
def test_get_me_valid_token(mock_uid, mock_ctx):
    response = client.get("/me", headers=AUTH_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == MOCK_USER_ID
    assert data["user_context"] == "Acme Corp"


@patch("app.upsert_user_context")
@patch("app.get_user_id", return_value=MOCK_USER_ID)
def test_post_me_context(mock_uid, mock_upsert):
    response = client.post(
        "/me/context",
        json={"user_context": "New context"},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    assert response.json() == {"status": "created"}
    mock_upsert.assert_called_once_with(MOCK_USER_ID, "New context")


@patch("app.upsert_user_context")
@patch("app.get_user_id", return_value=MOCK_USER_ID)
def test_put_me_context(mock_uid, mock_upsert):
    response = client.put(
        "/me/context",
        json={"user_context": "Updated context"},
        headers=AUTH_HEADER,
    )
    assert response.status_code == 200
    assert response.json() == {"status": "updated"}
    mock_upsert.assert_called_once_with(MOCK_USER_ID, "Updated context")


def test_generate_no_token():
    response = client.post("/generate", json={})
    assert response.status_code == 401


def test_generate_missing_required_field():
    with patch("app.get_user_id", return_value=MOCK_USER_ID):
        response = client.post(
            "/generate",
            json={"topic": "AI"},
            headers=AUTH_HEADER,
        )
    assert response.status_code == 422


VALID_GENERATE_PAYLOAD = {
    "topic": "artificial intelligence",
    "platform": "linkedin",
    "tone": "professional",
    "audience": "tech professionals",
    "language": "English",
    "model": "nvidia/nemotron-3.5-lightning:free",
    "provider": "openrouter",
    "image_enabled": False,
    "citations_enabled": False,
    "user_context": "",
}


def _make_mock_snapshots(text="Generated content"):
    async def _astream(*args, **kwargs):
        yield {
            "status_messages": ["Routing..."],
            "generated_text": "",
            "model": "test-model",
        }
        yield {
            "status_messages": ["Routing...", "Generating..."],
            "generated_text": text,
            "model": "test-model",
        }

    return _astream


@patch("app.get_user_id", return_value=MOCK_USER_ID)
def test_generate_valid_returns_result_event(mock_uid):
    with patch("app.graph") as mock_graph:
        mock_graph.astream = _make_mock_snapshots()
        response = client.post(
            "/generate",
            json=VALID_GENERATE_PAYLOAD,
            headers=AUTH_HEADER,
        )
    assert response.status_code == 200
    events = [line for line in response.text.splitlines() if line.startswith("data:")]
    result_events = [json.loads(e[5:]) for e in events if "generated_text" in e]
    assert result_events
    assert result_events[-1]["generated_text"] == "Generated content"


@patch("app.get_user_id", return_value=MOCK_USER_ID)
def test_generate_all_models_failed_returns_error_event(mock_uid):
    async def _failing_astream(*args, **kwargs):
        raise RuntimeError("All models failed — content could not be generated")
        yield  # make it an async generator

    with patch("app.graph") as mock_graph:
        mock_graph.astream = _failing_astream
        response = client.post(
            "/generate",
            json=VALID_GENERATE_PAYLOAD,
            headers=AUTH_HEADER,
        )
    assert response.status_code == 200
    data_events = [
        json.loads(line[5:])
        for line in response.text.splitlines()
        if line.startswith("data:")
    ]
    assert data_events
    assert "all models are currently unavailable" in data_events[-1]["message"].lower()
