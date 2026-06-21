from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, selectinload
from app.core.security import create_access_token, hash_password, user_roles, validate_password_length, verify_password
from app.models.db_models import Role, User, UserRole
from app.schemas.dto import LoginRequest, RegisterRequest
from app.utils.exceptions import AppError, UnauthorizedError


def user_to_dto(user: User) -> dict:
    return {
        "userId": user.user_id,
        "nguoiDungId": user.user_id,
        "fullName": user.full_name,
        "hoTen": user.full_name,
        "email": user.email,
        "username": user.username,
        "tenDangNhap": user.username,
        "trangThaiTaiKhoan": user.account_status,
        "roles": user_roles(user),
    }


def create_user_code() -> str:
    return ("U-" + uuid.uuid4().hex)[:18].upper()


def create_username(email: str) -> str:
    prefix = email.split("@", 1)[0].strip().lower() or "user"
    return (prefix[:70] + "-" + uuid.uuid4().hex[:8])[:100]


def auth_response(user: User) -> dict:
    roles = user_roles(user)
    access_token, expires_at = create_access_token(user.user_id, user.email, user.full_name, roles)
    return {
        "accessToken": access_token,
        "tokenType": "bearer",
        "expiresAt": expires_at.isoformat(),
        "user": user_to_dto(user),
    }


def register(db: Session, request: RegisterRequest) -> dict:
    try:
        if request.password != request.confirm_password:
            raise AppError("Mật khẩu nhập lại không khớp.")
        validate_password_length(request.password)

        email = request.email.strip().lower()
        exists = db.execute(
            select(User).where(func.lower(User.email) == email)
        ).scalar_one_or_none()
        if exists is not None:
            raise AppError("Email này đã được đăng ký.")

        role = db.execute(select(Role).where(Role.role_code == "NGUOI_DUNG")).scalar_one_or_none()
        if role is None:
            raise AppError("Database chưa seed role NGUOI_DUNG.", 500)

        user = User(
            full_name=request.full_name.strip(),
            email=email,
            username=create_username(email),
            password_hash=hash_password(request.password),
            account_status="Hoạt động",
            created_at=datetime.utcnow(),
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.user_id, role_id=role.role_id, assigned_at=datetime.utcnow()))
        db.commit()

        user = db.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.user_id == user.user_id)
        ).scalar_one()
        response = auth_response(user)
        response["message"] = "Đăng ký tài khoản thành công"
        return response
    except AppError:
        db.rollback()
        raise
    except IntegrityError as exc:
        db.rollback()
        raise AppError("Email này đã được đăng ký.", 400) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise AppError("Lỗi cơ sở dữ liệu khi đăng ký tài khoản.", 500) from exc


def login(db: Session, request: LoginRequest) -> dict:
    try:
        email = request.email.strip().lower()
        user = db.execute(
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(func.lower(User.email) == email, User.account_status == "Hoạt động")
        ).scalar_one_or_none()
    except SQLAlchemyError as exc:
        raise AppError("Lỗi cơ sở dữ liệu khi đăng nhập.", 500) from exc

    if user is None or not verify_password(request.password, user.password_hash):
        raise UnauthorizedError("Email hoặc mật khẩu không đúng.")
    return auth_response(user)
