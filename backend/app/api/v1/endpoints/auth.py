from fastapi import APIRouter, Request, status

from app.api.v1.deps import AuthenticatedUser, DbSession, get_client_meta
from app.core.config import settings
from app.core.rate_limit import limiter
from app.schemas.auth import (
    AcceptInviteRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    TotpDisableRequest,
    TotpEnableRequest,
    TotpSetupResponse,
    TotpStatusResponse,
    VerifyEmailRequest,
)
from app.schemas.common import MessageResponse, TokenPair
from app.schemas.organization import OrganizationResponse
from app.schemas.user import UserResponse
from app.services.auth import AuthService
from app.services.membership import MembershipService
from app.services.totp import TotpService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register user and organization",
)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def register(request: Request, payload: RegisterRequest, db: DbSession) -> dict:
    ip, ua = get_client_meta(request)
    user, org, tokens = AuthService(db).register(payload, ip_address=ip, user_agent=ua)
    return {
        "user": UserResponse.model_validate(user),
        "organization": OrganizationResponse.model_validate(org),
        "tokens": tokens,
    }


@router.post("/login", response_model=TokenPair, summary="Login")
@limiter.limit(settings.AUTH_RATE_LIMIT)
def login(request: Request, payload: LoginRequest, db: DbSession) -> TokenPair:
    ip, ua = get_client_meta(request)
    return AuthService(db).login(
        email=payload.email,
        password=payload.password,
        totp_code=payload.totp_code,
        ip_address=ip,
        user_agent=ua,
    )


@router.post("/refresh", response_model=TokenPair, summary="Refresh access token")
@limiter.limit(settings.AUTH_RATE_LIMIT)
def refresh(request: Request, payload: RefreshRequest, db: DbSession) -> TokenPair:
    ip, ua = get_client_meta(request)
    return AuthService(db).refresh(payload.refresh_token, ip_address=ip, user_agent=ua)


@router.post("/logout", response_model=MessageResponse, summary="Logout / revoke refresh token")
def logout(request: Request, payload: LogoutRequest, db: DbSession) -> MessageResponse:
    ip, ua = get_client_meta(request)
    AuthService(db).logout(payload.refresh_token, ip_address=ip, user_agent=ua)
    return MessageResponse(message="Logged out successfully")


@router.post("/forgot-password", response_model=MessageResponse, summary="Request password reset")
@limiter.limit(settings.AUTH_RATE_LIMIT)
def forgot_password(
    request: Request, payload: ForgotPasswordRequest, db: DbSession
) -> MessageResponse:
    AuthService(db).forgot_password(payload.email)
    return MessageResponse(message="If the email exists, a reset link has been sent")


@router.post("/reset-password", response_model=MessageResponse, summary="Reset password")
@limiter.limit(settings.AUTH_RATE_LIMIT)
def reset_password(
    request: Request, payload: ResetPasswordRequest, db: DbSession
) -> MessageResponse:
    AuthService(db).reset_password(token=payload.token, new_password=payload.new_password)
    return MessageResponse(message="Password has been reset successfully")


@router.post("/verify-email", response_model=MessageResponse, summary="Verify email")
def verify_email(payload: VerifyEmailRequest, db: DbSession) -> MessageResponse:
    AuthService(db).verify_email(payload.token)
    return MessageResponse(message="Email verified successfully")


@router.post(
    "/resend-verification",
    response_model=MessageResponse,
    summary="Resend email verification",
)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def resend_verification(
    request: Request, payload: ResendVerificationRequest, db: DbSession
) -> MessageResponse:
    AuthService(db).resend_verification(payload.email)
    return MessageResponse(message="If the email exists and is unverified, a link has been sent")


@router.post("/change-password", response_model=MessageResponse, summary="Change password")
def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    db: DbSession,
    current: AuthenticatedUser,
) -> MessageResponse:
    ip, ua = get_client_meta(request)
    AuthService(db).change_password(
        current.user,
        current_password=payload.current_password,
        new_password=payload.new_password,
        ip_address=ip,
        user_agent=ua,
    )
    return MessageResponse(message="Password changed successfully")


@router.get("/totp/status", response_model=TotpStatusResponse, summary="Get 2FA status")
def totp_status(current: AuthenticatedUser, db: DbSession) -> TotpStatusResponse:
    return TotpStatusResponse(**TotpService(db).status(current.user))


@router.post("/totp/setup", response_model=TotpSetupResponse, summary="Begin 2FA setup")
def totp_setup(current: AuthenticatedUser, db: DbSession) -> TotpSetupResponse:
    return TotpSetupResponse(**TotpService(db).setup(current.user))


@router.post("/totp/enable", response_model=MessageResponse, summary="Confirm and enable 2FA")
def totp_enable(
    payload: TotpEnableRequest, current: AuthenticatedUser, db: DbSession
) -> MessageResponse:
    result = TotpService(db).enable(current.user, code=payload.code)
    return MessageResponse(message=result["message"])


@router.post("/totp/disable", response_model=MessageResponse, summary="Disable 2FA")
def totp_disable(
    payload: TotpDisableRequest, current: AuthenticatedUser, db: DbSession
) -> MessageResponse:
    result = TotpService(db).disable(
        current.user, password=payload.password, code=payload.code
    )
    return MessageResponse(message=result["message"])


@router.post(
    "/accept-invite",
    response_model=dict,
    summary="Accept organization invite",
)
def accept_invite(request: Request, payload: AcceptInviteRequest, db: DbSession) -> dict:
    ip, ua = get_client_meta(request)
    user, org, tokens = MembershipService(db).accept_invite(
        payload, ip_address=ip, user_agent=ua
    )
    return {
        "user": UserResponse.model_validate(user),
        "organization": OrganizationResponse.model_validate(org),
        "tokens": tokens,
    }
