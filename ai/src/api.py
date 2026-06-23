from __future__ import annotations

import os
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import sklearn
from fastapi import FastAPI, HTTPException
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from ai.src.train_random_forest import doc_cau_hinh, tao_dac_trung


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "random_forest_thuoc_benh.joblib"
)
DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "random_forest.json"
)

MODEL_PATH = Path(os.getenv("AI_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
CONFIG_PATH = Path(os.getenv("AI_MODEL_CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
MODEL_VERSION = os.getenv("AI_MODEL_VERSION", "random-forest-datathuoc-1.0.0")
MODEL_N_JOBS = int(os.getenv("AI_MODEL_N_JOBS", "1"))


class ApiModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class CandidatePair(ApiModel):
    thuoc_id: int = Field(validation_alias=AliasChoices("thuocId", "drugId"))
    benh_id: int = Field(validation_alias=AliasChoices("benhId", "diseaseId"))
    ma_thuoc: str = Field(default="", validation_alias=AliasChoices("maThuoc", "drugCode"))
    ma_benh: str = Field(default="", validation_alias=AliasChoices("maBenh", "diseaseCode"))
    nhom_thuoc_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("nhomThuocId", "drugGroupId"),
    )
    route_id: int | None = Field(default=None, validation_alias=AliasChoices("routeId"))
    nhom_benh_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("nhomBenhId", "diseaseGroupId"),
    )
    ten_thuoc: str = Field(default="", validation_alias=AliasChoices("tenThuoc", "activeName", "drugName"))
    ten_benh: str = Field(default="", validation_alias=AliasChoices("tenBenh", "diseaseName"))
    ten_thuoc_goc: str = Field(default="", validation_alias=AliasChoices("tenThuocGoc", "tradeName"))
    hoat_chat: str = Field(default="", validation_alias=AliasChoices("hoatChat", "activeIngredient"))
    cong_dung: str = Field(default="", validation_alias=AliasChoices("congDung", "indication", "knownIndications"))
    tac_dung_phu: str = Field(default="", validation_alias=AliasChoices("tacDungPhu", "sideEffects"))
    mo_ta_benh: str = Field(default="", validation_alias=AliasChoices("moTaBenh", "diseaseDescription"))
    trieu_chung: str = Field(default="", validation_alias=AliasChoices("trieuChung", "symptoms"))
    thuoc_dieu_tri_da_biet: str = Field(
        default="",
        validation_alias=AliasChoices("thuocDieuTriDaBiet", "knownTreatments"),
    )
    feature_vector: list[float] = Field(
        default_factory=list,
        validation_alias=AliasChoices("featureVector", "dacTrungBoSung"),
    )


class BatchPredictionRequest(ApiModel):
    items: list[CandidatePair] = Field(min_length=1, max_length=2000)


app = FastAPI(title="Drug Disease AI Service", version="1.0.0")


@lru_cache(maxsize=1)
def load_model() -> Any:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    classifier = getattr(model, "named_steps", {}).get("random_forest")
    if classifier is not None and hasattr(classifier, "n_jobs"):
        classifier.n_jobs = MODEL_N_JOBS
    return model


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Model config file not found: {CONFIG_PATH}")
    return doc_cau_hinh(CONFIG_PATH)


def model_probe() -> tuple[bool, str | None]:
    try:
        load_model()
        load_config()
        return True, None
    except Exception as exc:
        return False, str(exc)


def text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def id_text(value: int | None) -> str:
    return "" if value is None else str(value)


def build_features(item: CandidatePair) -> dict[str, Any]:
    cau_hinh = load_config()
    mau_du_doan: dict[str, Any] = {
        "DrugId": item.thuoc_id,
        "DiseaseId": item.benh_id,
        "DrugCode": text(item.ma_thuoc),
        "DiseaseCode": text(item.ma_benh),
        "DrugGroupId": id_text(item.nhom_thuoc_id),
        "RouteId": id_text(item.route_id),
        "DiseaseGroupId": id_text(item.nhom_benh_id),
        "ActiveName": text(item.ten_thuoc),
        "TradeName": text(item.ten_thuoc_goc),
        "DiseaseName": text(item.ten_benh),
        "FeatureVectorJson": json.dumps(
            {"x": item.feature_vector},
            ensure_ascii=False,
        ),
        "HoatChat": text(item.hoat_chat),
        "CongDung": text(item.cong_dung),
        "TacDungPhu": text(item.tac_dung_phu),
        "MoTaBenh": text(item.mo_ta_benh),
        "TrieuChung": text(item.trieu_chung),
        "ThuocDieuTriDaBiet": text(item.thuoc_dieu_tri_da_biet),
        "LinkTypeCode": "UNKNOWN",
        "ConfidenceLevelCode": "UNKNOWN",
        "SourceScore": "",
    }

    return tao_dac_trung(
        mau_du_doan,
        bool(cau_hinh.get("loai_bo_dac_trung_ro_ri_nhan", True)),
        bool(cau_hinh.get("su_dung_dac_trung_dinh_danh", True)),
        bool(cau_hinh.get("su_dung_dac_trung_trung_khop_truc_tiep", True)),
        bool(cau_hinh.get("su_dung_thuoc_dieu_tri_da_biet", True)),
        bool(cau_hinh.get("su_dung_tac_dung_phu", True)),
        str(cau_hinh.get("che_do_dac_trung", "day_du")),
    )


def positive_class_index(model: Any) -> int:
    classifier = getattr(model, "named_steps", {}).get("random_forest", model)
    classes = list(getattr(classifier, "classes_", getattr(model, "classes_", [])))
    if 1 not in classes:
        raise RuntimeError("Model does not expose positive class LabelValue=1.")
    return classes.index(1)


@app.get("/health")
def health_check() -> dict[str, Any]:
    model_loaded, error = model_probe()
    return {
        "status": "healthy" if model_loaded else "degraded",
        "service": "drug-disease-ai",
        "modelLoaded": model_loaded,
        "modelVersion": MODEL_VERSION,
        "modelPath": str(MODEL_PATH),
        "error": error,
        "scikitLearnVersion": sklearn.__version__,
    }


@app.get("/model/info")
def model_info() -> dict[str, Any]:
    model_loaded, error = model_probe()
    info: dict[str, Any] = {
        "modelVersion": MODEL_VERSION,
        "modelPath": str(MODEL_PATH),
        "configPath": str(CONFIG_PATH),
        "modelLoaded": model_loaded,
        "scikitLearnVersion": sklearn.__version__,
    }
    if error:
        info["error"] = error
    if model_loaded:
        info["modelType"] = type(load_model()).__name__
    return info


@app.post("/predict/batch")
def predict_batch(request: BatchPredictionRequest) -> dict[str, Any]:
    try:
        model = load_model()
        feature_rows = [build_features(item) for item in request.items]
        probabilities = model.predict_proba(feature_rows)
        labels = model.predict(feature_rows)
        positive_index = positive_class_index(model)

        results: list[dict[str, Any]] = []
        for index, item in enumerate(request.items):
            score = float(probabilities[index][positive_index])
            score = max(0.0, min(1.0, score))
            label = int(labels[index])
            results.append(
                {
                    "thuocId": item.thuoc_id,
                    "benhId": item.benh_id,
                    "diemDuDoan": score,
                    "nhanDuDoan": label,
                    "nguonDiem": "AI_MODEL",
                    "drugId": item.thuoc_id,
                    "diseaseId": item.benh_id,
                    "predictionScore": score,
                    "predictedLabel": label,
                    "scoreSource": "AI_MODEL",
                }
            )

        return {"modelVersion": MODEL_VERSION, "results": results}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"AI prediction failed: {exc}") from exc
