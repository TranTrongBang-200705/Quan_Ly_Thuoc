from __future__ import annotations

import csv
import json
import logging
import re
from pathlib import Path
from typing import Any, Iterable

import pyodbc

from config import BASE_DIR, LOG_DIR, SQLSERVER_CONNECTION_STRING


SEED_PATH = BASE_DIR / "data" / "seed" / "common_vietnam_diseases.csv"
LOG_PATH = LOG_DIR / "import_common_diseases_local.log"

SYSTEM_EMAIL = "system@drug-disease-ml.local"
SYSTEM_FULL_NAME = "System Import Bot"
SYSTEM_USER_CODE = "U-SYSTEM-IMPORT"

LOCAL_SOURCE_CODE = "LOCAL_SEED"
ICD10_SOURCE_CODE = "ICD10"
MESH_UMLS_SOURCE_CODE = "MESH_UMLS"

LOCAL_FEATURE_CODE = "LOCAL_SEED_PROFILE"
MAX_NVARCHAR_50 = 50
MAX_NVARCHAR_100 = 100
MAX_NVARCHAR_150 = 150
MAX_NVARCHAR_200 = 200
MAX_NVARCHAR_255 = 255
MAX_NVARCHAR_500 = 500
MAX_NVARCHAR_1000 = 1000

EXPECTED_COLUMNS = [
    "DiseaseCode",
    "DiseaseNameVi",
    "DiseaseNameEn",
    "GroupCode",
    "ICD10",
    "MeSHOrUMLS",
    "KeywordsVi",
    "KeywordsEn",
    "DescriptionVi",
    "DescriptionEn",
]

GROUP_NAMES = {
    "CARDIO": "Tim mạch",
    "METABOLIC": "Chuyển hóa nội tiết",
    "RESPIRATORY": "Hô hấp",
    "INFECTIOUS": "Truyền nhiễm",
    "DIGESTIVE": "Tiêu hóa",
    "RENAL_URO": "Thận tiết niệu",
    "NEURO": "Thần kinh",
    "MENTAL": "Sức khỏe tâm thần",
    "CANCER": "Ung thư",
    "MUSCULOSKELETAL": "Cơ xương khớp tự miễn",
    "DERM_ALLERGY": "Da liễu dị ứng",
    "HEMATOLOGY": "Huyết học",
    "SYMPTOM": "Triệu chứng thường gặp",
    "EYE_ENT": "Mắt tai mũi họng",
    "GYNECOLOGY": "Phụ khoa",
    "OTHER": "Khác",
}


def configure_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
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


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value).strip())
    return text or None


def split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    return unique_nonempty(part.strip() for part in value.split(";"))


def unique_nonempty(values: Iterable[Any], max_len: int | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = normalize_text(value)
        if not text:
            continue
        if max_len is not None:
            text = text[:max_len]
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def ensure_data_source(
    cursor: pyodbc.Cursor,
    source_code: str,
    source_name: str,
    description: str | None = None,
    source_url: str | None = None,
) -> int:
    lookup_sql = "SELECT DataSourceId FROM dbo.DataSources WHERE SourceCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, source_code)
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.DataSources(SourceCode, SourceName, SourceUrl, Description)
        VALUES (?, ?, ?, ?)
        """,
        truncate(source_code, MAX_NVARCHAR_50),
        truncate(source_name, MAX_NVARCHAR_200),
        truncate(source_url, MAX_NVARCHAR_500),
        truncate(description, MAX_NVARCHAR_1000),
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (source_code,),
        f"dbo.DataSources(SourceCode={source_code!r})",
    )


def ensure_review_status(
    cursor: pyodbc.Cursor,
    status_code: str,
    status_name: str,
) -> int:
    lookup_sql = "SELECT ReviewStatusId FROM dbo.ReviewStatuses WHERE StatusCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, status_code)
    if existing is not None:
        return existing
    cursor.execute(
        "INSERT INTO dbo.ReviewStatuses(StatusCode, StatusName) VALUES (?, ?)",
        truncate(status_code, MAX_NVARCHAR_50),
        truncate(status_name, MAX_NVARCHAR_100),
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (status_code,),
        f"dbo.ReviewStatuses(StatusCode={status_code!r})",
    )


def ensure_confidence_level(
    cursor: pyodbc.Cursor,
    level_code: str,
    level_name: str,
    min_score: float | None,
    max_score: float | None,
) -> int:
    lookup_sql = "SELECT ConfidenceLevelId FROM dbo.ConfidenceLevels WHERE LevelCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, level_code)
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.ConfidenceLevels(LevelCode, LevelName, MinScore, MaxScore)
        VALUES (?, ?, ?, ?)
        """,
        truncate(level_code, MAX_NVARCHAR_50),
        truncate(level_name, MAX_NVARCHAR_100),
        min_score,
        max_score,
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (level_code,),
        f"dbo.ConfidenceLevels(LevelCode={level_code!r})",
    )


