from __future__ import annotations

import csv
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

import pyodbc

from config import BASE_DIR, LOG_DIR, SQLSERVER_CONNECTION_STRING


CANDIDATE_PATH = BASE_DIR / "data" / "seed" / "candidate_diseases_from_drugs.csv"
DICTIONARY_PATH = BASE_DIR / "data" / "seed" / "disease_vietnamese_dictionary.csv"
LOG_PATH = LOG_DIR / "import_candidate_diseases_local.log"

SYSTEM_EMAIL = "system@drug-disease-ml.local"
SYSTEM_FULL_NAME = "System Import Bot"
SYSTEM_USER_CODE = "U-SYSTEM-IMPORT"

SOURCE_CODE = "LOCAL_DRUG_TEXT_MINING"
SOURCE_NAME = "Local drug text disease mining"
FEATURE_CODE = "LOCAL_DRUG_TEXT_MINING_PROFILE"

IMPORT_ACTIONS = {"APPROVED", "IMPORT"}
CSV_COLUMNS = [
    "CandidateDiseaseCode",
    "CandidateDiseaseNameEn",
    "CandidateDiseaseNameVi",
    "SuggestedGroupCode",
    "MatchedKeyword",
    "EvidenceField",
    "EvidenceCount",
    "SampleDrugNames",
    "EvidenceSnippet",
    "Action",
]

DICTIONARY_COLUMNS = [
    "DiseaseNameEn",
    "DiseaseNameVi",
    "KeywordsVi",
    "GroupCode",
]

