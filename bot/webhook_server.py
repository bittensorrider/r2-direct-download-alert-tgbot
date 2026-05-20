from fastapi import FastAPI, Header, HTTPException

from bot.config import get_settings
from bot.models import DownloadEvent, R2Event
from bot.telegram_client import send_r2_alert


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="R2 Download Alerts", version="2.0.0")

    def verify_secret(authorization: str | None) -> None:
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing Authorization header")

        expected = f"Bearer {settings.webhook_secret}"
        if authorization != expected:
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(settings.webhook_path)
    async def r2_event_webhook(
        event: R2Event,
        authorization: str | None = Header(default=None),
    ) -> dict[str, bool | str]:
        verify_secret(authorization)
        sent = await send_r2_alert(event)
        return {"ok": True, "alert_sent": sent}

    @app.post("/webhook/download")
    async def download_webhook_legacy(
        event: DownloadEvent,
        authorization: str | None = Header(default=None),
    ) -> dict[str, bool | str]:
        verify_secret(authorization)
        sent = await send_r2_alert(event)
        return {"ok": True, "alert_sent": sent}

    @app.get("/")
    async def root() -> dict[str, str | list[str]]:
        return {
            "service": "r2-download-alerts",
            "webhook": settings.webhook_path,
            "legacy_webhook": "/webhook/download",
            "health": "/health",
            "buckets": settings.bucket_list,
        }

    return app
