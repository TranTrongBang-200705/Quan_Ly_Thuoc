from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings
from app.utils.exceptions import AppError


def ai_base_url() -> str:
    settings = get_settings()
    value = settings.ai_service_url or settings.ai_service_base_url
    return value.rstrip("/")


async def ai_health() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(f"{ai_base_url()}/health")
            res.raise_for_status()
            return res.json()
    except Exception as exc:
        raise AppError(f"AI service khong san sang: {exc}", 503) from exc


async def ai_model_info() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(f"{ai_base_url()}/model/info")
            res.raise_for_status()
            return res.json()
    except Exception as exc:
        raise AppError(f"Khong doc duoc thong tin model AI: {exc}", 503) from exc


async def predict_batch(items: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(f"{ai_base_url()}/predict/batch", json={"items": items})
            if res.status_code >= 400:
                detail = res.text
                try:
                    body = res.json()
                    detail = body.get("detail") or body.get("message") or detail
                except Exception:
                    pass
                raise AppError(f"AI service loi: {detail}", 503)
            return res.json()
    except AppError:
        raise
    except Exception as exc:
        raise AppError(f"Khong goi duoc AI service: {exc}", 503) from exc
