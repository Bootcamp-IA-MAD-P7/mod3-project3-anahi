import json
import os

import httpx
import pytest

from app import app

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("NEON_AUTH_TEST_TOKEN"),
        reason="NEON_AUTH_TEST_TOKEN not set",
    ),
]


@pytest.mark.asyncio
async def test_generate_end_to_end() -> None:
    token = os.environ["NEON_AUTH_TEST_TOKEN"]
    payload = {
        "topic": "artificial intelligence in the workplace",
        "platform": "linkedin",
        "tone": "professional",
        "audience": "tech professionals",
        "language": "en",
        "model": "nvidia/nemotron-3.5-lightning:free",
        "provider": "openrouter",
        "image_enabled": False,
        "citations_enabled": False,
        "user_context": "",
    }

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        async with ac.stream(
            "POST",
            "/generate",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        ) as response:
            assert response.status_code == 200
            result_events = [
                json.loads(line[5:])
                async for line in response.aiter_lines()
                if line.startswith("data:") and "generated_text" in line
            ]

    assert result_events
    assert result_events[-1]["generated_text"].strip()
    assert result_events[-1]["model"]
