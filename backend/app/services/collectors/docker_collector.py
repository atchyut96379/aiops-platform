from datetime import datetime, timezone
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def collect_docker_metrics(endpoint: str | None = None) -> dict[str, Any]:
    """Collect container list and CPU/memory stats from a Docker host."""
    base_url = endpoint or "unix:///var/run/docker.sock"
    try:
        import docker

        client = docker.DockerClient(base_url=base_url, timeout=10)
        containers = client.containers.list(all=False)
        items: list[dict[str, Any]] = []
        for container in containers[:50]:
            stats = container.stats(stream=False)
            cpu_pct = _calc_cpu_percent(stats)
            mem = stats.get("memory_stats", {})
            mem_usage = mem.get("usage", 0)
            mem_limit = mem.get("limit", 1) or 1
            mem_pct = round((mem_usage / mem_limit) * 100, 1)
            items.append(
                {
                    "container_id": container.short_id,
                    "name": container.name,
                    "image": (container.image.tags or ["unknown"])[0],
                    "status": container.status,
                    "cpu_percent": cpu_pct,
                    "memory_percent": mem_pct,
                }
            )
        return {"containers": items, "count": len(items), "source": "docker"}
    except Exception as exc:
        logger.warning("Docker collection failed (%s): %s", base_url, exc)
        return {
            "containers": [
                {
                    "container_id": "demo-abc123",
                    "name": "aiops-api",
                    "image": "aiops-api:latest",
                    "status": "running",
                    "cpu_percent": 12.5,
                    "memory_percent": 34.2,
                }
            ],
            "count": 1,
            "source": "docker",
            "demo": True,
            "error": str(exc),
        }


def _calc_cpu_percent(stats: dict[str, Any]) -> float:
    try:
        cpu = stats["cpu_stats"]
        precpu = stats["precpu_stats"]
        cpu_delta = cpu["cpu_usage"]["total_usage"] - precpu["cpu_usage"]["total_usage"]
        system_delta = cpu["system_cpu_usage"] - precpu["system_cpu_usage"]
        if system_delta > 0 and cpu_delta > 0:
            cores = len(cpu["cpu_usage"].get("percpu_usage", [1]))
            return round((cpu_delta / system_delta) * cores * 100.0, 1)
    except (KeyError, TypeError, ZeroDivisionError):
        pass
    return 0.0
