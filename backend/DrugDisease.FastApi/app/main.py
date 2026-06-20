from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from app.api.routes import router
from app.core.config import get_settings
from app.utils.exceptions import AppError

settings = get_settings()

app = FastAPI(
    title="DrugDisease FastAPI Backend",
    version="1.0.0",
    description="Backend nghiệp vụ FastAPI thay thế ASP.NET Core, giữ AI service Python/FastAPI riêng ở thư mục ai/.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"message": exc.message, "status_code": exc.status_code})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    detail = exc.errors()[0].get("msg", "Dữ liệu gửi lên không hợp lệ.") if exc.errors() else "Dữ liệu gửi lên không hợp lệ."
    return JSONResponse(status_code=400, content={"message": detail, "status_code": 400, "errors": exc.errors()})


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"message": "Lỗi cơ sở dữ liệu. Kiểm tra DATABASE_URL và SQL Server.", "status_code": 500})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"message": "Lỗi hệ thống chưa xử lý.", "status_code": 500})
