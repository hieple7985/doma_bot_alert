#!/usr/bin/env python3
from __future__ import annotations
from typing import Iterable
from sqlalchemy import select
from data.models import DeliveredAlert, get_session_factory


class AlertsService:
    async def was_delivered(self, event_id: str) -> bool:
        session_factory = get_session_factory()
        async with session_factory() as s:
            res = await s.execute(select(DeliveredAlert).where(DeliveredAlert.event_id == event_id))
            return res.scalar_one_or_none() is not None

    async def mark_delivered(self, event_id: str) -> None:
        session_factory = get_session_factory()
        async with session_factory() as s:
            s.add(DeliveredAlert(event_id=event_id))
            await s.commit()

    def format_alert(self, title: str, lines: Iterable[str]) -> str:
        body = "\n".join(lines)
        return f"{title}\n{body}"
