#!/usr/bin/env python3
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message

from infra.config import settings
from infra.logging import setup_logging
from data.models import init_db
from features.subscriptions import SubscriptionsService
from features.alerts import AlertsService
from features.cta import CTAService
from features.scoring import heuristic_score


async def create_app() -> Dispatcher:
    setup_logging(debug=settings.debug)
    await init_db(settings.database_url)

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    subs = SubscriptionsService(settings.database_url)
    alerts = AlertsService()
    cta = CTAService()

    @dp.message(CommandStart())
    async def on_start(message: Message) -> None:
        await message.answer("Domain Alert Bot ready. Use /help")

    @dp.message(Command("help"))
    async def on_help(message: Message) -> None:
        await message.answer("Commands:\n/sub_add <filter>\n/sub_list\n/sub_del <id>")

    @dp.message(Command("sub_add"))
    async def on_sub_add(message: Message) -> None:
        args = (message.text or "").split(maxsplit=1)
        if len(args) < 2:
            await message.answer("Usage: /sub_add <filter>")
            return
        flt = args[1].strip()
        sid = await subs.add_subscription(user_id=message.from_user.id, filter_text=flt)
        await message.answer(f"Added subscription #{sid}: {flt}")

    @dp.message(Command("sub_list"))
    async def on_sub_list(message: Message) -> None:
        items = await subs.list_subscriptions(user_id=message.from_user.id)
        if not items:
            await message.answer("No subscriptions")
            return
        lines = [f"#{i.id}: {i.filter_text}" for i in items]
        await message.answer("\n".join(lines))

    @dp.message(Command("sub_del"))
    async def on_sub_del(message: Message) -> None:
        args = (message.text or "").split(maxsplit=1)
        if len(args) < 2:
            await message.answer("Usage: /sub_del <id>")
            return
        try:
            sid = int(args[1].strip())
        except ValueError:
            await message.answer("Invalid id")
            return
        ok = await subs.delete_subscription(user_id=message.from_user.id, sub_id=sid)
        await message.answer("Deleted" if ok else "Not found")

    @dp.message(Command("alert_test"))
    async def on_alert_test(message: Message) -> None:
        args = (message.text or "").split(maxsplit=1)
        if len(args) < 2:
            await message.answer("Usage: /alert_test <domain>")
            return
        domain = args[1].strip()
        score = heuristic_score(domain)
        link = await cta.build_cta_link(domain)
        text = alerts.format_alert(
            title=f"Alert: {domain}",
            lines=[
                f"Score: {score}",
                f"CTA: {link}",
            ],
        )
        await message.answer(text)

    return bot, dp


async def main() -> None:
    bot, dp = await create_app()
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
