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
