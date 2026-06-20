from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.models.db_models import User
from app.schemas.dto import (
    FeedbackCreateRequest,
    LinkCreateRequest,
    LinkUpdateRequest,
    LoginRequest,
    PredictionCreateRequest,
    RegisterRequest,
)
from app.services import (
    admin_link_service,
    auth_service,
    catalog_service,
    dashboard_service,
    feedback_service,
    prediction_service,
)
from app.services.ai_client import ai_health, ai_model_info
from app.utils.exceptions import NotFoundError

router = APIRouter(prefix="/api")


@router.get("/health")
async def health(db: Session = Depends(get_db)) -> dict:
    ai_status = "unknown"
    try:
        data = await ai_health()
        ai_status = data.get("status", "healthy")
    except Exception:
        ai_status = "unavailable"
    return {"status": "healthy", "service": "drug-disease-fastapi", "aiStatus": ai_status}


@router.get("/model/info")
async def model_info(current_user: User = Depends(get_current_user)) -> dict:
    return await ai_model_info()


@router.post("/auth/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    return auth_service.register(db, request)


@router.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)) -> dict:
    return auth_service.login(db, request)


@router.get("/auth/me")
def me(current_user: User = Depends(get_current_user)) -> dict:
    return auth_service.user_to_dto(current_user)


@router.get("/admin/access-check")
def access_check(current_user: User = Depends(require_admin)) -> dict:
    return {"message": "Ban co quyen truy cap trang quan tri.", "role": "ADMIN"}


@router.get("/thuoc")
def thuoc(
    tu_khoa: str | None = Query(default=None, alias="tuKhoa"),
    page: int = 1,
    page_size: int = Query(default=12, alias="pageSize"),
    sap_xep: str | None = Query(default=None, alias="sapXep"),
    nha_san_xuat: str | None = Query(default=None, alias="nhaSanXuat"),
    nhom_thuoc_id: int | None = Query(default=None, alias="nhomThuocId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return catalog_service.list_thuoc(
        db,
        tu_khoa=tu_khoa,
        page=page,
        page_size=page_size,
        sap_xep=sap_xep,
        nha_san_xuat=nha_san_xuat,
        nhom_thuoc_id=nhom_thuoc_id,
    )


@router.get("/thuoc/{thuoc_id}")
def chi_tiet_thuoc(
    thuoc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return catalog_service.get_thuoc_detail(db, thuoc_id)


@router.get("/benh")
def benh(
    tu_khoa: str | None = Query(default=None, alias="tuKhoa"),
    page: int = 1,
    page_size: int = Query(default=12, alias="pageSize"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return catalog_service.list_benh(db, tu_khoa=tu_khoa, page=page, page_size=page_size)


@router.get("/benh/{benh_id}")
def chi_tiet_benh(
    benh_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return catalog_service.get_benh_detail(db, benh_id)


@router.get("/lien-ket-thuoc-benh")
def lien_ket_thuoc_benh(
    thuoc_id: int | None = Query(default=None, alias="thuocId"),
    benh_id: int | None = Query(default=None, alias="benhId"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return catalog_service.search_links(db, thuoc_id=thuoc_id, benh_id=benh_id)


@router.get("/lien-ket-thuoc-benh/theo-thuoc/{thuoc_id}")
def lien_ket_theo_thuoc(
    thuoc_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return catalog_service.search_links(db, thuoc_id=thuoc_id)


@router.get("/lien-ket-thuoc-benh/theo-benh/{benh_id}")
def lien_ket_theo_benh(
    benh_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return catalog_service.search_links(db, benh_id=benh_id)


@router.get("/lookups")
def lookups(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return catalog_service.get_lookups(db)


@router.get("/admin/dashboard")
def admin_dashboard(current_user: User = Depends(require_admin), db: Session = Depends(get_db)) -> dict:
    return dashboard_service.admin_dashboard(db)


@router.get("/admin/links")
def admin_links(
    thuoc_id: int | None = Query(default=None, alias="thuocId"),
    benh_id: int | None = Query(default=None, alias="benhId"),
    drug_id_legacy: int | None = Query(default=None, alias="drugId"),
    disease_id_legacy: int | None = Query(default=None, alias="diseaseId"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    return admin_link_service.admin_search_links(db, thuoc_id or drug_id_legacy, benh_id or disease_id_legacy)


@router.post("/admin/links", status_code=201)
def create_admin_link(
    request: LinkCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    return admin_link_service.create_link(db, request, current_user)


@router.put("/admin/links/{link_id}")
def update_admin_link(
    link_id: int,
    request: LinkUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict:
    return admin_link_service.update_link(db, link_id, request, current_user)


@router.delete("/admin/links/{link_id}", status_code=204)
def delete_admin_link(
    link_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    admin_link_service.delete_link(db, link_id, current_user)
    return Response(status_code=204)


@router.post("/du-doan", status_code=201)
async def create_prediction(
    request: PredictionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return await prediction_service.create_prediction(db, request, current_user)


@router.get("/du-doan/lich-su")
def prediction_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return prediction_service.history(db, current_user.user_id)


@router.get("/du-doan/admin/lich-su")
def admin_prediction_history(
    userId: int | None = None,
    status: str | None = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    return prediction_service.admin_history(db, userId, status)


@router.get("/du-doan/{yeu_cau_du_doan_id}")
def get_prediction(
    yeu_cau_du_doan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = prediction_service.get_prediction(db, yeu_cau_du_doan_id)
    if data is None:
        raise NotFoundError("Khong tim thay yeu cau du doan.")
    return data


@router.post("/phan-hoi-ket-qua")
def create_feedback(
    request: FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return feedback_service.create_feedback(db, request, current_user)


# Compatibility aliases for the older frontend/API contract.
@router.get("/drugs")
def drugs(keyword: str | None = None, take: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return catalog_service.search_drugs(db, keyword, take)


@router.get("/diseases")
def diseases(keyword: str | None = None, take: int = 20, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return catalog_service.search_diseases(db, keyword, take)


@router.get("/links")
def links(
    drugId: int | None = None,
    diseaseId: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    return catalog_service.search_links(db, thuoc_id=drugId, benh_id=diseaseId)


@router.post("/predictions", status_code=201)
async def create_prediction_alias(
    request: PredictionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return await prediction_service.create_prediction(db, request, current_user)


@router.get("/predictions/history")
def prediction_history_alias(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    return prediction_service.history(db, current_user.user_id)


@router.get("/predictions/admin/history")
def admin_prediction_history_alias(
    userId: int | None = None,
    status: str | None = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> list[dict]:
    return prediction_service.admin_history(db, userId, status)


@router.get("/predictions/{request_id}")
def get_prediction_alias(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    data = prediction_service.get_prediction(db, request_id)
    if data is None:
        raise NotFoundError("Khong tim thay yeu cau du doan.")
    return data


@router.post("/feedbacks")
def create_feedback_alias(
    request: FeedbackCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    return feedback_service.create_feedback(db, request, current_user)
