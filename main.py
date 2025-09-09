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
from features.poller import Poller


async def create_app() -> tuple[Bot, Dispatcher, Poller]:
    setup_logging(debug=settings.debug)
    await init_db(settings.database_url)

    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    subs = SubscriptionsService(settings.database_url)
    alerts = AlertsService()
    cta = CTAService()
    poller = Poller(bot=bot, alerts=alerts)

    @dp.message(CommandStart())
    async def on_start(message: Message) -> None:
        await message.answer("Domain Alert Bot ready. Use /help")

    @dp.message(Command("help"))
    async def on_help(message: Message) -> None:
        await message.answer(
            "Commands:\n"
            "/sub_add <filter>\n"
            "/sub_list\n"
            "/sub_del <id>\n"
            "/alert_test <domain>\n"
            "/cta_order <domain> <price>\n"
            "/alert_stats"
        )

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


    @dp.message(Command("cta_order"))
    async def on_cta_order(message: Message) -> None:
        args = (message.text or "").split()
        if len(args) < 3:
            await message.answer("Usage: /cta_order <domain> <price>")
            return
        domain = args[1].strip()
        price = args[2].strip()
        try:
            res = await cta.place_order_sample(domain, price)
            if res.get("ok"):
                await message.answer(f"Order placed: {res}")
            else:
                await message.answer(f"Order failed: {res}")
        except Exception as e:
            await message.answer(f"Error: {e}")

        link = await cta.build_cta_link(domain)
        text = alerts.format_alert(
            title=f"Alert: {domain}",
            lines=[
                f"Score: {score}",
                f"CTA: {link}",
            ],
        )

    @dp.message(Command("alert_stats"))
    async def on_alert_stats(message: Message) -> None:
        p = poller
        await message.answer(
            "Poller stats:\n"
            f"processed_total={p.processed_total} sent_total={p.sent_total} deduped_total={p.deduped_total} errors={p.error_total}\n"
            f"last_ack_id={p.last_ack_id} last_cycle_processed={p.last_cycle_processed} last_cycle_sent={p.last_cycle_sent} latency={p.last_cycle_latency:.3f}s"
        )

        await message.answer(text)

    return bot, dp, poller


async def main() -> None:
    bot, dp, poller = await create_app()
    try:
        await poller.start()
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await poller.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
