from __future__ import annotations

from html import escape
from typing import Any

from telebot import TeleBot, types

from app.client import SaltCloudClient, SaltCloudClientError
from app.config import Settings


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

    @bot.message_handler(commands=["run"])
    def get_run(message: types.Message) -> None:
        if not client.is_authenticated:
            bot.send_message(
                message.chat.id,
                "SALTAI_CLOUD_API_TOKEN не задан. Для /run нужен backend API token.",
            )
            return

        args = _args(message)
        if not args:
            bot.send_message(
                message.chat.id,
                "Укажи run_id: <code>/run &lt;run_id&gt;</code>",
            )
            return

        run_id = args[0]

        try:
            details = client.get_run_details(run_id)
        except SaltCloudClientError as exc:
            bot.send_message(message.chat.id, f"Не удалось получить run: {escape(str(exc))}")
            return

        bot.send_message(
            message.chat.id,
            _format_run_details(details),
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

        lines.append(f"   details: <code>/run {escape(run_id)}</code>")
        lines.append(f"   artifacts: <code>/artifacts {escape(run_id)}</code>")
        lines.append("")

    return _telegram_safe("\n".join(lines))


def _format_run_details(details: dict[str, Any]) -> str:
    run = details.get("run") or {}
    metrics = details.get("metrics") or []
    events = details.get("events") or []
    artifacts = details.get("artifacts") or []

    run_id = str(run.get("id") or "")
    name = str(run.get("name") or "unnamed")
    status = str(run.get("status") or "unknown")
    workspace_id = str(run.get("workspace_id") or "")
    project_id = str(run.get("project_id") or "")
    created_by_id = str(run.get("created_by_id") or "")
    created_at = str(run.get("created_at") or "unknown")
    updated_at = str(run.get("updated_at") or "")
    started_at = str(run.get("started_at") or "")
    finished_at = str(run.get("finished_at") or "")
    tags = run.get("tags") or []

    lines = [
        "<b>Run details</b>",
        "",
        f"name: <b>{escape(name)}</b>",
        f"id: <code>{escape(run_id)}</code>",
        f"status: <code>{escape(status)}</code>",
    ]

    if workspace_id:
        lines.append(f"workspace_id: <code>{escape(workspace_id)}</code>")

    if project_id:
        lines.append(f"project_id: <code>{escape(project_id)}</code>")

    if created_by_id:
        lines.append(f"created_by_id: <code>{escape(created_by_id)}</code>")

    lines.append(f"created: <code>{escape(created_at)}</code>")

    if updated_at:
        lines.append(f"updated: <code>{escape(updated_at)}</code>")

    if started_at:
        lines.append(f"started: <code>{escape(started_at)}</code>")

    if finished_at:
        lines.append(f"finished: <code>{escape(finished_at)}</code>")

    if tags:
        lines.append(f"tags: <code>{escape(', '.join(map(str, tags)))}</code>")

    lines.extend([
        "",
        "<b>Summary</b>",
        f"metrics: <code>{len(metrics)}</code>",
        f"events: <code>{len(events)}</code>",
        f"artifacts: <code>{len(artifacts)}</code>",
    ])

    if metrics:
        lines.extend([
            "",
            "<b>Latest metrics</b>",
        ])

        latest_metrics = sorted(
            metrics,
            key=lambda item: str(item.get("timestamp") or item.get("created_at") or ""),
            reverse=True,
        )[:5]

        for metric in latest_metrics:
            key = str(metric.get("key") or "unknown")
            value = str(metric.get("value") or "0")
            step = metric.get("step")
            timestamp = str(metric.get("timestamp") or "")

            line = f"- <code>{escape(key)}</code> = <code>{escape(value)}</code>"
            if step is not None:
                line += f", step <code>{escape(str(step))}</code>"
            if timestamp:
                line += f", <code>{escape(timestamp)}</code>"

            lines.append(line)

    if events:
        lines.extend([
            "",
            "<b>Latest events</b>",
        ])

        latest_events = sorted(
            events,
            key=lambda item: str(item.get("timestamp") or item.get("created_at") or ""),
            reverse=True,
        )[:5]

        for event in latest_events:
            event_type = str(event.get("type") or "unknown")
            level = str(event.get("level") or "info")
            message = str(event.get("message") or "")
            timestamp = str(event.get("timestamp") or "")

            line = f"- <code>{escape(level)}</code> <code>{escape(event_type)}</code>"
            if timestamp:
                line += f" <code>{escape(timestamp)}</code>"
            if message:
                line += f": {escape(message)}"

            lines.append(line)

    if artifacts:
        lines.extend([
            "",
            "<b>Artifacts</b>",
        ])

        latest_artifacts = sorted(
            artifacts,
            key=lambda item: str(item.get("created_at") or ""),
            reverse=True,
        )[:5]

        for artifact in latest_artifacts:
            artifact_id = str(artifact.get("id") or "")
            artifact_name = str(artifact.get("name") or "unnamed")
            artifact_status = str(artifact.get("status") or "unknown")

            lines.extend([
                f"- <b>{escape(artifact_name)}</b> <code>{escape(artifact_status)}</code>",
                f"  <code>/artifact {escape(artifact_id)}</code>",
            ])

    return _telegram_safe("\n".join(lines))


def _telegram_safe(text: str) -> str:
    if len(text) <= 3900:
        return text

    return text[:3800] + "\n\n..."
