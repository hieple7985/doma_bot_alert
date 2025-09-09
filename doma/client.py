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
        self._headers = {}
        if settings.doma_api_key:
            # Support either Authorization: Bearer ... or x-api-key: ... via env DOMA_API_HEADER
            if settings.doma_api_header.lower() == "authorization":
                self._headers["Authorization"] = f"Bearer {settings.doma_api_key}"
            else:
                self._headers[settings.doma_api_header] = settings.doma_api_key


    async def close(self) -> None:
        await self._client.aclose()

    # Backoff-enabled HTTP helpers (used when not simulating)
    @backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
    async def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        r = await self._client.get(url, params=params, headers=self._headers or None)
        r.raise_for_status()
        return r

    @backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
    async def _post(self, url: str, json: Optional[Dict[str, Any]] = None) -> httpx.Response:
        r = await self._client.post(url, json=json, headers=self._headers or None)
        r.raise_for_status()
        return r

    async def get_events(self, kind: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch recent events from Doma Poll API or simulate.

        When real: GET {base}/v1/poll with optional eventTypes[], limit, finalizedOnly.
        """
        if settings.doma_simulate:
            # Simulated sample events mapped to Poll API-like shape
            sample = [
                {
                    "id": i,
                    "type": "NAME_TOKEN_LISTED",
                    "name": f"demo{i}.tld",
                    "uniqueId": f"sim-{kind}-{i}-{random.randint(1000,9999)}",
                    "eventData": {"createdAt": "2025-09-04T00:00:00Z"},
                }
                for i in range(1, min(limit, 3) + 1)
            ]
            return sample
        # Real call per docs
        url = f"{self.base_url}/v1/poll"
        params: Dict[str, Any] = {"limit": limit}
        # eventTypes can be repeated; we support comma-separated in env
        types = [t.strip() for t in settings.doma_event_types.split(",") if t.strip()]
        for t in types:
            params.setdefault("eventTypes", []).append(t)
        params["finalizedOnly"] = settings.doma_finalized_only
        try:
            r = await self._get(url, params=params)
            data = r.json() or {}
            events = data.get("events", [])
            # Return list of events as-is; caller will use fields: id, uniqueId, name, type, eventData
            return events if isinstance(events, list) else []
        except httpx.HTTPError:
            return []


    async def ack_events(self, last_event_id: int) -> bool:
        if settings.doma_simulate:
            return True
        url = f"{self.base_url}/v1/poll/ack/{last_event_id}"
        try:
            r = await self._post(url, json=None)
            return r.status_code == 200
        except httpx.HTTPError:
            return False

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

    # ---------- Subgraph (GraphQL) and Orderbook helpers ----------
    async def get_name_info(self, name: str) -> Dict[str, Any]:
        """Fetch basic name info (expiresAt, registrar, tokens) from Subgraph GraphQL."""
        if settings.doma_simulate:
            return {
                "name": name,
                "expiresAt": "2025-12-31T00:00:00Z",
                "tokens": [
                    {
                        "tokenId": "sim-token",
                        "tokenAddress": "0x0000000000000000000000000000000000000000",
                        "ownerAddress": "eip155:11155111:0x0000000000000000000000000000000000000000",
                        "chain": {"networkId": "eip155:11155111"},
                    }
                ],
            }
        url = f"{self.base_url}/graphql"
        query = (
            "query($name: String!) { name(name: $name) { name expiresAt registrar { name ianaId } "
            "tokens { tokenId tokenAddress ownerAddress chain { networkId } } } }"
        )
        try:
            r = await self._post(url, json={"query": query, "variables": {"name": name}})
            data = r.json() or {}
            return (data.get("data", {}) or {}).get("name", {}) or {}
        except httpx.HTTPError:
            return {}

    async def get_supported_currencies(self, chain_id: str, contract_address: str, orderbook: str = "DOMA") -> List[Any]:
        if settings.doma_simulate:
            return [{"symbol": "ETH"}, {"symbol": "USDC"}]
        url = f"{self.base_url}/v1/orderbook/currencies/{chain_id}/{contract_address}/{orderbook}"
        try:
            r = await self._get(url)
            data = r.json() or {}
            return data.get("currencies", [])
        except httpx.HTTPError:
            return []

    async def get_orderbook_fees(self, orderbook: str, chain_id: str, contract_address: str) -> List[Any]:
        if settings.doma_simulate:
            return [["DOMA_FEE", "0.5%"]]
        url = f"{self.base_url}/v1/orderbook/fee/{orderbook}/{chain_id}/{contract_address}"
        try:
            r = await self._get(url)
            data = r.json() or {}
            return data.get("marketplaceFees", [])
        except httpx.HTTPError:
            return []

