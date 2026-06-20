from __future__ import annotations

from typing import Any
import httpx
from app.core.config import get_settings
from app.utils.exceptions import AppError


async def ai_health() -> dict[str, Any]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(f"{settings.ai_service_base_url.rstrip('/')}/health")
            res.raise_for_status()
            return res.json()
    except Exception as exc:
        raise AppError(f"AI service không sẵn sàng: {exc}", 503)


async def ai_model_info() -> dict[str, Any]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(f"{settings.ai_service_base_url.rstrip('/')}/model/info")
            res.raise_for_status()
            return res.json()
    except Exception as exc:
        raise AppError(f"Không đọc được thông tin model AI: {exc}", 503)


async def predict_batch(items: list[dict[str, Any]]) -> dict[str, Any]:
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(
                f"{settings.ai_service_base_url.rstrip('/')}/predict/batch",
                json={"items": items},
            )
            if res.status_code >= 400:
                detail = res.text
                try:
                    body = res.json()
                    detail = body.get("detail") or body.get("message") or detail
                except Exception:
                    pass
                raise AppError(f"AI service lỗi: {detail}", 503)
            return res.json()
    except AppError:
        raise
    except Exception as exc:
        raise AppError(f"Không gọi được AI service: {exc}", 503)
