from typing import Any

from app.services.cloud.azure import discover_azure_vms
from app.services.cloud.aws import discover_aws_ec2_instances

# Re-export GCP from azure module file - create gcp.py
from app.services.cloud.gcp import discover_gcp_vms

__all__ = ["discover_aws_ec2_instances", "discover_azure_vms", "discover_gcp_vms"]