def ensure_disease_group(cursor: pyodbc.Cursor, group_code: str) -> int:
    lookup_sql = "SELECT DiseaseGroupId FROM dbo.DiseaseGroups WHERE GroupCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, group_code)
    if existing is not None:
        return existing
    group_name = GROUP_NAMES.get(group_code, group_code.replace("_", " ").title())
    cursor.execute(
        "INSERT INTO dbo.DiseaseGroups(GroupCode, GroupName) VALUES (?, ?)",
        truncate(group_code, MAX_NVARCHAR_50),
        truncate(group_name, MAX_NVARCHAR_150),
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (group_code,),
        f"dbo.DiseaseGroups(GroupCode={group_code!r})",
    )


def ensure_feature_definition(cursor: pyodbc.Cursor) -> int:
    lookup_sql = """
        SELECT FeatureDefinitionId
        FROM dbo.FeatureDefinitions
        WHERE EntityType = 'DISEASE' AND FeatureCode = ?
    """
    existing = fetch_one_id(cursor, lookup_sql, LOCAL_FEATURE_CODE)
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.FeatureDefinitions
            (EntityType, FeatureCode, FeatureName, DataType, EncodingMethod, Description)
        VALUES ('DISEASE', ?, ?, 'JSON', 'LOCAL_SEED', ?)
        """,
        LOCAL_FEATURE_CODE,
        "Local seed disease profile",
        "Disease names keywords ICD-10 and local curation metadata from common_vietnam_diseases.csv",
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (LOCAL_FEATURE_CODE,),
        f"dbo.FeatureDefinitions(EntityType='DISEASE', FeatureCode={LOCAL_FEATURE_CODE!r})",
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


def read_seed_rows() -> list[dict[str, str]]:
    if not SEED_PATH.exists():
        raise FileNotFoundError(f"Seed file not found: {SEED_PATH}")
    with SEED_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise RuntimeError(
                "Unexpected seed CSV columns. Expected "
                f"{EXPECTED_COLUMNS}, got {reader.fieldnames}."
            )
        rows = [dict(row) for row in reader]
    if len(rows) < 10:
        raise RuntimeError("Disease seed file is too small. Expected at least 10 diseases.")
    return rows


def disease_description(row: dict[str, str]) -> str | None:
    parts = []
    description_vi = normalize_text(row.get("DescriptionVi"))
    description_en = normalize_text(row.get("DescriptionEn"))
    if description_vi:
        parts.append(description_vi)
    if description_en:
        parts.append(f"English: {description_en}")
    return "\n".join(parts) or None


def synonym_terms(row: dict[str, str]) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for term in [row.get("DiseaseNameVi"), *split_terms(row.get("KeywordsVi"))]:
        if term:
            values.append((term, "vi"))
    for term in [row.get("DiseaseNameEn"), *split_terms(row.get("KeywordsEn"))]:
        if term:
            values.append((term, "en"))
    deduped: list[tuple[str, str]] = []
    seen: set[str] = set()
    for term, language_code in values:
        clean = truncate(term, MAX_NVARCHAR_255)
        if not clean:
            continue
        key = clean.casefold()
        if key not in seen:
            seen.add(key)
            deduped.append((clean, language_code))
    return deduped


def find_existing_disease(cursor: pyodbc.Cursor, row: dict[str, str]) -> int | None:
    disease_code = normalize_text(row.get("DiseaseCode"))
    disease_name_vi = normalize_text(row.get("DiseaseNameVi"))
    disease_name_en = normalize_text(row.get("DiseaseNameEn"))

    if disease_code:
        disease_id = fetch_one_id(
            cursor,
            "SELECT DiseaseId FROM dbo.Diseases WHERE DiseaseCode = ?",
            disease_code,
        )
        if disease_id is not None:
            return disease_id

    for disease_name in unique_nonempty([disease_name_vi, disease_name_en], MAX_NVARCHAR_255):
        disease_id = fetch_one_id(
            cursor,
            """
            SELECT TOP 1 DiseaseId
            FROM dbo.Diseases
            WHERE UPPER(DiseaseName) = UPPER(?)
            ORDER BY DiseaseId
            """,
            disease_name,
        )
        if disease_id is not None:
            return disease_id

        disease_id = fetch_one_id(
            cursor,
            """
            SELECT TOP 1 DiseaseId
            FROM dbo.DiseaseSynonyms
            WHERE UPPER(SynonymName) = UPPER(?)
            ORDER BY DiseaseId
            """,
            disease_name,
        )
        if disease_id is not None:
            return disease_id
    return None


def insert_disease(
    cursor: pyodbc.Cursor,
    row: dict[str, str],
    disease_group_id: int | None,
    confidence_level_id: int,
    review_status_id: int,
    user_id: int,
) -> int:
    disease_code = truncate(row["DiseaseCode"], MAX_NVARCHAR_50)
    disease_name = truncate(row["DiseaseNameVi"], MAX_NVARCHAR_255)
    if not disease_code or not disease_name:
        raise RuntimeError(f"Seed row is missing required disease code/name: {row}")
    cursor.execute(
        """
        INSERT INTO dbo.Diseases
            (DiseaseCode, DiseaseName, DiseaseGroupId, Description,
             ConfidenceLevelId, ReviewStatusId, CreatedBy, IsDeleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        disease_code,
        disease_name,
        disease_group_id,
        disease_description(row),
        confidence_level_id,
        review_status_id,
        user_id,
    )
    return require_lookup_id(
        cursor,
        "SELECT DiseaseId FROM dbo.Diseases WHERE DiseaseCode = ?",
        (disease_code,),
        f"dbo.Diseases(DiseaseCode={disease_code!r})",
    )


