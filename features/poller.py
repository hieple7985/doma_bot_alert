#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import logging
from typing import Optional

from aiogram import Bot

from infra.config import settings
from doma.client import DomaClient
from features.alerts import AlertsService
from features.scoring import heuristic_score
from features.subscriptions import SubscriptionsService

logger = logging.getLogger(__name__)


class Poller:
    def __init__(self, bot: Bot, alerts: AlertsService, client: Optional[DomaClient] = None) -> None:
        self.bot = bot
        self.alerts = alerts
        self.client = client or DomaClient()
        self.subs = SubscriptionsService(settings.database_url)
        self._task: Optional[asyncio.Task] = None
        self._stopped = asyncio.Event()

    async def start(self) -> None:
        if self._task is None or self._task.done():
            self._stopped.clear()
            self._task = asyncio.create_task(self._run(), name="doma_poller")

    async def stop(self) -> None:
        self._stopped.set()
        if self._task:
            await self._task
        await self.client.close()

    async def _run(self) -> None:
        interval = max(3, settings.poll_interval_seconds)
        kind = settings.doma_event_kind
        logger.info(
            "Poller started: interval=%ss kind=%s simulate=%s dry_run=%s",
            interval,
            kind,
            settings.doma_simulate,
            settings.alerts_dry_run,
        )
        while not self._stopped.is_set():
            try:
                events = await self.client.get_events(kind=kind, limit=20)
                sent = 0
                for ev in events:
                    ev_id = str(ev.get("id"))
                    domain = str(ev.get("domain", ""))
                    if not ev_id or not domain:
                        continue
                    # dedupe
                    if await self.alerts.was_delivered(ev_id):
                        continue
                    score = heuristic_score(domain)
                    cta = f"https://start.doma.xyz/?domain={domain}"
                    text = self.alerts.format_alert(
                        title=f"{kind.title()} — {domain}",
                        lines=[
                            f"Score: {score}",
                            f"Event ID: {ev_id}",
                            f"CTA: {cta}",
                        ],
                    )
                    # fan-out: naive mapping by event kind substring in filter_text
                    recipients = await self.subs.list_all()
                    matched_users = {s.user_id for s in recipients if kind in (s.filter_text or "")}
                    if not matched_users:
                        logger.debug("No matching subscribers for kind=%s", kind)
                    if settings.alerts_dry_run:
                        logger.info("[DRY-RUN] Would send to %s: %s", list(matched_users), text.replace("\n", " | "))
                    else:
                        for uid in matched_users:
                            try:
                                await self.bot.send_message(chat_id=uid, text=text)
                            except Exception:
                                logger.exception("Failed to send to user_id=%s", uid)
                        logger.info("Sent alert to %d users", len(matched_users))
                    await self.alerts.mark_delivered(ev_id)
                    sent += 1
                if sent:
                    logger.info("Poller cycle: processed=%d sent=%d", len(events), sent)
            except Exception as e:
                logger.exception("Poller error: %s", e)
            await asyncio.wait([self._stopped.wait()], timeout=interval)

