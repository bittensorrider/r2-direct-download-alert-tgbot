import uvicorn

from bot.config import get_settings
settings = get_settings() 


def main() -> None:
    uvicorn.run(
        "bot.webhook_server:create_app",
        factory=True,
        host=settings.webhook_host,
        port=settings.webhook_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
