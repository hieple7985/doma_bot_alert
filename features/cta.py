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


    async def order_preview(self, domain: str, price: str, orderbook: str = "DOMA") -> dict:
        """Prepare a human-friendly preview using Subgraph + Orderbook APIs.
        Returns: { ok, domain, price, chainId, tokenAddress, currencies, fees, cta }
        """
        client = await self.ensure_client()
        info = await client.get_name_info(domain)
        if not info:
            # Fallback: still return CTA so demo flow doesn't block
            return {
                "ok": True,
                "domain": domain,
                "price": price,
                "chainId": "N/A",
                "tokenAddress": "N/A",
                "currencies": [],
                "fees": [],
                "note": "Subgraph has no data for this name on testnet",
                "cta": await self.build_cta_link(domain),
            }
        tokens = info.get("tokens") or []
        if not tokens:
            return {
                "ok": True,
                "domain": domain,
                "price": price,
                "chainId": "N/A",
                "tokenAddress": "N/A",
                "currencies": [],
                "fees": [],
                "note": "No token found for this name in Subgraph",
                "cta": await self.build_cta_link(domain),
            }
        token = tokens[0]
        chain_id = (token.get("chain") or {}).get("networkId") or ""
        contract_address = token.get("tokenAddress") or ""
        currencies = await client.get_supported_currencies(chain_id, contract_address, orderbook)
        fees = await client.get_orderbook_fees(orderbook, chain_id, contract_address)
        return {
            "ok": True,
            "domain": domain,
            "price": price,
            "chainId": chain_id or "N/A",
            "tokenAddress": contract_address or "N/A",
            "currencies": currencies,
            "fees": fees,
            "cta": await self.build_cta_link(domain),
        }
