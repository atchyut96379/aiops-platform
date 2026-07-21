import enum


class RoleName(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ORGANIZATION_ADMIN = "organization_admin"
    DEVOPS_ENGINEER = "devops_engineer"
    CLOUD_ENGINEER = "cloud_engineer"
    SUPPORT_ENGINEER = "support_engineer"
    READ_ONLY = "read_only"


class SubscriptionPlan(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


ROLE_DESCRIPTIONS: dict[RoleName, str] = {
    RoleName.SUPER_ADMIN: "Platform-wide administrator",
    RoleName.ORGANIZATION_ADMIN: "Organization administrator",
    RoleName.DEVOPS_ENGINEER: "DevOps engineer with infrastructure access",
    RoleName.CLOUD_ENGINEER: "Cloud engineer with cloud resource access",
    RoleName.SUPPORT_ENGINEER: "Support engineer with incident access",
    RoleName.READ_ONLY: "Read-only observer",
}


class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


class AssetType(str, enum.Enum):
    LINUX_SERVER = "linux_server"
    WINDOWS_SERVER = "windows_server"
    VIRTUAL_MACHINE = "virtual_machine"
    AWS_EC2 = "aws_ec2"
    AZURE_VM = "azure_vm"
    GCP_VM = "gcp_vm"
    KUBERNETES_CLUSTER = "kubernetes_cluster"
    DOCKER_HOST = "docker_host"


class AssetStatus(str, enum.Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    OFFLINE = "offline"


class IncidentSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EnvironmentType(str, enum.Enum):
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DR = "dr"
