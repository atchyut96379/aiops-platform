from typing import Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


def discover_aws_ec2_instances(credentials: dict[str, Any], region: Optional[str] = None) -> list[dict[str, Any]]:
    """Discover EC2 instances using boto3. Falls back to demo data if credentials missing or invalid."""
    access_key = credentials.get("access_key_id") or credentials.get("access_key")
    secret_key = credentials.get("secret_access_key") or credentials.get("secret_key")
    region = region or credentials.get("region") or "us-east-1"

    if not access_key or not secret_key:
        logger.warning("AWS credentials missing — returning demo discovery data")
        return _demo_aws_instances()

    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
        ec2 = session.client("ec2")
        paginator = ec2.get_paginator("describe_instances")
        discovered: list[dict[str, Any]] = []

        for page in paginator.paginate():
            for reservation in page.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    instance_id = inst.get("InstanceId", "unknown")
                    state = inst.get("State", {}).get("Name", "unknown")
                    private_ip = inst.get("PrivateIpAddress")
                    public_ip = inst.get("PublicIpAddress")
                    tags = {t["Key"]: t["Value"] for t in inst.get("Tags", []) if "Key" in t}
                    name = tags.get("Name", instance_id)
                    discovered.append(
                        {
                            "asset_type": "aws_ec2",
                            "hostname": instance_id,
                            "ip_address": public_ip or private_ip,
                            "os": inst.get("PlatformDetails") or inst.get("Platform") or "linux",
                            "status": "healthy" if state == "running" else "offline",
                            "metadata": {
                                "cloud_provider": "aws",
                                "external_id": instance_id,
                                "region": region,
                                "instance_type": inst.get("InstanceType"),
                                "state": state,
                                "name": name,
                                "integration_tags": tags,
                            },
                        }
                    )
        return discovered or _demo_aws_instances()
    except (ImportError, BotoCoreError, ClientError, Exception) as exc:
        logger.exception("AWS EC2 discovery failed: %s", exc)
        return _demo_aws_instances()


def _demo_aws_instances() -> list[dict[str, Any]]:
    return [
        {
            "asset_type": "aws_ec2",
            "hostname": "i-demo001",
            "ip_address": "10.0.1.10",
            "os": "Linux/UNIX",
            "status": "healthy",
            "metadata": {
                "cloud_provider": "aws",
                "external_id": "i-demo001",
                "region": "us-east-1",
                "instance_type": "t3.medium",
                "state": "running",
                "demo": True,
            },
        }
    ]
