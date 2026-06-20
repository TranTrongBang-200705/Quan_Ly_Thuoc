from __future__ import annotations

class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class NotFoundError(AppError):
    def __init__(self, message: str = "Không tìm thấy dữ liệu.") -> None:
        super().__init__(message, 404)

class UnauthorizedError(AppError):
    def __init__(self, message: str = "Bạn chưa đăng nhập hoặc token không hợp lệ.") -> None:
        super().__init__(message, 401)

class ForbiddenError(AppError):
    def __init__(self, message: str = "Bạn không có quyền thực hiện thao tác này.") -> None:
        super().__init__(message, 403)
