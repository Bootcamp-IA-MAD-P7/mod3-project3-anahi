from dataclasses import dataclass

from src.chains.cloudflare import (
    ImageGenerationError,
    ImageRateLimitError,
    generate_image,
)
from src.graph.enums import Platform

IMAGE_MODELS = [
    "@cf/black-forest-labs/flux-2-klein-4b",
    "@cf/black-forest-labs/flux-1-schnell",
    "@cf/leonardo/phoenix-1.0",
    "@cf/leonardo/lucid-origin",
]


@dataclass
class ImageFallbackUpdate:
    status: str
    result: bytes | None = None
    is_last: bool = False


async def run_image_with_fallback(
    prompt: str,
    platform: Platform,
    user_id: str,
):
    for i, model in enumerate(IMAGE_MODELS):
        try:
            image_bytes, is_last = await generate_image(
                prompt=prompt,
                platform=platform,
                user_id=user_id,
                model=model,
            )
            yield ImageFallbackUpdate(
                status=f"Image generated with {model}",
                result=image_bytes,
                is_last=is_last,
            )
            return

        except ImageRateLimitError as e:
            yield ImageFallbackUpdate(status=str(e))
            return

        except ImageGenerationError:
            next_model = IMAGE_MODELS[i + 1] if i + 1 < len(IMAGE_MODELS) else None
            if next_model:
                yield ImageFallbackUpdate(
                    status=f"Model {model} unavailable, trying {next_model}..."
                )
            else:
                yield ImageFallbackUpdate(
                    status="Image generation failed — your post will be "
                    "generated without an image"
                )
