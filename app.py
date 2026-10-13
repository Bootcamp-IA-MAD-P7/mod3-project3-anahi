import base64
import json
import os

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from src.graph.builder import graph
from src.graph.enums import Language, Platform, Provider, Tone
from src.rag.store import get_user_context, upsert_user_context


def get_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Session expired — please sign in again",
        )
    return auth.split(" ", 1)[1]


def get_user_id(token: str) -> str:
    try:
        jwks_client = jwt.PyJWKClient(os.environ["NEON_AUTH_JWKS_URL"])
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        print(f"Signing key alg: {signing_key.algorithm_name}", flush=True)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["EdDSA"],
            options={"verify_aud": False},
        )
        return payload["sub"]
    except Exception as e:
        print(f"JWT error: {type(e).__name__}: {e}", flush=True)
        raise HTTPException(
            status_code=401,
            detail="Session expired — please sign in again",
        )


def authenticated_user(request: Request) -> tuple[str, str]:
    token = get_token(request)
    user_id = get_user_id(token)
    return user_id, token


class GenerateRequest(BaseModel):
    topic: str
    platform: Platform
    tone: Tone
    audience: str
    language: Language
    model: str
    provider: Provider
    image_enabled: bool = False
    citations_enabled: bool = False
    user_context: str = ""


class UserContextRequest(BaseModel):
    user_context: str


app = FastAPI()

origins = [os.environ.get("ALLOWED_ORIGIN", "http://localhost:5173")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/me")
def get_me(auth: tuple[str, str] = Depends(authenticated_user)):
    user_id, _ = auth
    try:
        user_context = get_user_context(user_id)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable — please try again shortly",
        )
    return {"user_id": user_id, "user_context": user_context}


@app.post("/me/context")
def create_context(
    body: UserContextRequest,
    auth: tuple[str, str] = Depends(authenticated_user),
):
    user_id, _ = auth
    try:
        upsert_user_context(user_id, body.user_context)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable — please try again shortly",
        )
    return {"status": "created"}


@app.put("/me/context")
def update_context(
    body: UserContextRequest,
    auth: tuple[str, str] = Depends(authenticated_user),
):
    user_id, _ = auth
    try:
        upsert_user_context(user_id, body.user_context)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable — please try again shortly",
        )
    return {"status": "updated"}


@app.post("/generate")
async def generate(
    body: GenerateRequest,
    request: Request,
    auth: tuple[str, str] = Depends(authenticated_user),
):
    user_id, token = auth

    state = {
        "token": token,
        "topic": body.topic,
        "platform": body.platform,
        "tone": body.tone,
        "audience": body.audience,
        "language": body.language,
        "model": body.model,
        "provider": body.provider,
        "image_enabled": body.image_enabled,
        "citations_enabled": body.citations_enabled,
        "user_context": body.user_context,
        "generated_text": "",
        "image_data": None,
        "image_prompt": "",
        "rag_context": [],
        "status_messages": [],
    }

    async def event_stream():
        try:
            final_state = None
            seen_status_count = 0
            seen_rag_status = False

            async for snapshot in graph.astream(state, stream_mode="values"):
                final_state = snapshot
                new_messages = snapshot["status_messages"][seen_status_count:]
                for msg in new_messages:
                    yield {
                        "event": "status",
                        "data": json.dumps({"message": msg}),
                    }
                seen_status_count = len(snapshot["status_messages"])

                if snapshot.get("rag_status") and not seen_rag_status:
                    yield {
                        "event": "status",
                        "data": json.dumps({"message": snapshot["rag_status"]}),
                    }
                    seen_rag_status = True

            image_data = None
            if final_state.get("image_data"):
                image_data = base64.b64encode(final_state["image_data"]).decode("utf-8")

            yield {
                "event": "result",
                "data": json.dumps(
                    {
                        "generated_text": final_state["generated_text"],
                        "image_data": image_data,
                        "rag_status": final_state.get("rag_status"),
                        "status_messages": final_state["status_messages"],
                        "model": final_state["model"],
                    }
                ),
            }

        except RuntimeError as e:
            print(f"RuntimeError: {e}", flush=True)
            if "All models failed" in str(e):
                yield {
                    "event": "error",
                    "data": json.dumps(
                        {
                            "message": (
                                "Content generation failed — all models are currently "
                                "unavailable. Please try again shortly"
                            ),
                        }
                    ),
                }
            else:
                yield {
                    "event": "error",
                    "data": json.dumps(
                        {
                            "message": (
                                "An unexpected error occurred — please try again"
                            ),
                        }
                    ),
                }
        except Exception as e:
            print(f"Generation error: {e}", flush=True)
            yield {
                "event": "error",
                "data": json.dumps(
                    {
                        "message": "An unexpected error occurred — please try again",
                    }
                ),
            }

    return EventSourceResponse(event_stream())


if os.path.exists("frontend/dist"):
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join("frontend/dist", full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse("frontend/dist/index.html")
