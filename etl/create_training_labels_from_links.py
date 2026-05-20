from __future__ import annotations

import json
import logging
import random
import re
from typing import Any

import pyodbc

from config import LOG_DIR, SQLSERVER_CONNECTION_STRING


LOG_PATH = LOG_DIR / "create_training_labels_from_links.log"

SYSTEM_EMAIL = "system@drug-disease-ml.local"
SYSTEM_FULL_NAME = "System Import Bot"
SYSTEM_USER_CODE = "U-SYSTEM-IMPORT"

EVIDENCE_SOURCE_CODE = "EXISTING_DRUG_LABEL_TEXT"
POSITIVE_LABEL_SOURCE = "AUTO_EXTRACTED_POSITIVE_DEMO"
NEGATIVE_LABEL_SOURCE = "UNKNOWN_NEGATIVE_DEMO"

DATASET_CODE = "DATA-LOCAL-LABEL-TEXT"
DATASET_VERSION_CODE = "VER-LOCAL-LABEL-TEXT-001"
NEGATIVE_RATIO = 1
RANDOM_SEED = 20260519


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_PATH, encoding="utf-8"),
        ],
    )


LOGGER = logging.getLogger(__name__)


def connect_sql_server() -> pyodbc.Connection:
    return pyodbc.connect(SQLSERVER_CONNECTION_STRING, autocommit=False)


def scalar(cursor: pyodbc.Cursor, sql: str, *params: Any) -> Any:
    row = cursor.execute(sql, params).fetchone()
    return None if row is None else row[0]


def fetch_one_id(cursor: pyodbc.Cursor, sql: str, *params: Any) -> int | None:
    value = scalar(cursor, sql, *params)
    return None if value is None else int(value)


def require_lookup_id(
    cursor: pyodbc.Cursor,
    sql: str,
    params: tuple[Any, ...],
    context: str,
) -> int:
    value = fetch_one_id(cursor, sql, *params)
    if value is None:
        raise RuntimeError(f"Could not look up ID after insert for {context}.")
    return value


def truncate(value: Any, max_len: int) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:max_len]


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_data_source(
    cursor: pyodbc.Cursor,
    source_code: str,
    source_name: str,
    description: str | None = None,
) -> int:
    lookup_sql = "SELECT DataSourceId FROM dbo.DataSources WHERE SourceCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, source_code)
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.DataSources(SourceCode, SourceName, Description)
        VALUES (?, ?, ?)
        """,
        source_code,
        source_name,
        description,
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (source_code,),
        f"dbo.DataSources(SourceCode={source_code!r})",
    )


def ensure_system_user(cursor: pyodbc.Cursor) -> int:
    lookup_sql = "SELECT UserId FROM dbo.Users WHERE Email = ?"
    existing = fetch_one_id(cursor, lookup_sql, SYSTEM_EMAIL)
    if existing is not None:
        return existing

    user_code_exists = scalar(
        cursor,
        "SELECT 1 FROM dbo.Users WHERE UserCode = ?",
        SYSTEM_USER_CODE,
    )
    user_code = None if user_code_exists else SYSTEM_USER_CODE
    cursor.execute(
        """
        INSERT INTO dbo.Users(UserCode, FullName, Email, Organization, IsActive, IsDeleted)
        VALUES (?, ?, ?, ?, 1, 0)
        """,
        user_code,
        SYSTEM_FULL_NAME,
        SYSTEM_EMAIL,
        "DrugDiseaseML local ETL",
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (SYSTEM_EMAIL,),
        f"dbo.Users(Email={SYSTEM_EMAIL!r})",
    )


def ensure_training_dataset(
    cursor: pyodbc.Cursor,
    created_by: int,
    data_source_id: int,
) -> int:
    lookup_sql = "SELECT TrainingDatasetId FROM dbo.TrainingDatasets WHERE DatasetCode = ?"
    dataset_id = fetch_one_id(cursor, lookup_sql, DATASET_CODE)
    if dataset_id is None:
        cursor.execute(
            """
            INSERT INTO dbo.TrainingDatasets(DatasetCode, DatasetName, Description, CreatedBy)
            VALUES (?, ?, ?, ?)
            """,
            DATASET_CODE,
            "Local label-text drug-disease ML dataset",
            (
                "Idempotent demo dataset built only from existing imported drug "
                "label text and local disease seed matches. For research only."
            ),
            created_by,
        )
        dataset_id = require_lookup_id(
            cursor,
            lookup_sql,
            (DATASET_CODE,),
            f"dbo.TrainingDatasets(DatasetCode={DATASET_CODE!r})",
        )

    exists = scalar(
        cursor,
        """
        SELECT 1
        FROM dbo.DatasetSources
        WHERE TrainingDatasetId = ? AND DataSourceId = ?
        """,
        dataset_id,
        data_source_id,
    )
    if exists is None:
        cursor.execute(
            """
            INSERT INTO dbo.DatasetSources(TrainingDatasetId, DataSourceId)
            VALUES (?, ?)
            """,
            dataset_id,
            data_source_id,
        )
    return dataset_id


def ensure_dataset_version(cursor: pyodbc.Cursor, dataset_id: int) -> int:
    lookup_sql = "SELECT DatasetVersionId FROM dbo.DatasetVersions WHERE VersionCode = ?"
    dataset_version_id = fetch_one_id(cursor, lookup_sql, DATASET_VERSION_CODE)
    metadata = {
        "source": EVIDENCE_SOURCE_CODE,
        "positive_label_source": POSITIVE_LABEL_SOURCE,
        "negative_label_source": NEGATIVE_LABEL_SOURCE,
        "negative_note": (
            "Generated as unknown/negative sample for ML demo only; "
            "not a medically confirmed negative."
        ),
    }
    if dataset_version_id is None:
        cursor.execute(
            """
            INSERT INTO dbo.DatasetVersions
                (TrainingDatasetId, VersionCode, DrugCount, DiseaseCount,
                 PositiveLinkCount, NegativeUnknownLinkCount, DataFilePath, MetadataJson)
            VALUES (?, ?, 0, 0, 0, 0, ?, ?)
            """,
            dataset_id,
            DATASET_VERSION_CODE,
            "sqlserver://DrugDiseaseML_DB/dbo.DatasetItems",
            json_dumps(metadata),
        )
        dataset_version_id = require_lookup_id(
            cursor,
            lookup_sql,
            (DATASET_VERSION_CODE,),
            f"dbo.DatasetVersions(VersionCode={DATASET_VERSION_CODE!r})",
        )
    else:
        cursor.execute(
            """
            UPDATE dbo.DatasetVersions
            SET MetadataJson = ?
            WHERE DatasetVersionId = ?
            """,
            json_dumps(metadata),
            dataset_version_id,
        )
    return dataset_version_id


def parse_reference_description(description: str | None) -> dict[str, str | None]:
    text = description or ""
    field_match = re.search(r"FieldName=([^;]+)", text)
    keyword_match = re.search(r"MatchedKeyword=([^;]+)", text)
    return {
        "evidence_field": field_match.group(1).strip() if field_match else None,
        "matched_keyword": keyword_match.group(1).strip() if keyword_match else None,
    }


def load_generated_indication_links(cursor: pyodbc.Cursor) -> list[dict[str, Any]]:
    rows = cursor.execute(
        """
        SELECT DISTINCT
            l.LinkId,
            l.DrugId,
            l.DiseaseId,
            lt.LinkTypeCode,
            lt.LinkTypeName,
            er.Description AS EvidenceReferenceDescription
        FROM dbo.DrugDiseaseLinks l
        JOIN dbo.LinkTypes lt ON lt.LinkTypeId = l.LinkTypeId
        JOIN dbo.LinkEvidenceReferences er ON er.LinkId = l.LinkId
        JOIN dbo.DataSources src ON src.DataSourceId = er.DataSourceId
        WHERE l.IsDeleted = 0
          AND lt.LinkTypeCode IN ('INDICATION', 'THERAPEUTIC_INDICATION')
          AND src.SourceCode = ?
          AND er.Description LIKE '%FieldName=KnownIndications%'
        ORDER BY l.LinkId
        """,
        EVIDENCE_SOURCE_CODE,
    ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        metadata = parse_reference_description(row.EvidenceReferenceDescription)
        result.append(
            {
                "link_id": int(row.LinkId),
                "drug_id": int(row.DrugId),
                "disease_id": int(row.DiseaseId),
                "link_type": row.LinkTypeCode,
                "link_type_name": row.LinkTypeName,
                "evidence_field": metadata["evidence_field"],
                "matched_keyword": metadata["matched_keyword"],
            }
        )
    return result


def insert_positive_labels(
    cursor: pyodbc.Cursor,
    positive_links: list[dict[str, Any]],
) -> int:
    inserted = 0
    for link in positive_links:
        exists = scalar(
            cursor,
            """
            SELECT 1
            FROM dbo.LinkTrainingLabels
            WHERE LinkId = ?
              AND DrugId = ?
              AND DiseaseId = ?
              AND LabelValue = 1
              AND LabelSource = ?
            """,
            link["link_id"],
            link["drug_id"],
            link["disease_id"],
            POSITIVE_LABEL_SOURCE,
        )
        if exists is not None:
            continue
        cursor.execute(
            """
            INSERT INTO dbo.LinkTrainingLabels
                (LinkId, DrugId, DiseaseId, LabelValue, LabelSource)
            VALUES (?, ?, ?, 1, ?)
            """,
            link["link_id"],
            link["drug_id"],
            link["disease_id"],
            POSITIVE_LABEL_SOURCE,
        )
        inserted += 1
    return inserted


def active_ids(cursor: pyodbc.Cursor, table_name: str, id_column: str) -> list[int]:
    rows = cursor.execute(
        f"SELECT {id_column} FROM dbo.{table_name} WHERE IsDeleted = 0 ORDER BY {id_column}"
    ).fetchall()
    return [int(row[0]) for row in rows]


def load_existing_link_pairs(cursor: pyodbc.Cursor) -> set[tuple[int, int]]:
    rows = cursor.execute(
        """
        SELECT DrugId, DiseaseId
        FROM dbo.DrugDiseaseLinks
        WHERE IsDeleted = 0
        """
    ).fetchall()
    return {(int(row.DrugId), int(row.DiseaseId)) for row in rows}


def load_existing_negative_pairs(cursor: pyodbc.Cursor) -> set[tuple[int, int]]:
    rows = cursor.execute(
        """
        SELECT DrugId, DiseaseId
        FROM dbo.LinkTrainingLabels
        WHERE LabelValue = 0 AND LabelSource = ?
        """,
        NEGATIVE_LABEL_SOURCE,
    ).fetchall()
    return {(int(row.DrugId), int(row.DiseaseId)) for row in rows}


def insert_negative_labels(cursor: pyodbc.Cursor, positive_count: int) -> int:
    if positive_count <= 0:
        return 0

    drug_ids = active_ids(cursor, "Drugs", "DrugId")
    disease_ids = active_ids(cursor, "Diseases", "DiseaseId")
    existing_link_pairs = load_existing_link_pairs(cursor)
    existing_negative_pairs = load_existing_negative_pairs(cursor)
    target_negative_count = positive_count * NEGATIVE_RATIO
    needed = max(0, target_negative_count - len(existing_negative_pairs))
    if needed == 0:
        return 0

    candidates = [
        (drug_id, disease_id)
        for drug_id in drug_ids
        for disease_id in disease_ids
        if (drug_id, disease_id) not in existing_link_pairs
        and (drug_id, disease_id) not in existing_negative_pairs
    ]
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(candidates)

    inserted = 0
    for drug_id, disease_id in candidates:
        cursor.execute(
            """
            INSERT INTO dbo.LinkTrainingLabels
                (LinkId, DrugId, DiseaseId, LabelValue, LabelSource)
            VALUES (NULL, ?, ?, 0, ?)
            """,
            drug_id,
            disease_id,
            NEGATIVE_LABEL_SOURCE,
        )
        inserted += 1
        if inserted >= needed:
            break
    return inserted


def load_label_records(cursor: pyodbc.Cursor) -> list[dict[str, Any]]:
    rows = cursor.execute(
        """
        SELECT
            lbl.LinkTrainingLabelId,
            lbl.LinkId,
            lbl.DrugId,
            lbl.DiseaseId,
            lbl.LabelValue,
            lbl.LabelSource,
            lt.LinkTypeCode,
            er.Description AS EvidenceReferenceDescription
        FROM dbo.LinkTrainingLabels lbl
        LEFT JOIN dbo.DrugDiseaseLinks l ON l.LinkId = lbl.LinkId
        LEFT JOIN dbo.LinkTypes lt ON lt.LinkTypeId = l.LinkTypeId
        OUTER APPLY (
            SELECT TOP 1 er.Description
            FROM dbo.LinkEvidenceReferences er
            JOIN dbo.DataSources src ON src.DataSourceId = er.DataSourceId
            WHERE er.LinkId = lbl.LinkId
              AND src.SourceCode = ?
              AND er.Description LIKE '%FieldName=KnownIndications%'
            ORDER BY er.LinkEvidenceReferenceId
        ) er
        WHERE lbl.LabelSource IN (?, ?)
        ORDER BY lbl.LabelValue DESC, lbl.DrugId, lbl.DiseaseId, lbl.LinkTrainingLabelId
        """,
        EVIDENCE_SOURCE_CODE,
        POSITIVE_LABEL_SOURCE,
        NEGATIVE_LABEL_SOURCE,
    ).fetchall()

    records: list[dict[str, Any]] = []
    for row in rows:
        evidence = parse_reference_description(row.EvidenceReferenceDescription)
        label_value = int(row.LabelValue)
        records.append(
            {
                "label_id": int(row.LinkTrainingLabelId),
                "link_id": None if row.LinkId is None else int(row.LinkId),
                "drug_id": int(row.DrugId),
                "disease_id": int(row.DiseaseId),
                "label_value": label_value,
                "label_source": row.LabelSource,
                "link_type": row.LinkTypeCode,
                "feature_json": {
                    "drug_id": int(row.DrugId),
                    "disease_id": int(row.DiseaseId),
                    "link_type": row.LinkTypeCode,
                    "source": "existing_label_text"
                    if label_value == 1
                    else "unknown_negative_demo",
                    "matched_keyword": evidence["matched_keyword"],
                    "evidence_field": evidence["evidence_field"],
                    "label_source": row.LabelSource,
                    "note": None
                    if label_value == 1
                    else (
                        "Generated as unknown/negative sample for ML demo only; "
                        "not a medically confirmed negative."
                    ),
                },
            }
        )
    return records


def split_name(index: int, total_count: int) -> str:
    if total_count <= 0:
        return "TRAIN"
    fraction = index / total_count
    if fraction < 0.70:
        return "TRAIN"
    if fraction < 0.85:
        return "VALIDATION"
    return "TEST"


def upsert_dataset_items(
    cursor: pyodbc.Cursor,
    dataset_version_id: int,
    records: list[dict[str, Any]],
) -> tuple[int, int]:
    inserted = 0
    updated = 0
    total_count = len(records)
    for index, record in enumerate(records):
        source_link_id = record["link_id"]
        if source_link_id is None:
            item_id = fetch_one_id(
                cursor,
                """
                SELECT TOP 1 DatasetItemId
                FROM dbo.DatasetItems
                WHERE DatasetVersionId = ?
                  AND DrugId = ?
                  AND DiseaseId = ?
                  AND LabelValue = ?
                  AND SourceLinkId IS NULL
                ORDER BY DatasetItemId
                """,
                dataset_version_id,
                record["drug_id"],
                record["disease_id"],
                record["label_value"],
            )
        else:
            item_id = fetch_one_id(
                cursor,
                """
                SELECT TOP 1 DatasetItemId
                FROM dbo.DatasetItems
                WHERE DatasetVersionId = ?
                  AND DrugId = ?
                  AND DiseaseId = ?
                  AND LabelValue = ?
                  AND SourceLinkId = ?
                ORDER BY DatasetItemId
                """,
                dataset_version_id,
                record["drug_id"],
                record["disease_id"],
                record["label_value"],
                source_link_id,
            )

        feature_json = json_dumps(record["feature_json"])
        split = split_name(index, total_count)
        if item_id is None:
            cursor.execute(
                """
                INSERT INTO dbo.DatasetItems
                    (DatasetVersionId, DrugId, DiseaseId, LabelValue,
                     FeatureVectorJson, SplitName, SourceLinkId)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                dataset_version_id,
                record["drug_id"],
                record["disease_id"],
                record["label_value"],
                feature_json,
                split,
                source_link_id,
            )
            inserted += 1
        else:
            cursor.execute(
                """
                UPDATE dbo.DatasetItems
                SET FeatureVectorJson = ?, SplitName = ?
                WHERE DatasetItemId = ?
                """,
                feature_json,
                split,
                item_id,
            )
            updated += 1
    return inserted, updated


def update_dataset_version_counts(
    cursor: pyodbc.Cursor,
    dataset_version_id: int,
) -> None:
    row = cursor.execute(
        """
        SELECT
            COUNT(DISTINCT DrugId) AS DrugCount,
            COUNT(DISTINCT DiseaseId) AS DiseaseCount,
            SUM(CASE WHEN LabelValue = 1 THEN 1 ELSE 0 END) AS PositiveLinkCount,
            SUM(CASE WHEN LabelValue = 0 THEN 1 ELSE 0 END) AS NegativeUnknownLinkCount
        FROM dbo.DatasetItems
        WHERE DatasetVersionId = ?
        """,
        dataset_version_id,
    ).fetchone()
    cursor.execute(
        """
        UPDATE dbo.DatasetVersions
        SET DrugCount = ?,
            DiseaseCount = ?,
            PositiveLinkCount = ?,
            NegativeUnknownLinkCount = ?
        WHERE DatasetVersionId = ?
        """,
        int(row.DrugCount or 0),
        int(row.DiseaseCount or 0),
        int(row.PositiveLinkCount or 0),
        int(row.NegativeUnknownLinkCount or 0),
        dataset_version_id,
    )


def create_training_labels(
    connection: pyodbc.Connection | None = None,
    commit: bool = True,
) -> dict[str, int]:
    configure_logging()
    owns_connection = connection is None
    conn = connection or connect_sql_server()
    summary = {
        "positive_links_found": 0,
        "positive_labels_created": 0,
        "negative_labels_created": 0,
        "dataset_items_created": 0,
        "dataset_items_updated": 0,
    }

    try:
        cursor = conn.cursor()
        user_id = ensure_system_user(cursor)
        evidence_source_id = ensure_data_source(
            cursor,
            EVIDENCE_SOURCE_CODE,
            "Existing imported drug label text",
            "Local SQL Server drug label fields already imported into dbo.Drugs.",
        )
        dataset_id = ensure_training_dataset(cursor, user_id, evidence_source_id)
        dataset_version_id = ensure_dataset_version(cursor, dataset_id)

        positive_links = load_generated_indication_links(cursor)
        summary["positive_links_found"] = len(positive_links)
        summary["positive_labels_created"] = insert_positive_labels(cursor, positive_links)
        summary["negative_labels_created"] = insert_negative_labels(
            cursor,
            len(positive_links),
        )

        label_records = load_label_records(cursor)
        created, updated = upsert_dataset_items(
            cursor,
            dataset_version_id,
            label_records,
        )
        summary["dataset_items_created"] = created
        summary["dataset_items_updated"] = updated
        update_dataset_version_counts(cursor, dataset_version_id)

        if commit:
            conn.commit()
    except Exception:
        if commit:
            conn.rollback()
        LOGGER.exception("Training label generation failed. Transaction rolled back.")
        raise
    finally:
        if owns_connection:
            conn.close()

    LOGGER.info("Training label summary: %s", summary)
    return summary


def main() -> None:
    summary = create_training_labels()
    print("Created local ML training labels from generated links.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
