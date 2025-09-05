#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import random
from typing import Any, Dict, List, Optional
import httpx
import backoff

from infra.config import settings


class DomaClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0) -> None:
        self.base_url = (base_url or settings.doma_base_url).rstrip("/")
        self._client = httpx.AsyncClient(timeout=timeout)

    async def close(self) -> None:
        await self._client.aclose()

    # Backoff-enabled HTTP helpers (used when not simulating)
    @backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
    async def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        r = await self._client.get(url, params=params)
        r.raise_for_status()
        return r

    @backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
    async def _post(self, url: str, json: Optional[Dict[str, Any]] = None) -> httpx.Response:
        r = await self._client.post(url, json=json)
        r.raise_for_status()
        return r

    async def get_events(self, kind: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent events.

        If settings.doma_simulate is True, returns simulated events for development.
        Otherwise, performs a real HTTP GET to `${base_url}/events?kind=...&limit=...` (subject to real API shape).
        """
        if settings.doma_simulate:
            # Simulate a small number of events with stable-ish IDs
            sample = [
                {
                    "id": f"sim-{kind}-{i}-{random.randint(1000,9999)}",
                    "kind": kind,
                    "domain": f"demo{i}.tld",
                    "ts": "2025-09-04T00:00:00Z",
                }
                for i in range(min(limit, 3))
            ]
            return sample
        # Real call (adjust path/params to match Doma API once available)
        url = f"{self.base_url}/events"
        params = {"kind": kind, "limit": limit}
        try:
            r = await self._get(url, params=params)
            data = r.json()
            # Expect list of events
            return data if isinstance(data, list) else []
        except httpx.HTTPError:
            return []

    async def get_domain_state(self, domain: str) -> Dict[str, Any]:
        if settings.doma_simulate:
            return {"domain": domain, "state": "simulated"}
        url = f"{self.base_url}/domains/{domain}"
        try:
            r = await self._get(url)
            return r.json()
        except httpx.HTTPError:
            return {"domain": domain, "state": "error"}

    async def place_order(self, domain: str, price: str) -> Dict[str, Any]:
        if settings.doma_simulate:
            return {"ok": True, "order_id": f"sim-{domain}-{price}"}
        url = f"{self.base_url}/orders"
        payload = {"domain": domain, "price": price}
        try:
            r = await self._post(url, json=payload)
            return r.json()
        except httpx.HTTPError as e:
            return {"ok": False, "error": str(e)}
