"""
NexusTalent Security & Authorization Engine
JWT Management, Password Hashing & Unified RBAC/ABAC Policy Evaluator
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Set
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from backend.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    sub: str  # User ID / Email
    user_id: str
    tenant_id: str
    roles: List[str] = []
    department_id: Optional[str] = None
    permissions: List[str] = []
    exp: Optional[int] = None


class UserContext(BaseModel):
    user_id: str
    email: str
    tenant_id: str
    roles: Set[str] = set()
    permissions: Set[str] = set()
    department_id: Optional[str] = None
    is_superadmin: bool = False


# Password Hashing
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# JWT Generation
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except (JWTError, Exception):
        return None


# Unified RBAC & ABAC Policy Evaluator
class PolicyEngine:
    """
    Attribute-Based Access Control (ABAC) + Role-Based Access Control (RBAC).
    Evaluates role permissions, department boundaries, tenancy, and resource ownership.
    """
    
    ROLE_PERMISSIONS_MAP: Dict[str, Set[str]] = {
        "superadmin": {"*"},
        "hr_admin": {
            "employees:read", "employees:write", "employees:delete",
            "recruitment:read", "recruitment:write", "recruitment:hire",
            "attendance:read", "attendance:write", "attendance:approve",
            "payroll:read", "payroll:write", "payroll:execute",
            "performance:read", "performance:write", "performance:calibrate",
            "helpdesk:read", "helpdesk:write", "helpdesk:manage",
            "audit:read", "settings:manage"
        },
        "hiring_manager": {
            "employees:read",
            "recruitment:read", "recruitment:write", "recruitment:interview", "recruitment:scorecard",
            "attendance:read", "attendance:approve",
            "performance:read", "performance:write",
            "helpdesk:read", "helpdesk:write"
        },
        "recruiter": {
            "recruitment:read", "recruitment:write", "recruitment:sourcing",
            "employees:read",
            "helpdesk:read", "helpdesk:write"
        },
        "payroll_specialist": {
            "payroll:read", "payroll:write", "payroll:execute",
            "attendance:read", "employees:read"
        },
        "employee": {
            "employees:self_read", "employees:self_update",
            "attendance:self_clock", "attendance:self_read", "attendance:leave_request",
            "payroll:self_payslip",
            "performance:self_review", "performance:peer_feedback",
            "helpdesk:create_ticket", "helpdesk:self_read"
        }
    }

    @classmethod
    def resolve_permissions_for_roles(cls, roles: List[str]) -> Set[str]:
        perms = set()
        for role in roles:
            perms.update(cls.ROLE_PERMISSIONS_MAP.get(role.lower(), set()))
        return perms

    @classmethod
    def evaluate(
        cls,
        user: UserContext,
        required_permission: str,
        resource_owner_id: Optional[str] = None,
        resource_department_id: Optional[str] = None
    ) -> bool:
        if user.is_superadmin or "*" in user.permissions:
            return True

        if required_permission in user.permissions:
            # Attribute-Based check: If constrained to department
            if resource_department_id and "hr_admin" not in user.roles:
                if user.department_id and user.department_id != resource_department_id:
                    return False
            return True

        # Self-ownership checks
        if resource_owner_id and resource_owner_id == user.user_id:
            self_perm = required_permission.replace(":", ":self_")
            if self_perm in user.permissions:
                return True

        return False


# FastAPI Dependency for Current User
async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    x_tenant_id: Optional[str] = Header(default=None)
) -> UserContext:
    tenant = x_tenant_id or settings.DEFAULT_TENANT_ID

    if not auth or not auth.credentials:
        # Development fallback / mock superadmin context for easy exploration
        roles = {"superadmin", "hr_admin"}
        perms = PolicyEngine.resolve_permissions_for_roles(list(roles))
        return UserContext(
            user_id="usr_admin_master_001",
            email="admin@nexustalent.enterprise",
            tenant_id=tenant,
            roles=roles,
            permissions=perms,
            department_id="dept_executive",
            is_superadmin=True
        )

    payload = decode_access_token(auth.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    roles_set = set(payload.roles)
    perms_set = PolicyEngine.resolve_permissions_for_roles(payload.roles)
    if payload.permissions:
        perms_set.update(payload.permissions)

    return UserContext(
        user_id=payload.user_id,
        email=payload.sub,
        tenant_id=payload.tenant_id or tenant,
        roles=roles_set,
        permissions=perms_set,
        department_id=payload.department_id,
        is_superadmin="superadmin" in roles_set
    )


def require_permission(permission: str):
    """Decorator dependency to enforce permissions."""
    async def permission_checker(user: UserContext = Depends(get_current_user)):
        if not PolicyEngine.evaluate(user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Missing required permission [{permission}]"
            )
        return user
    return permission_checker
