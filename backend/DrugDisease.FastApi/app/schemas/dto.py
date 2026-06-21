from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field


class CamelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class RegisterRequest(CamelModel):
    full_name: str = Field(alias="fullName", min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, validation_alias=AliasChoices("phoneNumber", "phone"), max_length=30)
    organization: str | None = Field(default=None, max_length=255)
    password: str = Field(min_length=6)
    confirm_password: str = Field(alias="confirmPassword")


class LoginRequest(CamelModel):
    email: str = Field(min_length=1, max_length=200)
    password: str


class PredictionCreateRequest(CamelModel):
    prediction_type: str = Field(validation_alias=AliasChoices("predictionType", "kieuDuDoan"))
    drug_id: int | None = Field(default=None, validation_alias=AliasChoices("drugId", "thuocId", "thuocDauVaoId"), ge=1)
    disease_id: int | None = Field(default=None, validation_alias=AliasChoices("diseaseId", "benhId", "benhDauVaoId"), ge=1)
    top_k: int = Field(default=10, validation_alias=AliasChoices("topK", "soLuongKetQua"), ge=1, le=100)
    score_threshold: float | None = Field(default=0.5, validation_alias=AliasChoices("scoreThreshold", "nguongDiem"), ge=0, le=1)
    purpose: str | None = Field(default=None, validation_alias=AliasChoices("purpose", "mucDich"), max_length=500)
    contact_email: EmailStr | None = Field(default=None, validation_alias=AliasChoices("contactEmail", "emailLienHe"))
    medical_warning_accepted: bool = Field(default=False, validation_alias=AliasChoices("medicalWarningAccepted", "daChapNhanCanhBaoYTe"))


class LinkCreateRequest(CamelModel):
    drug_id: int = Field(alias="drugId", ge=1)
    disease_id: int = Field(alias="diseaseId", ge=1)
    link_type_id: int = Field(alias="linkTypeId", ge=1)
    evidence_status_id: int = Field(alias="evidenceStatusId", ge=1)
    confidence_level_id: int | None = Field(default=None, alias="confidenceLevelId", ge=1)
    source_score: float | None = Field(default=None, alias="sourceScore", ge=0, le=1)
    formation_basis: str | None = Field(default=None, alias="formationBasis", max_length=500)
    evidence_description: str | None = Field(default=None, alias="evidenceDescription")


class LinkUpdateRequest(LinkCreateRequest):
    pass


class FeedbackCreateRequest(CamelModel):
    prediction_run_id: int | None = Field(default=None, validation_alias=AliasChoices("predictionRunId", "yeuCauDuDoanId"), ge=1)
    prediction_result_id: int | None = Field(default=None, validation_alias=AliasChoices("predictionResultId", "ketQuaDuDoanId"), ge=1)
    ket_qua_du_doan_id: int | None = Field(default=None, validation_alias=AliasChoices("ketQuaDuDoanId", "predictionResultId"), ge=1)
    user_id: int | None = Field(default=None, validation_alias=AliasChoices("userId", "nguoiDungId"), ge=1)
    general_assessment: str | None = Field(default=None, validation_alias=AliasChoices("generalAssessment", "danhGia"), max_length=100)
    danh_gia: str | None = Field(default=None, validation_alias=AliasChoices("danhGia", "generalAssessment"), max_length=100)
    useful_score: int | None = Field(default=None, alias="usefulScore", ge=1, le=5)
    suggested_action: str | None = Field(default=None, validation_alias=AliasChoices("suggestedAction", "nguonThamKhaoBoSung"), max_length=1000)
    reason_text: str | None = Field(default=None, validation_alias=AliasChoices("reasonText", "nhanXet"), max_length=1000)
    nhan_xet: str | None = Field(default=None, validation_alias=AliasChoices("nhanXet", "reasonText"), max_length=1000)
    nguon_tham_khao_bo_sung: str | None = Field(default=None, validation_alias=AliasChoices("nguonThamKhaoBoSung", "suggestedAction"), max_length=1000)
