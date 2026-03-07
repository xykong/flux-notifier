from __future__ import annotations

import logging
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth import require_api_key
from app.providers.apns import send_apns
from app.providers.fcm import send_fcm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["notify"])


class PushRequest(BaseModel):
    platform: Literal["apns", "fcm"]
    device_token: str
    title: str
    body: str = ""
    data: dict[str, Any] = {}


class PushResponse(BaseModel):
    ok: bool
    platform: str


@router.post("/push", response_model=PushResponse, dependencies=[Depends(require_api_key)])
async def push(req: PushRequest) -> PushResponse:
    try:
        if req.platform == "apns":
            await send_apns(req.device_token, req.title, req.body, req.data)
        else:
            await send_fcm(req.device_token, req.title, req.body, req.data)
        return PushResponse(ok=True, platform=req.platform)
    except Exception as exc:
        logger.error("push failed platform=%s: %s", req.platform, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
