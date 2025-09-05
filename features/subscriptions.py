#!/usr/bin/env python3
from __future__ import annotations
from typing import List

from data.models import add_subscription as db_add_subscription
from data.models import list_subscriptions as db_list_subscriptions
from data.models import delete_subscription as db_delete_subscription, Subscription
from data.models import list_all_subscriptions as db_list_all


class SubscriptionsService:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    async def add_subscription(self, user_id: int, filter_text: str) -> int:
        return await db_add_subscription(user_id=user_id, filter_text=filter_text)

    async def list_subscriptions(self, user_id: int) -> List[Subscription]:
        return await db_list_subscriptions(user_id=user_id)

    async def delete_subscription(self, user_id: int, sub_id: int) -> bool:
        return await db_delete_subscription(user_id=user_id, sub_id=sub_id)

    async def list_all(self) -> List[Subscription]:
        return await db_list_all()
