#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import logging
import time
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
        # metrics
        self.processed_total = 0
        self.sent_total = 0
        self.deduped_total = 0
        self.error_total = 0
        self.last_ack_id: Optional[int] = None
        self.last_cycle_latency = 0.0
        self.last_cycle_processed = 0
        self.last_cycle_sent = 0

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
            start = time.perf_counter()
            try:
                events = await self.client.get_events(kind=kind, limit=20)
                sent = 0
                processed = 0
                last_id: int | None = None
                for ev in events:
                    # Poll API shape
                    ev_id_num = ev.get("id")
                    ev_unique = str(ev.get("uniqueId"))
                    ev_type = str(ev.get("type", ""))
                    domain = str(ev.get("name", ""))
                    if ev_id_num is not None:
                        try:
                            last_id = int(ev_id_num)
                        except Exception:
                            pass
                    if not ev_unique or not domain:
                        continue
                    # dedupe on uniqueId per docs
                    if await self.alerts.was_delivered(ev_unique):
                        self.deduped_total += 1
                        continue
                    score = heuristic_score(domain)
                    cta = f"https://start.doma.xyz/?domain={domain}"
                    text = self.alerts.format_alert(
                        title=f"{ev_type} — {domain}",
                        lines=[
                            f"Score: {score}",
                            f"UniqueID: {ev_unique}",
                            f"CTA: {cta}",
                        ],
                    )
                    # fan-out: naive mapping by event type substring in filter_text
                    recipients = await self.subs.list_all()
                    matched_users = {s.user_id for s in recipients if ev_type in (s.filter_text or "")}
                    if not matched_users:
                        logger.debug("No matching subscribers for type=%s", ev_type)
                    if settings.alerts_dry_run:
                        logger.info("[DRY-RUN] Would send to %s: %s", list(matched_users), text.replace("\n", " | "))
                    else:
                        for uid in matched_users:
                            try:
                                await self.bot.send_message(chat_id=uid, text=text)
                            except Exception:
                                logger.exception("Failed to send to user_id=%s", uid)
                        logger.info("Sent alert to %d users", len(matched_users))
                    await self.alerts.mark_delivered(ev_unique)
                    sent += 1
                    processed += 1
                # acknowledge last event id to receive next page
                if last_id is not None:
                    ok = await self.client.ack_events(last_id)
                    self.last_ack_id = last_id
                    if not ok:
                        logger.warning("Failed to ack lastId=%s", last_id)
                # metrics rollup
                self.processed_total += processed
                self.sent_total += sent
                self.last_cycle_processed = processed
                self.last_cycle_sent = sent
                self.last_cycle_latency = time.perf_counter() - start
                if sent or processed:
                    logger.info(
                        "Poller cycle: processed=%d sent=%d latency=%.3fs ack=%s",
                        len(events), sent, self.last_cycle_latency, self.last_ack_id,
                    )
            except Exception as e:
                self.error_total += 1
                logger.exception("Poller error: %s", e)
            await asyncio.wait([self._stopped.wait()], timeout=interval)

