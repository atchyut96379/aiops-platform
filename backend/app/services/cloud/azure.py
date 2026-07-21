from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def discover_azure_vms(credentials: dict[str, Any]) -> list[dict[str, Any]]:
    """Azure VM discovery — demo/stub until azure-mgmt-compute is wired with service principal."""
    subscription_id = credentials.get("subscription_id")
    logger.info("Azure discovery for subscription %s (stub mode)", subscription_id or "unknown")
    return [
        {
            "asset_type": "azure_vm",
            "hostname": "vm-prod-web-01",
            "ip_address": "10.1.0.4",
            "os": "Ubuntu 22.04",
            "status": "healthy",
            "metadata": {
                "cloud_provider": "azure",
                "external_id": "vm-prod-web-01",
                "resource_group": credentials.get("resource_group", "prod-rg"),
                "location": credentials.get("location", "centralindia"),
                "demo": True,
            },
        }
    ]


def discover_gcp_vms(credentials: dict[str, Any]) -> list[dict[str, Any]]:
    """GCP VM discovery — demo/stub until google-cloud-compute is wired."""
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
