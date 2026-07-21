#!/usr/bin/env python3
"""Legacy metric pusher (user JWT). Prefer the monitoring agent instead.

See scripts/agent/aiops_agent.py for production use with API keys.
"""

from __future__ import annotations

import os
import random
import sys

import httpx

API_URL = os.getenv("AIOPS_API_URL", "http://localhost:8000").rstrip("/")
EMAIL = os.getenv("AIOPS_EMAIL", "")
PASSWORD = os.getenv("AIOPS_PASSWORD", "")


def login(client: httpx.Client) -> str:
    response = client.post(
        f"{API_URL}/api/v1/auth/login",
        json={"email": EMAIL, "password": PASSWORD},
    )
    response.raise_for_status()
    return response.json()["access_token"]


def main() -> int:
    if not EMAIL or not PASSWORD:
        print("Set AIOPS_EMAIL and AIOPS_PASSWORD environment variables.", file=sys.stderr)
        return 1

    headers: dict[str, str] = {}
    with httpx.Client(timeout=30.0) as client:
        token = login(client)
        headers["Authorization"] = f"Bearer {token}"

        assets_resp = client.get(f"{API_URL}/api/v1/organizations/me/assets", headers=headers)
        assets_resp.raise_for_status()
        assets = assets_resp.json()

        if not assets:
            print("No assets found. Add assets in the UI first.")
            return 0

        for asset in assets:
            asset_id = asset["id"]
            hostname = asset.get("hostname", asset_id)
            cpu = round(random.uniform(20, 95), 1)
            memory = round(random.uniform(30, 90), 1)

            for metric_type, value in (
                ("cpu.percent", cpu),
                ("memory.percent", memory),
            ):
                resp = client.post(
                    f"{API_URL}/api/v1/organizations/me/monitoring/assets/{asset_id}/metrics",
                    headers=headers,
                    json={"metric_type": metric_type, "metric_value": value},
                )
                resp.raise_for_status()
                print(f"Pushed {metric_type}={value} for {hostname} (asset {asset_id})")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
