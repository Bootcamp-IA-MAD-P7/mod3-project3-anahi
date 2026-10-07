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


class ImageGenerationError(Exception):
    pass


class ImageRateLimitError(Exception):
    pass


async def _post_to_cloudflare(
    prompt: str,
    width: int,
    height: int,
    account_id: str,
    api_token: str,
    model: str,
) -> bytes | None:
    url = _CLOUDFLARE_URL.format(account_id=account_id, model=model)
    async with httpx.AsyncClient(timeout=150) as client:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
                "Accept": "image/jpeg",
            },
            json={
                "prompt": prompt,
                "num_steps": 4,
                "width": width,
                "height": height,
            },
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

    return response.content


async def generate_image(
    prompt: str,
    platform: Platform,
    user_id: str,
    model: str = "@cf/black-forest-labs/flux-1-schnell",
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
