import base64

import httpx

from src.chains.image_security import (
    check_account_limit,
    check_image_rate_limit,
    register_image_request,
)
from src.config import get_settings
from src.graph.enums import Platform

DIMENSIONS: dict[Platform, tuple[int, int]] = {
    Platform.INSTAGRAM: (512, 512),
    Platform.LINKEDIN: (768, 400),
    Platform.MEDIUM: (768, 432),
    Platform.SUBSTACK: (768, 432),
}

_CLOUDFLARE_URL = (
    "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
)

_MULTIPART_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
_PROMPT_ONLY_MODELS = frozenset({"@cf/black-forest-labs/flux-1-schnell"})


class ImageGenerationError(Exception):
    pass


class ImageRateLimitError(Exception):
    pass


def _request_body(prompt: str, width: int, height: int, model: str) -> dict:
    if model == _MULTIPART_MODEL:
        return {
            "files": {
                "prompt": (None, prompt),
                "width": (None, str(width)),
                "height": (None, str(height)),
            }
        }
    if model in _PROMPT_ONLY_MODELS:
        return {"json": {"prompt": prompt}}
    return {"json": {"prompt": prompt, "width": width, "height": height}}


async def _post_to_cloudflare(
    prompt: str,
    width: int,
    height: int,
    account_id: str,
    api_token: str,
    model: str,
) -> bytes | None:
    url = _CLOUDFLARE_URL.format(account_id=account_id, model=model)
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Accept": "image/png",
    }
    async with httpx.AsyncClient(timeout=150) as client:
        response = await client.post(
            url,
            headers=headers,
            **_request_body(prompt, width, height, model),
        )

    if response.status_code == 429:
        raise ImageRateLimitError(
            "Cloudflare daily image quota exhausted, resets at 00:00 UTC. "
            "Your post will be generated without an image"
        )

    if not response.is_success:
        data = response.json()
        errors = data.get("errors", [])
        if any(e.get("code") == 3030 for e in errors):
            return None
        raise ImageGenerationError(
            f"Cloudflare image generation failed with status {response.status_code}"
        )

    if response.headers.get("content-type", "").startswith("image/"):
        return response.content

    image_b64 = response.json().get("result", {}).get("image")
    if not image_b64:
        return None
    return base64.b64decode(image_b64)


async def generate_image(
    prompt: str,
    platform: Platform,
    user_id: str,
    model: str = "@cf/black-forest-labs/flux-2-klein-4b",
) -> tuple[bytes, bool]:
    check_account_limit()
    check_image_rate_limit(user_id)

    settings = get_settings()
    width, height = DIMENSIONS[platform]

    result = await _post_to_cloudflare(
        prompt=prompt,
        width=width,
        height=height,
        account_id=settings.cloudflare_account_id,
        api_token=settings.cloudflare_api_token,
        model=model,
    )

    if result is None:
        safe_prompt = f"illustration, safe for work, {prompt}"
        result = await _post_to_cloudflare(
            prompt=safe_prompt,
            width=width,
            height=height,
            account_id=settings.cloudflare_account_id,
            api_token=settings.cloudflare_api_token,
            model=model,
        )

    if result is None:
        raise ImageGenerationError("Image generation failed after NSFW retry")

    is_last = register_image_request(user_id)
    return result, is_last
