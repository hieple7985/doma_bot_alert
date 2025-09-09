#!/usr/bin/env python3
from __future__ import annotations
from typing import Optional

from doma.client import DomaClient
from infra.config import settings


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
        # Respect DRY-RUN: do not perform writes when in dry-run
        if settings.alerts_dry_run:
            return {"ok": True, "order_id": f"dryrun-{domain}-{price}"}
        # If still in overall simulate mode, use simulated client behavior
        client = await self.ensure_client()
        if settings.doma_simulate:
            return await client.place_order(domain=domain, price=price)
        # Real write path not integrated yet (Orderbook REST). Keep UX by returning a friendly error.
        return {
            "ok": False,
            "error": "Orderbook REST not integrated yet in MVP. Use CTA link to proceed in UI.",
        }
