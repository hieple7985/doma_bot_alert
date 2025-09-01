#!/usr/bin/env python3
from __future__ import annotations
from typing import Optional

from doma.client import DomaClient


class CTAService:
    def __init__(self) -> None:
        self._client: Optional[DomaClient] = None

    async def ensure_client(self) -> DomaClient:
        if self._client is None:
            self._client = DomaClient()
        return self._client

    async def build_cta_link(self, domain: str) -> str:
        # Placeholder deep link into Doma testnet UI (adjust once routes are confirmed)
        return f"https://start.doma.xyz/?domain={domain}"

    async def place_order_sample(self, domain: str, price: str) -> dict:
        client = await self.ensure_client()
        return await client.place_order(domain=domain, price=price)
