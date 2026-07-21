from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def discover_gcp_vms(credentials: dict[str, Any]) -> list[dict[str, Any]]:
    project_id = credentials.get("project_id")
    logger.info("GCP discovery for project %s (stub mode)", project_id or "unknown")
    return [
        {
            "asset_type": "gcp_vm",
            "hostname": "gcp-app-server-1",
            "ip_address": "10.2.0.5",
            "os": "Debian 12",
            "status": "healthy",
            "metadata": {
                "cloud_provider": "gcp",
                "external_id": "gcp-app-server-1",
                "zone": credentials.get("zone", "us-central1-a"),
                "machine_type": "e2-medium",
                "demo": True,
            },
        }
    ]
