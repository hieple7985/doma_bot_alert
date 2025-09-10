#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import datetime as dt
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Text, select, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

_engine = None
_Session: Optional[async_sessionmaker[AsyncSession]] = None


class Base(DeclarativeBase):
    pass


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    filter_text: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )


class DeliveredAlert(Base):
    __tablename__ = "delivered_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    delivered_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc)
    )


async def init_db(database_url: str) -> None:
    global _engine, _Session
    url = database_url
    if url.startswith("sqlite:///"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    _engine = create_async_engine(url, echo=False, future=True)
    _Session = async_sessionmaker(bind=_engine, expire_on_commit=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    assert _Session is not None, "DB not initialized"
    return _Session


# Convenience helpers used by services
async def add_subscription(user_id: int, filter_text: str) -> int:
    session_factory = get_session_factory()
    async with session_factory() as s:
        sub = Subscription(user_id=user_id, filter_text=filter_text)
        s.add(sub)
        await s.commit()
        await s.refresh(sub)
        return sub.id


async def list_subscriptions(user_id: int) -> list[Subscription]:
    session_factory = get_session_factory()
    async with session_factory() as s:
        res = await s.execute(select(Subscription).where(Subscription.user_id == user_id))
        return list(res.scalars().all())


async def delete_subscription(user_id: int, sub_id: int) -> bool:
    session_factory = get_session_factory()
    async with session_factory() as s:
        res = await s.execute(
            select(Subscription).where(Subscription.id == sub_id, Subscription.user_id == user_id)
        )
        obj = res.scalar_one_or_none()
        if not obj:
            return False
        await s.delete(obj)
        await s.commit()
        return True



async def list_all_subscriptions() -> list[Subscription]:
    session_factory = get_session_factory()
    async with session_factory() as s:
        res = await s.execute(select(Subscription))
        return list(res.scalars().all())
