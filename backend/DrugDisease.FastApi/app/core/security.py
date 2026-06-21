from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from app.core.config import get_settings
from app.core.database import get_db
from app.models.db_models import User, UserRole, Role
from app.utils.exceptions import AppError, ForbiddenError, UnauthorizedError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)
MAX_BCRYPT_PASSWORD_BYTES = 72
PASSWORD_TOO_LONG_MESSAGE = "Mật khẩu quá dài, vui lòng dùng mật khẩu tối đa 72 bytes."


def password_byte_length(password: str) -> int:
    return len(password.encode("utf-8"))


def validate_password_length(password: str) -> None:
    if password_byte_length(password) > MAX_BCRYPT_PASSWORD_BYTES:
        raise AppError(PASSWORD_TOO_LONG_MESSAGE, 400)


def hash_password(password: str) -> str:
    validate_password_length(password)
    try:
        return pwd_context.hash(password)
    except ValueError as exc:
        if "password cannot be longer than 72 bytes" in str(exc):
            raise AppError(PASSWORD_TOO_LONG_MESSAGE, 400) from exc
        raise AppError("Không thể mã hóa mật khẩu.", 500) from exc


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    if password_byte_length(password) > MAX_BCRYPT_PASSWORD_BYTES:
        return False
    if not password_hash.startswith("$2"):
        return password == password_hash
    try:
        return pwd_context.verify(password, password_hash)
    except Exception:
        return False


def create_access_token(user_id: int, email: str, full_name: str, roles: list[str]) -> tuple[str, datetime]:
    settings = get_settings()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "nameid": str(user_id),
        "email": email,
        "name": full_name,
        "roles": roles,
        "exp": expires_at,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_at


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise UnauthorizedError("Thiếu token đăng nhập.")
    settings = get_settings()
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )
        subject = payload.get("sub") or payload.get("nameid")
        user_id = int(subject)
    except (JWTError, ValueError, TypeError):
        raise UnauthorizedError("Token không hợp lệ hoặc đã hết hạn.")

    user = db.execute(
        select(User)
        .options(selectinload(User.user_roles).selectinload(UserRole.role))
        .where(User.user_id == user_id, User.account_status == "Hoạt động")
    ).scalar_one_or_none()

    if user is None:
        raise UnauthorizedError("Không tìm thấy tài khoản hợp lệ.")
    return user


def user_roles(user: User) -> list[str]:
    return sorted({ur.role.role_code for ur in user.user_roles if ur.role})


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if "ADMIN" not in user_roles(current_user):
        raise ForbiddenError("Bạn không có quyền truy cập trang quản trị.")
    return current_user
