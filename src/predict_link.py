from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd

from src.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def build_prediction_row(args: argparse.Namespace) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "drug_class": args.drug_class,
                "disease_group": args.disease_group,
                "mechanism_overlap": args.mechanism_overlap,
                "clinical_evidence": args.clinical_evidence,
            }
        ],
        columns=CATEGORICAL_FEATURES + NUMERIC_FEATURES,
    )


def predict_link_probability(model_path: str | Path, row: pd.DataFrame) -> float:
    model = joblib.load(model_path)
    return float(model.predict_proba(row)[:, 1][0])


def main() -> None:
    parser = argparse.ArgumentParser(description="Predict a drug-disease link probability.")
    parser.add_argument("--model", default="models/random_forest_drug_disease.joblib")
    parser.add_argument("--drug-class", required=True)
    parser.add_argument("--disease-group", required=True)
    parser.add_argument("--mechanism-overlap", type=float, required=True)
    parser.add_argument("--clinical-evidence", type=float, required=True)
    args = parser.parse_args()

    row = build_prediction_row(args)
    probability = predict_link_probability(args.model, row)
    label = "linked" if probability >= 0.5 else "not_linked"
    print(f"link_probability={probability:.4f}")
    print(f"prediction={label}")


if __name__ == "__main__":
    main()
