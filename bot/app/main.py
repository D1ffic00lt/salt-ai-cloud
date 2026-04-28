import logging

from telebot import TeleBot

from app.client import SaltCloudClient
from app.config import Settings
from app.handlers import (
    register_artifact_handlers,
    register_run_handlers,
    register_start_handlers,
)


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = Settings.from_env()
    settings.validate_bot()

    bot = TeleBot(
        settings.telegram_bot_token,
        parse_mode="HTML",
    )

    client = SaltCloudClient(
        base_url=settings.cloud_base_url,
        api_prefix=settings.cloud_api_prefix,
        api_token=settings.cloud_api_token,
    )

    register_start_handlers(bot, settings)
    register_run_handlers(bot, client, settings)
    register_artifact_handlers(bot, client, settings)

    logging.info("Starting SaltAI Cloud Telegram bot")
    bot.infinity_polling(
        skip_pending=True,
        timeout=settings.polling_timeout,
    )


if __name__ == "__main__":
    main()
