from fastapi import APIRouter, Depends, Query, status

from app.api.v1.deps import AuthenticatedUser, CurrentUser, DbSession
from app.models.enums import RoleName
from app.schemas.alert_rule import AlertRuleCreate, AlertRuleResponse, AlertRuleUpdate
from app.security.rbac import require_any_authenticated, require_roles
from app.services.alert_rule import AlertRuleService

router = APIRouter(prefix="/organizations/me/alert-rules", tags=["Alert Rules"])


def _org_id(current: CurrentUser) -> int:
    if current.organization_id is None:
        from app.core.exceptions import ValidationAppError

        raise ValidationAppError("No organization context")
    return current.organization_id


@router.get("", response_model=list[AlertRuleResponse], summary="List alert rules")
def list_alert_rules(
    db: DbSession,
    current: CurrentUser = Depends(require_any_authenticated),
    asset_id: int | None = Query(default=None),
) -> list[AlertRuleResponse]:
    return AlertRuleService(db).list_rules(
        organization_id=_org_id(current),
        requester=current.user,
        asset_id=asset_id,
    )


@router.post(
    "",
    response_model=AlertRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create alert rule",
)
def create_alert_rule(
    payload: AlertRuleCreate,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.DEVOPS_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> AlertRuleResponse:
    return AlertRuleService(db).create_rule(
        organization_id=_org_id(current),
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.patch("/{rule_id}", response_model=AlertRuleResponse, summary="Update alert rule")
def update_alert_rule(
    rule_id: int,
    payload: AlertRuleUpdate,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.DEVOPS_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> AlertRuleResponse:
    return AlertRuleService(db).update_rule(
        organization_id=_org_id(current),
        rule_id=rule_id,
        payload=payload,
        requester=current.user,
        roles=current.roles,
    )


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete alert rule")
def delete_alert_rule(
    rule_id: int,
    db: DbSession,
    current: CurrentUser = Depends(require_roles(
        RoleName.ORGANIZATION_ADMIN,
        RoleName.DEVOPS_ENGINEER,
        RoleName.SUPER_ADMIN,
    )),
) -> None:
    AlertRuleService(db).delete_rule(
        organization_id=_org_id(current),
        rule_id=rule_id,
        requester=current.user,
        roles=current.roles,
    )
