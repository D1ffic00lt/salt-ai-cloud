from __future__ import annotations

from html import escape
from typing import Any

from telebot import TeleBot, types

from bot.app.client import SaltCloudClient, SaltCloudClientError
from bot.app.config import Settings


def register_run_handlers(
        bot: TeleBot,
        client: SaltCloudClient,
        settings: Settings,
) -> None:
    @bot.message_handler(commands=["runs"])
    def list_runs(message: types.Message) -> None:
        if not client.is_authenticated:
            bot.send_message(
                message.chat.id,
                "SALTAI_CLOUD_API_TOKEN не задан. Для /runs нужен backend API token.",
            )
            return

        args = _args(message)
        project_id = args[0] if args else settings.default_project_id

        if project_id is None:
            bot.send_message(
                message.chat.id,
                "Укажи project_id: <code>/runs &lt;project_id&gt;</code>",
            )
            return

        limit = _limit(args[1:] if args else [], settings.runs_limit)

        try:
            runs = client.list_project_runs(project_id)
        except SaltCloudClientError as exc:
            bot.send_message(message.chat.id, f"Не удалось получить runs: {escape(str(exc))}")
            return

        runs = sorted(
            runs,
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )[:limit]

        bot.send_message(
            message.chat.id,
            _format_runs(project_id=project_id, runs=runs),
        )


def _args(message: types.Message) -> list[str]:
    text = message.text or ""
    parts = text.split()
    return parts[1:]


def _limit(args: list[str], default: int) -> int:
    if not args:
        return default

    try:
        value = int(args[0])
    except ValueError:
        return default

    return max(1, min(value, 30))


def _format_runs(project_id: str, runs: list[dict[str, Any]]) -> str:
    if not runs:
        return f"Runs для project <code>{escape(project_id)}</code> не найдены."

    lines = [
        f"<b>Runs</b> для project <code>{escape(project_id)}</code>",
        "",
    ]

    for index, run in enumerate(runs, start=1):
        run_id = str(run.get("id") or "")
        name = str(run.get("name") or "unnamed")
        status = str(run.get("status") or "unknown")
        created_at = str(run.get("created_at") or "unknown")
        started_at = str(run.get("started_at") or "")
        finished_at = str(run.get("finished_at") or "")
        tags = run.get("tags") or []

        lines.extend([
            f"{index}. <b>{escape(name)}</b>",
            f"   id: <code>{escape(run_id)}</code>",
            f"   status: <code>{escape(status)}</code>",
            f"   created: <code>{escape(created_at)}</code>",
        ])

        if started_at:
            lines.append(f"   started: <code>{escape(started_at)}</code>")

        if finished_at:
            lines.append(f"   finished: <code>{escape(finished_at)}</code>")

        if tags:
            lines.append(f"   tags: <code>{escape(', '.join(map(str, tags)))}</code>")

        lines.append(f"   artifacts: <code>/artifacts {escape(run_id)}</code>")
        lines.append("")

    return _telegram_safe("\n".join(lines))


def _telegram_safe(text: str) -> str:
    if len(text) <= 3900:
        return text

    return text[:3800] + "\n\n..."
