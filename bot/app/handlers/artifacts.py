from __future__ import annotations

from html import escape
from typing import Any

from telebot import TeleBot, types

from bot.app.client import SaltCloudClient, SaltCloudClientError
from bot.app.config import Settings


def register_artifact_handlers(
        bot: TeleBot,
        client: SaltCloudClient,
        settings: Settings,
) -> None:
    @bot.message_handler(commands=["artifacts"])
    def list_artifacts(message: types.Message) -> None:
        if not client.is_authenticated:
            bot.send_message(
                message.chat.id,
                "SALTAI_CLOUD_API_TOKEN не задан. Для /artifacts нужен backend API token.",
            )
            return

        args = _args(message)
        if not args:
            bot.send_message(
                message.chat.id,
                "Укажи run_id: <code>/artifacts &lt;run_id&gt;</code>",
            )
            return

        run_id = args[0]
        limit = _limit(args[1:], settings.artifacts_limit)

        try:
            artifacts = client.list_run_artifacts(run_id)
        except SaltCloudClientError as exc:
            bot.send_message(message.chat.id, f"Не удалось получить artifacts: {escape(str(exc))}")
            return

        artifacts = sorted(
            artifacts,
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )[:limit]

        bot.send_message(
            message.chat.id,
            _format_artifacts(run_id=run_id, artifacts=artifacts),
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


def _format_artifacts(run_id: str, artifacts: list[dict[str, Any]]) -> str:
    if not artifacts:
        return f"Artifacts для run <code>{escape(run_id)}</code> не найдены."

    lines = [
        f"<b>Artifacts</b> для run <code>{escape(run_id)}</code>",
        "",
    ]

    for index, artifact in enumerate(artifacts, start=1):
        artifact_id = str(artifact.get("id") or "")
        name = str(artifact.get("name") or "unnamed")
        kind = str(artifact.get("kind") or "other")
        status = str(artifact.get("status") or "unknown")
        size_bytes = artifact.get("size_bytes")
        content_type = artifact.get("content_type")
        created_at = str(artifact.get("created_at") or "unknown")
        completed_at = str(artifact.get("completed_at") or "")

        lines.extend([
            f"{index}. <b>{escape(name)}</b>",
            f"   id: <code>{escape(artifact_id)}</code>",
            f"   kind: <code>{escape(kind)}</code>",
            f"   status: <code>{escape(status)}</code>",
            f"   created: <code>{escape(created_at)}</code>",
        ])

        if completed_at:
            lines.append(f"   completed: <code>{escape(completed_at)}</code>")

        if size_bytes is not None:
            lines.append(f"   size: <code>{escape(_format_size(int(size_bytes)))}</code>")

        if content_type:
            lines.append(f"   content_type: <code>{escape(str(content_type))}</code>")

        lines.append("")

    return _telegram_safe("\n".join(lines))


def _format_size(size_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size_bytes)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.2f} {unit}"
        value /= 1024

    return f"{size_bytes} B"


def _telegram_safe(text: str) -> str:
    if len(text) <= 3900:
        return text

    return text[:3800] + "\n\n..."
