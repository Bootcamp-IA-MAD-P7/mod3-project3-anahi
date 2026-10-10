# Image Generation

How a post gets its image: the scene tag, the Cloudflare client, the model
cascade and the rate limits.

## Pipeline

1. When `image_enabled` is on, the platform prompt builder asks the model to emit a
   scene tag in the generated text:

   | Platform | Tag |
   | --- | --- |
   | LinkedIn | `[HEADER IMAGE: ...]` |
   | Instagram | `[POST IMAGE: ...]` |
   | Medium | `[HEADER IMAGE: ...]` |
   | Substack | `[HEADER IMAGE: ...]` |

2. The platform node in [src/graph/nodes.py](../src/graph/nodes.py) pulls that line
   out of the text and stores it as `state["image_prompt"]`. The tag format shown
   to the LLM embeds the platform's `IMAGE_STYLE`, so the extracted scene already
   carries the style with it.
3. `image_node` forwards the scene as
   `f"{image_prompt}, topic: {topic}"` and streams `ImageFallbackUpdate` values
   from `run_image_with_fallback`.
4. The winning image lands in `state["image_data"]` as raw bytes, and every update
   status is appended to `state["status_messages"]`. When the update carries
   `is_last=True` the node also appends "You've reached your daily image limit".

`image_node` is async, so the graph has to be invoked with
`await graph.ainvoke()`.

## Models

`IMAGE_MODELS` in [src/chains/image_fallback.py](../src/chains/image_fallback.py),
in cascade order:

| Model | Request body | Response |
| --- | --- | --- |
| `@cf/black-forest-labs/flux-2-klein-4b` (default) | `multipart/form-data` with `prompt`, `width`, `height` | JSON, base64 in `result.image` |
| `@cf/black-forest-labs/flux-1-schnell` | JSON with `prompt` only, it rejects `width` and `height` | JSON, base64 in `result.image` |
| `@cf/leonardo/phoenix-1.0` | JSON with `prompt`, `width`, `height` | raw `image/jpeg` bytes |
| `@cf/leonardo/lucid-origin` | JSON with `prompt`, `width`, `height` | JSON, base64 in `result.image` |

`_request_body` in [src/chains/cloudflare.py](../src/chains/cloudflare.py) picks the
body format from the model id, and `_post_to_cloudflare` returns image bytes either
way: it passes raw bytes through when the content type is an image, otherwise it
base64-decodes `result.image`. No `num_steps` is sent, that is a FLUX.1 era
parameter.

If Cloudflare answers with error code `3030` (NSFW filter) the call returns `None`
and `generate_image` retries once with an `illustration, safe for work, ` prefix on
the prompt.

## Fallback cascade

`run_image_with_fallback(prompt, platform, user_id)` walks `IMAGE_MODELS` and yields
an `ImageFallbackUpdate` per attempt:

- `ImageGenerationError` → try the next model, status "Model X unavailable, trying Y..."
- `ImageRateLimitError` → stop immediately, the quota message is surfaced
- success → yield the image and stop
- every model failed → final update with `result=None` and a status ending in
  "without an image", so the post is generated without an image

## Rate limits

Constants live in [src/chains/image_security.py](../src/chains/image_security.py):

| Limit | Value |
| --- | --- |
| Images per user per minute | `MAX_IMAGES_PER_MINUTE` = 2 |
| Images per user per day | `MAX_IMAGES_PER_USER_PER_DAY` = 5 |
| Images per account per day | `_ACCOUNT_MAX_IMAGES_PER_DAY` = 100 |

The per minute check runs first, then the per user day, then the account day.
`check_image_rate_limit(user_id, bypass_limits=True)` skips the checks for callers
that already consumed their budget. `register_image_request` returns `True` on the
image that fills the user's daily allowance.

## Image sizes

`DIMENSIONS` in [src/chains/cloudflare.py](../src/chains/cloudflare.py):

| Platform | Size |
| --- | --- |
| Instagram | 512 x 512 |
| LinkedIn | 768 x 400 |
| Medium | 768 x 432 |
| Substack | 768 x 432 |

## Environment Variables

| Variable | Description |
| --- | --- |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token with Workers AI read permission |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare account id that owns the Workers AI models |

Both are read through `get_settings()` in [src/config.py](../src/config.py).

## Tests

Unit tests (offline, mocked):

```bash
pytest tests/unit/test_image_security.py tests/unit/test_image_fallback.py tests/unit/test_image_node.py
```

Live tests, gated behind `RUN_LIVE_LLM_TESTS=1` and skipped when the Cloudflare
variables are missing:

```bash
RUN_LIVE_LLM_TESTS=1 pytest tests/integration/test_image_generation.py -m live
```

Each parametrized case uses a user id derived from the model name so one model's
per minute budget does not block the next.

## Adding a New Image Model

1. Add the model id to `IMAGE_MODELS` in
   [src/chains/image_fallback.py](../src/chains/image_fallback.py)
2. If it needs a different body format, extend `_request_body` in
   [src/chains/cloudflare.py](../src/chains/cloudflare.py)
3. Confirm `_post_to_cloudflare` handles its response (raw image bytes or base64)
4. Run the live test, it picks up `IMAGE_MODELS` automatically
5. Document the model in the table above
