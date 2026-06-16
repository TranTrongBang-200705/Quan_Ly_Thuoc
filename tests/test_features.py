from pathlib import Path

from src.features import CATEGORICAL_FEATURES, NUMERIC_FEATURES, build_preprocessor, load_dataset


def test_load_dataset_splits_features_target_and_metadata():
    bundle = load_dataset(Path("data/drug_disease_links.csv"))

    assert len(bundle.features) == len(bundle.target) == len(bundle.metadata)
    assert list(bundle.features.columns) == CATEGORICAL_FEATURES + NUMERIC_FEATURES
    assert set(bundle.target.unique()) == {0, 1}


def test_preprocessor_transforms_training_features():
    bundle = load_dataset(Path("data/drug_disease_links.csv"))
    preprocessor = build_preprocessor()

    transformed = preprocessor.fit_transform(bundle.features)

    assert transformed.shape[0] == len(bundle.features)
    assert transformed.shape[1] >= len(NUMERIC_FEATURES)
