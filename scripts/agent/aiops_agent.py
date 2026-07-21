#!/usr/bin/env python3
"""AIOps lightweight monitoring agent — collects real CPU, memory, disk, network metrics.

Usage:
  set AIOPS_API_URL=http://localhost:8000
  set AIOPS_AGENT_KEY=aiops_xxxxxxxx
  python scripts/agent/aiops_agent.py

Schedule with Windows Task Scheduler, cron, or systemd timer.
"""

from __future__ import annotations

import os
import platform
import socket
import sys
import time

import httpx

try:
    import psutil
except ImportError:
    print("Install psutil: pip install psutil", file=sys.stderr)
    raise SystemExit(1)

API_URL = os.getenv("AIOPS_API_URL", "http://localhost:8000").rstrip("/")
AGENT_KEY = os.getenv("AIOPS_AGENT_KEY", "")
INTERVAL = int(os.getenv("AIOPS_AGENT_INTERVAL", "60"))
AGENT_VERSION = "1.0.0"


def collect_metrics() -> list[dict]:
    metrics: list[dict] = []

    cpu = psutil.cpu_percent(interval=1)
    metrics.append({"metric_type": "cpu.percent", "metric_value": round(cpu, 1), "unit": "%"})

    mem = psutil.virtual_memory()
    metrics.append({"metric_type": "memory.percent", "metric_value": round(mem.percent, 1), "unit": "%"})

    try:
        disk = psutil.disk_usage("/")
        metrics.append({"metric_type": "disk.percent", "metric_value": round(disk.percent, 1), "unit": "%"})
    except Exception:
        pass

    try:
        net = psutil.net_io_counters()
        metrics.append({"metric_type": "network.bytes_sent", "metric_value": float(net.bytes_sent), "unit": "bytes"})
        metrics.append({"metric_type": "network.bytes_recv", "metric_value": float(net.bytes_recv), "unit": "bytes"})
    except Exception:
        pass

    return metrics


def main() -> int:
    if not AGENT_KEY:
        print("Set AIOPS_AGENT_KEY environment variable.", file=sys.stderr)
        return 1

    headers = {"X-Agent-Key": AGENT_KEY, "Content-Type": "application/json"}
    hostname = socket.gethostname()

    print(f"AIOps agent v{AGENT_VERSION} starting on {hostname} ({platform.system()})")
    print(f"Reporting to {API_URL} every {INTERVAL}s")

    with httpx.Client(timeout=30.0) as client:
        while True:
            try:
                client.post(
                    f"{API_URL}/api/v1/agent/heartbeat",
                    headers=headers,
                    json={"agent_version": AGENT_VERSION, "hostname": hostname},
                )

                metrics = collect_metrics()
                resp = client.post(
                    f"{API_URL}/api/v1/agent/metrics",
                    headers=headers,
                    json={"metrics": metrics},
                )
                resp.raise_for_status()
                print(f"Pushed {len(metrics)} metrics: {', '.join(m['metric_type'] for m in metrics)}")
            except httpx.HTTPStatusError as exc:
                print(f"HTTP error: {exc.response.status_code} {exc.response.text}", file=sys.stderr)
            except Exception as exc:
                print(f"Error: {exc}", file=sys.stderr)

            time.sleep(INTERVAL)


if __name__ == "__main__":
    raise SystemExit(main())
