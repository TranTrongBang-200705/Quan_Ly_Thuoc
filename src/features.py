from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder


CATEGORICAL_FEATURES = ["drug_class", "disease_group"]
NUMERIC_FEATURES = ["mechanism_overlap", "clinical_evidence"]
TARGET_COLUMN = "known_link"


@dataclass(frozen=True)
class DatasetBundle:
    features: pd.DataFrame
    target: pd.Series
    metadata: pd.DataFrame


def load_dataset(path: str | Path) -> DatasetBundle:
    dataset = pd.read_csv(path)
    required_columns = {
        "drug_id",
        "drug_name",
        "disease_id",
        "disease_name",
        *CATEGORICAL_FEATURES,
        *NUMERIC_FEATURES,
        TARGET_COLUMN,
    }
    missing_columns = required_columns.difference(dataset.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Dataset is missing required columns: {missing}")

    features = dataset[CATEGORICAL_FEATURES + NUMERIC_FEATURES]
    target = dataset[TARGET_COLUMN].astype(int)
    metadata = dataset[["drug_id", "drug_name", "disease_id", "disease_name"]]
    return DatasetBundle(features=features, target=target, metadata=metadata)


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )
