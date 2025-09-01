#!/usr/bin/env python3
from __future__ import annotations
import asyncio
from typing import Any, Dict, List, Optional
import httpx

from infra.config import settings


class DomaClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0) -> None:
        self.base_url = (base_url or settings.doma_base_url).rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    async def get_events(self, kind: str, limit: int = 20) -> List[Dict[str, Any]]:
        # TODO: Replace with real endpoint once available
        # Placeholder returns empty list to keep app runnable
        return []

    async def get_domain_state(self, domain: str) -> Dict[str, Any]:
        # TODO: Replace with real endpoint once available
        return {"domain": domain, "state": "unknown"}

    async def place_order(self, domain: str, price: str) -> Dict[str, Any]:
        # TODO: Implement minimal write on testnet via proper API
        # For now, simulate accepted order id
        return {"ok": True, "order_id": f"sim-{domain}-{price}"}
