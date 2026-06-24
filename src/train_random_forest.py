from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import yaml
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.features import build_preprocessor, load_dataset


def read_config(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def build_model(config: dict) -> Pipeline:
    random_forest_config = config.get("random_forest", {})
    classifier = RandomForestClassifier(
        n_estimators=random_forest_config.get("n_estimators", 200),
        max_depth=random_forest_config.get("max_depth"),
        min_samples_leaf=random_forest_config.get("min_samples_leaf", 1),
        class_weight=random_forest_config.get("class_weight", "balanced"),
        random_state=config.get("random_state", 42),
    )
    return Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("classifier", classifier),
        ]
    )


def evaluate_model(model: Pipeline, x_test, y_test) -> dict:
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    return {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
        "roc_auc": roc_auc_score(y_test, probabilities),
        "confusion_matrix": confusion_matrix(y_test, predictions).tolist(),
    }


def write_metrics(metrics: dict, path: str | Path) -> None:
    metrics_path = Path(path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with metrics_path.open("w", encoding="utf-8") as metrics_file:
        json.dump(metrics, metrics_file, indent=2)


def train(config: dict) -> tuple[Pipeline, dict]:
    bundle = load_dataset(config["data_path"])
    x_train, x_test, y_train, y_test = train_test_split(
        bundle.features,
        bundle.target,
        test_size=config.get("test_size", 0.3),
        random_state=config.get("random_state", 42),
        stratify=bundle.target,
    )

    model = build_model(config)
    model.fit(x_train, y_train)
    metrics = evaluate_model(model, x_test, y_test)
    return model, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Train RandomForest for drug-disease links.")
    parser.add_argument("--config", default="config/random_forest.yaml")
    args = parser.parse_args()

    config = read_config(args.config)
    model, metrics = train(config)

    model_path = Path(config["model_path"])
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)
    write_metrics(metrics, config["metrics_path"])
    print(f"Saved RandomForest model to {model_path}")
    print(f"Saved evaluation metrics to {config['metrics_path']}")


if __name__ == "__main__":
    main()
