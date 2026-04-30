from html import escape

from telebot import TeleBot, types

from app.config import Settings


def register_start_handlers(bot: TeleBot, settings: Settings) -> None:
    @bot.message_handler(commands=["start"])
    def start(message: types.Message) -> None:
        lines = [
            "<b>SaltAI Cloud Bot</b>",
            "",
            "Команды:",
            "<code>/runs</code> — последние runs для проекта из SALTAI_DEFAULT_PROJECT_ID",
            "<code>/runs &lt;project_id&gt;</code> — последние runs проекта",
            "<code>/run &lt;run_id&gt;</code> — детали конкретного run",
            "<code>/artifacts &lt;run_id&gt;</code> — artifacts конкретного run",
            "<code>/artifact &lt;artifact_id&gt;</code> — детали конкретного artifact",
            "",
            f"Backend: <code>{escape(settings.cloud_base_url)}</code>",
        ]

        if settings.default_project_id:
            lines.append(f"Default project: <code>{escape(settings.default_project_id)}</code>")

        if not settings.has_cloud_token:
            lines.extend([
                "",
                "SALTAI_CLOUD_API_TOKEN не задан, поэтому защищённые Cloud-команды не смогут ходить в backend.",
            ])

        markup = None
        if settings.mini_app_url:
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    text="Open SaltAI Cloud",
                    web_app=types.WebAppInfo(url=settings.mini_app_url),
                )
            )

        bot.send_message(
            message.chat.id,
            "\n".join(lines),
            reply_markup=markup,
        )
