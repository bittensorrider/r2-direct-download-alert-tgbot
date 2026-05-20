from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str = Field(validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(validation_alias="TELEGRAM_CHAT_ID")

    webhook_host: str = Field(default="0.0.0.0", validation_alias="WEBHOOK_HOST")
    webhook_port: int = Field(default=8080, validation_alias="WEBHOOK_PORT")
    webhook_path: str = Field(default="/webhook/event", validation_alias="WEBHOOK_PATH")
    webhook_secret: str = Field(validation_alias="WEBHOOK_SECRET")

    r2_buckets: str = Field(default="", validation_alias="R2_BUCKETS")

    ignore_ips: str = Field(default="", validation_alias="IGNORE_IPS")
    alert_extensions: str = Field(default="", validation_alias="ALERT_EXTENSIONS")

    notify_download: bool = Field(default=True, validation_alias="NOTIFY_DOWNLOAD")
    notify_object_create: bool = Field(default=True, validation_alias="NOTIFY_OBJECT_CREATE")
    notify_object_delete: bool = Field(default=True, validation_alias="NOTIFY_OBJECT_DELETE")

    @property
    def ignore_ip_set(self) -> set[str]:
        return {ip.strip() for ip in self.ignore_ips.split(",") if ip.strip()}

    @property
    def extension_set(self) -> set[str]:
        raw = self.alert_extensions.strip()
        if not raw:
            return set()
        return {ext.strip().lower() for ext in raw.split(",") if ext.strip()}

    @property
    def bucket_list(self) -> list[str]:
        return [name.strip() for name in self.r2_buckets.split(",") if name.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
