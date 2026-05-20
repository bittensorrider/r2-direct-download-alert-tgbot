import html

import httpx

from bot.config import get_settings
from bot.models import EventType, R2Event

EVENT_LABELS: dict[EventType, str] = {
    "download": "R2 download",
    "object-create": "R2 upload / overwrite",
    "object-delete": "R2 delete",
}


def _matches_extension_filter(key: str) -> bool:
    settings = get_settings()
    extensions = settings.extension_set
    if not extensions:
        return True
    key_lower = key.lower()
    return any(key_lower.endswith(ext) for ext in extensions)


def _is_enabled(event_type: EventType) -> bool:
    settings = get_settings()
    if event_type == "download":
        return settings.notify_download
    if event_type == "object-create":
        return settings.notify_object_create
    return settings.notify_object_delete


def should_alert(event: R2Event) -> bool:
    if not _is_enabled(event.event_type):
        return False

    if event.event_type == "download" and event.ip:
        if event.ip in get_settings().ignore_ip_set:
            return False

    return _matches_extension_filter(event.key)


def format_event_message(event: R2Event) -> str:
    label = EVENT_LABELS[event.event_type]
    file_name = html.escape(event.key.rsplit("/", 1)[-1] or event.key)
    object_path = html.escape(event.key)
    bucket = html.escape(event.bucket)
    when = html.escape(event.timestamp)

    lines = [
        f"<b>{html.escape(label)}</b>",
        "",
        f"<b>File:</b> {file_name}",
        f"<b>Path:</b> <code>{object_path}</code>",
        f"<b>Bucket:</b> {bucket}",
    ]

    if event.action:
        lines.append(f"<b>Action:</b> {html.escape(event.action)}")
    if event.size is not None:
        lines.append(f"<b>Size:</b> {event.size:,} bytes")
    if event.e_tag:
        lines.append(f"<b>ETag:</b> <code>{html.escape(event.e_tag)}</code>")

    if event.event_type == "download":
        ip = html.escape(event.ip or "unknown")
        country = html.escape(event.country or "?")
        ua = html.escape((event.user_agent or "unknown")[:200])
        referer = html.escape(event.referer or "—")
        range_info = html.escape(event.range_header or "full file")
        method = html.escape(event.method or "GET")
        lines.extend(
            [
                f"<b>Method:</b> {method}",
                f"<b>Range:</b> {range_info}",
                f"<b>IP:</b> {ip} ({country})",
                f"<b>Referer:</b> {referer}",
                f"<b>User-Agent:</b> {ua}",
            ]
        )

    lines.append(f"<b>Time (UTC):</b> {when}")
    return "\n".join(lines)


async def send_r2_alert(event: R2Event) -> bool:
    if not should_alert(event):
        return False

    settings = get_settings()
    message = format_event_message(event)
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return True


# Backward-compatible name
async def send_download_alert(event: R2Event) -> bool:
    return await send_r2_alert(event)