def update_existing_disease(
    cursor: pyodbc.Cursor,
    disease_id: int,
    row: dict[str, str],
    disease_group_id: int | None,
    confidence_level_id: int,
    review_status_id: int,
    user_id: int,
) -> None:
    disease_name_vi = truncate(row.get("DiseaseNameVi"), MAX_NVARCHAR_255)
    disease_name_en = truncate(row.get("DiseaseNameEn"), MAX_NVARCHAR_255)
    cursor.execute(
        """
        UPDATE dbo.Diseases
        SET DiseaseName = CASE
                WHEN ? IS NOT NULL
                 AND ? IS NOT NULL
                 AND UPPER(DiseaseName) = UPPER(?)
                 AND ReviewStatusId IN (
                    SELECT ReviewStatusId FROM dbo.ReviewStatuses
                    WHERE StatusCode IN ('PENDING', 'NEED_REVIEW')
                 )
                THEN ? ELSE DiseaseName END,
            DiseaseGroupId = COALESCE(DiseaseGroupId, ?),
            Description = CASE
                WHEN NULLIF(LTRIM(RTRIM(ISNULL(Description, ''))), '') IS NULL
                THEN ? ELSE Description END,
            ConfidenceLevelId = COALESCE(ConfidenceLevelId, ?),
            ReviewStatusId = CASE
                WHEN ReviewStatusId IN (
                    SELECT ReviewStatusId FROM dbo.ReviewStatuses
                    WHERE StatusCode IN ('PENDING', 'NEED_REVIEW')
                )
                THEN ? ELSE ReviewStatusId END,
            UpdatedBy = ?,
            UpdatedAt = SYSUTCDATETIME()
        WHERE DiseaseId = ?
        """,
        disease_name_vi,
        disease_name_en,
        disease_name_en,
        disease_name_vi,
        disease_group_id,
        disease_description(row),
        confidence_level_id,
        review_status_id,
        user_id,
        disease_id,
    )