GROUP_NAMES = {
    "CARDIO": "Tim mạch",
    "METABOLIC": "Chuyển hóa nội tiết",
    "RESPIRATORY": "Hô hấp",
    "INFECTIOUS": "Truyền nhiễm",
    "DIGESTIVE": "Tiêu hóa",
    "UROLOGY": "Tiết niệu",
    "RENAL_URO": "Thận tiết niệu",
    "NEURO": "Thần kinh",
    "MENTAL": "Sức khỏe tâm thần",
    "CANCER": "Ung thư",
    "DERMATOLOGY": "Da liễu",
    "DERM_ALLERGY": "Da liễu dị ứng",
    "AUTOIMMUNE": "Tự miễn",
    "MUSCULOSKELETAL": "Cơ xương khớp",
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


def clean_whitespace(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = text.replace("’", "'")
    text = re.sub(r"[^0-9a-zA-ZÀ-ỹ'+-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -+")


def normalize_name_for_compare(value: str) -> str:
    text = normalize_text(value)
    aliases = {
        "copd": "chronic obstructive pulmonary disease",
        "gerd": "gastroesophageal reflux disease",
        "gastro oesophageal reflux disease": "gastroesophageal reflux disease",
        "hiv": "hiv infection",
        "uti": "urinary tract infection",
        "bph": "benign prostatic hyperplasia",
        "pcos": "polycystic ovary syndrome",
    }
    return aliases.get(text, text)


def truncate(value: Any, max_len: int) -> str | None:
    text = clean_whitespace(value)
    if not text:
        return None
    return text[:max_len]


def split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    return unique_nonempty(part.strip() for part in value.split(";"))


def load_vietnamese_dictionary(
    path: Path = DICTIONARY_PATH,
) -> dict[str, dict[str, Any]]:
    if not path.exists():
        LOGGER.warning("Vietnamese disease dictionary not found: %s", path)
        return {}

    dictionary: dict[str, dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != DICTIONARY_COLUMNS:
            raise RuntimeError(
                "Unexpected Vietnamese disease dictionary columns. Expected "
                f"{DICTIONARY_COLUMNS}, got {reader.fieldnames}."
            )
        for row in reader:
            name_en = clean_whitespace(row.get("DiseaseNameEn"))
            name_vi = clean_whitespace(row.get("DiseaseNameVi"))
            if not name_en or not name_vi:
                continue
            mapping = {
                "name_vi": name_vi,
                "keywords_vi": split_terms(row.get("KeywordsVi")),
                "group_code": clean_whitespace(row.get("GroupCode")).upper()
                or "OTHER",
            }
            for key in {
                normalize_text(name_en),
                normalize_name_for_compare(name_en),
            }:
                dictionary.setdefault(key, mapping)
    return dictionary


def find_vietnamese_mapping(
    dictionary: dict[str, dict[str, Any]],
    disease_name_en: str,
) -> dict[str, Any] | None:
    for key in {
        normalize_text(disease_name_en),
        normalize_name_for_compare(disease_name_en),
    }:
        mapping = dictionary.get(key)
        if mapping is not None:
            return mapping
    return None


def enrich_row_with_dictionary(
    row: dict[str, str],
    dictionary: dict[str, dict[str, Any]],
) -> dict[str, str]:
    enriched = dict(row)
    mapping = find_vietnamese_mapping(
        dictionary,
        clean_whitespace(enriched.get("CandidateDiseaseNameEn")),
    )
    if mapping is None:
        return enriched
    if not clean_whitespace(enriched.get("CandidateDiseaseNameVi")):
        enriched["CandidateDiseaseNameVi"] = mapping["name_vi"]
    if not clean_whitespace(enriched.get("SuggestedGroupCode")):
        enriched["SuggestedGroupCode"] = mapping["group_code"]
    enriched["_KeywordsVi"] = "; ".join(mapping["keywords_vi"])
    return enriched


def unique_nonempty(values: Iterable[Any], max_len: int | None = None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = clean_whitespace(value)
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


def ensure_data_source(cursor: pyodbc.Cursor) -> int:
    lookup_sql = "SELECT DataSourceId FROM dbo.DataSources WHERE SourceCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, SOURCE_CODE)
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.DataSources(SourceCode, SourceName, Description)
        VALUES (?, ?, ?)
        """,
        SOURCE_CODE,
        SOURCE_NAME,
        (
            "Disease candidates reviewed from phrases mined locally from existing "
            "dbo.Drugs label text. No external API source."
        ),
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (SOURCE_CODE,),
        f"dbo.DataSources(SourceCode={SOURCE_CODE!r})",
    )


def ensure_review_status(cursor: pyodbc.Cursor) -> int:
    lookup_sql = "SELECT ReviewStatusId FROM dbo.ReviewStatuses WHERE StatusCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, "NEED_REVIEW")
    if existing is not None:
        return existing
    cursor.execute(
        "INSERT INTO dbo.ReviewStatuses(StatusCode, StatusName) VALUES (?, ?)",
        "NEED_REVIEW",
        "Cần xem lại",
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        ("NEED_REVIEW",),
        "dbo.ReviewStatuses(StatusCode='NEED_REVIEW')",
    )


def ensure_confidence_level(cursor: pyodbc.Cursor) -> int:
    lookup_sql = "SELECT ConfidenceLevelId FROM dbo.ConfidenceLevels WHERE LevelCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, "LOW")
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.ConfidenceLevels(LevelCode, LevelName, MinScore, MaxScore)
        VALUES (?, ?, 0.0000, 0.4999)
        """,
        "LOW",
        "Thấp",
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        ("LOW",),
        "dbo.ConfidenceLevels(LevelCode='LOW')",
    )


def ensure_group(cursor: pyodbc.Cursor, group_code: str | None) -> int | None:
    group_code = clean_whitespace(group_code).upper() or "OTHER"
    lookup_sql = "SELECT DiseaseGroupId FROM dbo.DiseaseGroups WHERE GroupCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, group_code)
    if existing is not None:
        return existing
    cursor.execute(
        "INSERT INTO dbo.DiseaseGroups(GroupCode, GroupName) VALUES (?, ?)",
        group_code,
        GROUP_NAMES.get(group_code, group_code.replace("_", " ").title()),
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
    existing = fetch_one_id(cursor, lookup_sql, FEATURE_CODE)
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.FeatureDefinitions
            (EntityType, FeatureCode, FeatureName, DataType, EncodingMethod, Description)
        VALUES ('DISEASE', ?, ?, 'JSON', 'LOCAL_TEXT_MINING', ?)
        """,
        FEATURE_CODE,
        "Local drug text mining profile",
        "Candidate disease metadata mined from existing dbo.Drugs text and manually reviewed through CSV.",
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (FEATURE_CODE,),
        f"dbo.FeatureDefinitions(EntityType='DISEASE', FeatureCode={FEATURE_CODE!r})",
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


def read_candidate_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Candidate CSV not found: {path}. Run extract_candidate_diseases_from_drug_text.py first."
        )
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != CSV_COLUMNS:
            raise RuntimeError(
                f"Unexpected candidate CSV columns. Expected {CSV_COLUMNS}, got {reader.fieldnames}."
            )
        return [dict(row) for row in reader]


def approved_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if clean_whitespace(row.get("Action")).upper() in IMPORT_ACTIONS
    ]


def disease_name(row: dict[str, str]) -> str:
    return (
        clean_whitespace(row.get("CandidateDiseaseNameVi"))
        or clean_whitespace(row.get("CandidateDiseaseNameEn"))
    )


def find_existing_disease(cursor: pyodbc.Cursor, row: dict[str, str]) -> int | None:
    candidate_code = clean_whitespace(row.get("CandidateDiseaseCode"))
    name_en = clean_whitespace(row.get("CandidateDiseaseNameEn"))
    name_vi = clean_whitespace(row.get("CandidateDiseaseNameVi"))
    keywords_vi = split_terms(row.get("_KeywordsVi"))

    if candidate_code:
        disease_id = fetch_one_id(
            cursor,
            "SELECT DiseaseId FROM dbo.Diseases WHERE DiseaseCode = ?",
            candidate_code,
        )
        if disease_id is not None:
            return disease_id

    for name in unique_nonempty([name_vi, name_en, *keywords_vi]):
        disease_id = fetch_one_id(
            cursor,
            """
            SELECT TOP 1 DiseaseId
            FROM dbo.Diseases
            WHERE UPPER(DiseaseName) = UPPER(?)
            ORDER BY DiseaseId
            """,
            name,
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
            name,
        )
        if disease_id is not None:
            return disease_id
    return None


def description(row: dict[str, str]) -> str:
    snippet = clean_whitespace(row.get("EvidenceSnippet"))
    evidence_count = clean_whitespace(row.get("EvidenceCount"))
    return (
        "Candidate disease mined from existing imported drug label text and approved "
        f"for local import. EvidenceCount={evidence_count}. "
        f"Sample evidence: {snippet[:700]}"
    )


def insert_disease(
    cursor: pyodbc.Cursor,
    row: dict[str, str],
    group_id: int | None,
    confidence_level_id: int,
    review_status_id: int,
    user_id: int,
) -> int:
    candidate_code = truncate(row.get("CandidateDiseaseCode"), 50)
    name = truncate(disease_name(row), 255)
    if not candidate_code or not name:
        raise RuntimeError(f"Approved candidate is missing code/name: {row}")
    cursor.execute(
        """
        INSERT INTO dbo.Diseases
            (DiseaseCode, DiseaseName, DiseaseGroupId, Description,
             ConfidenceLevelId, ReviewStatusId, CreatedBy, IsDeleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """,
        candidate_code,
        name,
        group_id,
        description(row),
        confidence_level_id,
        review_status_id,
        user_id,
    )
    return require_lookup_id(
        cursor,
        "SELECT DiseaseId FROM dbo.Diseases WHERE DiseaseCode = ?",
        (candidate_code,),
        f"dbo.Diseases(DiseaseCode={candidate_code!r})",
    )


def update_disease(
    cursor: pyodbc.Cursor,
    disease_id: int,
    row: dict[str, str],
    group_id: int | None,
    confidence_level_id: int,
    review_status_id: int,
    user_id: int,
) -> None:
    display_name = truncate(disease_name(row), 255)
    name_en = truncate(row.get("CandidateDiseaseNameEn"), 255)
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
        display_name,
        name_en,
        name_en,
        display_name,
        group_id,
        description(row),
        confidence_level_id,
        review_status_id,
        user_id,
        disease_id,
    )


def synonym_terms(row: dict[str, str]) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    for term in [
        row.get("CandidateDiseaseNameVi"),
        *split_terms(row.get("_KeywordsVi")),
    ]:
        if term:
            values.append((term, "vi"))
    for term in [
        row.get("CandidateDiseaseNameEn"),
        *split_terms(row.get("MatchedKeyword")),
    ]:
        if term:
            values.append((term, "en"))

    deduped: list[tuple[str, str]] = []
    seen: set[str] = set()
    for term, language_code in values:
        clean = truncate(term, 255)
        if not clean:
            continue
        key = clean.casefold()
        if key in seen:
            continue
        seen.add(key)
        deduped.append((clean, language_code))
    return deduped


def synonym_values(row: dict[str, str]) -> list[str]:
    return [synonym for synonym, _language_code in synonym_terms(row)]


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


def upsert_source(cursor: pyodbc.Cursor, disease_id: int, data_source_id: int) -> bool:
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
        "Imported from manually reviewed local drug text mining candidates.",
    )
    return True


def upsert_external_code(
    cursor: pyodbc.Cursor,
    disease_id: int,
    data_source_id: int,
    candidate_code: str,
) -> bool:
    candidate_code = clean_whitespace(candidate_code)
    if not candidate_code:
        return False
    existing = cursor.execute(
        """
        SELECT DiseaseId
        FROM dbo.DiseaseExternalCodes
        WHERE DataSourceId = ? AND ExternalCode = ?
        """,
        data_source_id,
        candidate_code,
    ).fetchone()
    if existing is not None:
        existing_disease_id = int(existing[0])
        if existing_disease_id != disease_id:
            LOGGER.warning(
                "Candidate code %s already belongs to DiseaseId=%s; skipping external code for DiseaseId=%s.",
                candidate_code,
                existing_disease_id,
                disease_id,
            )
        return False
    cursor.execute(
        """
        INSERT INTO dbo.DiseaseExternalCodes(DiseaseId, DataSourceId, ExternalCode)
        VALUES (?, ?, ?)
        """,
        disease_id,
        data_source_id,
        candidate_code,
    )
    return True


def upsert_feature(
    cursor: pyodbc.Cursor,
    disease_id: int,
    feature_definition_id: int,
    row: dict[str, str],
) -> bool:
    payload = {
        "source": SOURCE_CODE,
        "candidate_code": row.get("CandidateDiseaseCode"),
        "candidate_name_en": row.get("CandidateDiseaseNameEn"),
        "candidate_name_vi": row.get("CandidateDiseaseNameVi"),
        "keywords_vi": split_terms(row.get("_KeywordsVi")),
        "suggested_group_code": row.get("SuggestedGroupCode"),
        "matched_keywords": split_terms(row.get("MatchedKeyword")),
        "evidence_fields": split_terms(row.get("EvidenceField")),
        "evidence_count": clean_whitespace(row.get("EvidenceCount")),
        "sample_drug_names": split_terms(row.get("SampleDrugNames")),
        "evidence_snippet": clean_whitespace(row.get("EvidenceSnippet")),
        "review_action": clean_whitespace(row.get("Action")).upper(),
    }
    feature_value = "; ".join(synonym_values(row))
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
            json_dumps(payload),
        )
        return True
    cursor.execute(
        """
        UPDATE dbo.DiseaseFeatureValues
        SET FeatureValue = ?, FeatureVectorJson = ?
        WHERE DiseaseId = ? AND FeatureDefinitionId = ?
        """,
        feature_value,
        json_dumps(payload),
        disease_id,
        feature_definition_id,
    )
    return False


def import_candidate_diseases(path: Path = CANDIDATE_PATH) -> dict[str, int]:
    configure_logging()
    rows = read_candidate_rows(path)
    approved = approved_rows(rows)
    summary = {
        "candidate_rows": len(rows),
        "approved_rows": len(approved),
        "diseases_inserted": 0,
        "diseases_updated": 0,
        "synonyms_inserted": 0,
        "sources_inserted": 0,
        "external_codes_inserted": 0,
        "features_inserted": 0,
        "features_updated": 0,
    }

    conn = connect_sql_server()
    try:
        cursor = conn.cursor()
        data_source_id = ensure_data_source(cursor)
        confidence_level_id = ensure_confidence_level(cursor)
        review_status_id = ensure_review_status(cursor)
        feature_definition_id = ensure_feature_definition(cursor)
        user_id = ensure_system_user(cursor)
        dictionary = load_vietnamese_dictionary()

        for raw_row in approved:
            row = enrich_row_with_dictionary(raw_row, dictionary)
            group_id = ensure_group(cursor, row.get("SuggestedGroupCode"))
            disease_id = find_existing_disease(cursor, row)
            if disease_id is None:
                disease_id = insert_disease(
                    cursor,
                    row,
                    group_id,
                    confidence_level_id,
                    review_status_id,
                    user_id,
                )
                summary["diseases_inserted"] += 1
            else:
                update_disease(
                    cursor,
                    disease_id,
                    row,
                    group_id,
                    confidence_level_id,
                    review_status_id,
                    user_id,
                )
                summary["diseases_updated"] += 1

            summary["synonyms_inserted"] += upsert_synonyms(cursor, disease_id, row)
            if upsert_source(cursor, disease_id, data_source_id):
                summary["sources_inserted"] += 1
            if upsert_external_code(
                cursor,
                disease_id,
                data_source_id,
                clean_whitespace(row.get("CandidateDiseaseCode")),
            ):
                summary["external_codes_inserted"] += 1
            if upsert_feature(cursor, disease_id, feature_definition_id, row):
                summary["features_inserted"] += 1
            else:
                summary["features_updated"] += 1

        conn.commit()
    except Exception:
        conn.rollback()
        LOGGER.exception("Candidate disease import failed. Transaction rolled back.")
        raise
    finally:
        conn.close()

    LOGGER.info("Candidate disease import summary: %s", summary)
    return summary


def main() -> None:
    summary = import_candidate_diseases()
    print("Imported approved local candidate diseases.")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
