from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import sklearn
from fastapi import FastAPI, HTTPException
from pydantic import AliasChoices, BaseModel, ConfigDict, Field


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "random_forest_thuoc_benh.joblib"
)

MODEL_PATH = Path(os.getenv("AI_MODEL_PATH", str(DEFAULT_MODEL_PATH)))
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


def model_probe() -> tuple[bool, str | None]:
    try:
        load_model()
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
    features: dict[str, Any] = {
        "drug_id": item.thuoc_id,
        "disease_id": item.benh_id,
        "drug_code": text(item.ma_thuoc),
        "disease_code": text(item.ma_benh),
        "drug_group_id": id_text(item.nhom_thuoc_id),
        "route_id": id_text(item.route_id),
        "disease_group_id": id_text(item.nhom_benh_id),
        "do_dai_ten_thuoc": len(text(item.ten_thuoc)),
        "do_dai_ten_benh": len(text(item.ten_benh)),
    }

    for index, value in enumerate(item.feature_vector):
        features[f"x_{index}"] = float(value)

    return features


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