def upsert_disease_source(
    cursor: pyodbc.Cursor,
    disease_id: int,
    data_source_id: int,
) -> bool:
    exists = scalar(
        cursor,
        """
        SELECT 1
        FROM dbo.DiseaseSources
        WHERE DiseaseId = ? AND DataSourceId = ?
        """,
        disease_id,
        data_source_id,
    )
    if exists is not None:
        return False
    cursor.execute(
        """
        INSERT INTO dbo.DiseaseSources(DiseaseId, DataSourceId, SourceNote)
        VALUES (?, ?, ?)
        """,
        disease_id,
        data_source_id,
        "Imported from local curated common Vietnam disease seed.",
    )
    return True


def upsert_synonyms(cursor: pyodbc.Cursor, disease_id: int, row: dict[str, str]) -> int:
    inserted = 0
    for synonym, language_code in synonym_terms(row):
        exists = scalar(
            cursor,
            """
            SELECT 1
            FROM dbo.DiseaseSynonyms
            WHERE DiseaseId = ? AND UPPER(SynonymName) = UPPER(?)
            """,
            disease_id,
            synonym,
        )
        if exists is not None:
            continue
        cursor.execute(
            """
            INSERT INTO dbo.DiseaseSynonyms(DiseaseId, SynonymName, LanguageCode)
            VALUES (?, ?, ?)
            """,
            disease_id,
            synonym,
            language_code,
        )
        inserted += 1
    return inserted


def upsert_external_codes(
    cursor: pyodbc.Cursor,
    disease_id: int,
    data_source_id: int,
    codes: Iterable[str],
    source_label: str,
) -> int:
    inserted = 0
    for code in unique_nonempty(codes, MAX_NVARCHAR_100):
        existing = cursor.execute(
            """
            SELECT DiseaseId
            FROM dbo.DiseaseExternalCodes
            WHERE DataSourceId = ? AND ExternalCode = ?
            """,
            data_source_id,
            code,
        ).fetchone()
        if existing is not None:
            existing_disease_id = int(existing[0])
            if existing_disease_id != disease_id:
                LOGGER.warning(
                    "Skipping %s code %s for disease_id=%s because it already belongs to disease_id=%s.",
                    source_label,
                    code,
                    disease_id,
                    existing_disease_id,
                )
            continue
        cursor.execute(
            """
            INSERT INTO dbo.DiseaseExternalCodes(DiseaseId, DataSourceId, ExternalCode)
            VALUES (?, ?, ?)
            """,
            disease_id,
            data_source_id,
            code,
        )
        inserted += 1
    return inserted


def upsert_disease_feature(
    cursor: pyodbc.Cursor,
    disease_id: int,
    feature_definition_id: int,
    row: dict[str, str],
) -> bool:
    payload = {
        "source": LOCAL_SOURCE_CODE,
        "disease_code": row.get("DiseaseCode"),
        "disease_name_vi": row.get("DiseaseNameVi"),
        "disease_name_en": row.get("DiseaseNameEn"),
        "group_code": row.get("GroupCode"),
        "icd10": split_terms(row.get("ICD10")),
        "mesh_or_umls": split_terms(row.get("MeSHOrUMLS")),
        "keywords_vi": split_terms(row.get("KeywordsVi")),
        "keywords_en": split_terms(row.get("KeywordsEn")),
    }
    feature_value = "; ".join(
        unique_nonempty(
            [
                row.get("DiseaseNameVi"),
                row.get("DiseaseNameEn"),
                row.get("KeywordsVi"),
                row.get("KeywordsEn"),
            ]
        )
    )
    feature_json = json_dumps(payload)
    exists = scalar(
        cursor,
        """
        SELECT 1
        FROM dbo.DiseaseFeatureValues
        WHERE DiseaseId = ? AND FeatureDefinitionId = ?
        """,
        disease_id,
        feature_definition_id,
    )
    if exists is None:
        cursor.execute(
            """
            INSERT INTO dbo.DiseaseFeatureValues
                (DiseaseId, FeatureDefinitionId, FeatureValue, FeatureVectorJson)
            VALUES (?, ?, ?, ?)
            """,
            disease_id,
            feature_definition_id,
            feature_value,
            feature_json,
        )
        return True

    cursor.execute(
        """
        UPDATE dbo.DiseaseFeatureValues
        SET FeatureValue = ?, FeatureVectorJson = ?
        WHERE DiseaseId = ? AND FeatureDefinitionId = ?
        """,
        feature_value,
        feature_json,
        disease_id,
        feature_definition_id,
    )
    return False


def import_common_diseases() -> dict[str, int]:
    configure_logging()
    rows = read_seed_rows()
    summary = {
        "seed_rows": len(rows),
        "diseases_inserted": 0,
        "diseases_updated": 0,
        "synonyms_inserted": 0,
        "external_codes_inserted": 0,
        "sources_inserted": 0,
        "features_inserted": 0,
        "features_updated": 0,
    }

    conn = connect_sql_server()
    try:
        cursor = conn.cursor()
        local_source_id = ensure_data_source(
            cursor,
            LOCAL_SOURCE_CODE,
            "Local curated disease seed",
            "Local seed file: data/seed/common_vietnam_diseases.csv",
        )
        icd10_source_id = ensure_data_source(
            cursor,
            ICD10_SOURCE_CODE,
            "ICD-10",
            "International Classification of Diseases 10th Revision code from local seed.",
        )
        mesh_umls_source_id = ensure_data_source(
            cursor,
            MESH_UMLS_SOURCE_CODE,
            "MeSH or UMLS",
            "Optional MeSH or UMLS identifier from local seed.",
        )
        confidence_level_id = ensure_confidence_level(
            cursor,
            "MEDIUM",
            "Trung bình",
            0.5000,
            0.6999,
        )
        review_status_id = ensure_review_status(cursor, "NEED_REVIEW", "Cần xem lại")
        user_id = ensure_system_user(cursor)
        feature_definition_id = ensure_feature_definition(cursor)

        for row in rows:
            group_code = normalize_text(row.get("GroupCode")) or "OTHER"
            disease_group_id = ensure_disease_group(cursor, group_code)
            disease_id = find_existing_disease(cursor, row)
            if disease_id is None:
                disease_id = insert_disease(
                    cursor,
                    row,
                    disease_group_id,
                    confidence_level_id,
                    review_status_id,
                    user_id,
                )
                summary["diseases_inserted"] += 1
            else:
                update_existing_disease(
                    cursor,
                    disease_id,
                    row,
                    disease_group_id,
                    confidence_level_id,
                    review_status_id,
                    user_id,
                )
                summary["diseases_updated"] += 1

            summary["synonyms_inserted"] += upsert_synonyms(cursor, disease_id, row)
            if upsert_disease_source(cursor, disease_id, local_source_id):
                summary["sources_inserted"] += 1
            summary["external_codes_inserted"] += upsert_external_codes(
                cursor,
                disease_id,
                icd10_source_id,
                split_terms(row.get("ICD10")),
                "ICD-10",
            )
            summary["external_codes_inserted"] += upsert_external_codes(
                cursor,
                disease_id,
                mesh_umls_source_id,
                split_terms(row.get("MeSHOrUMLS")),
                "MeSH/UMLS",
            )
            if upsert_disease_feature(cursor, disease_id, feature_definition_id, row):
                summary["features_inserted"] += 1
            else:
                summary["features_updated"] += 1

        conn.commit()
    except Exception:
        conn.rollback()
        LOGGER.exception("Disease import failed. Transaction rolled back.")
        raise
    finally:
        conn.close()

    LOGGER.info("Disease import summary: %s", summary)
    return summary


def main() -> None:
    summary = import_common_diseases()
    print("Imported local common disease seed.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
