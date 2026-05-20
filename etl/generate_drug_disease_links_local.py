from __future__ import annotations

import hashlib
import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Any

import pyodbc

from config import LOG_DIR, SQLSERVER_CONNECTION_STRING
from create_training_labels_from_links import create_training_labels


LOG_PATH = LOG_DIR / "generate_drug_disease_links_local.log"

SYSTEM_EMAIL = "system@drug-disease-ml.local"
SYSTEM_FULL_NAME = "System Import Bot"
SYSTEM_USER_CODE = "U-SYSTEM-IMPORT"

EVIDENCE_SOURCE_CODE = "EXISTING_DRUG_LABEL_TEXT"
EVIDENCE_SOURCE_NAME = "Existing imported drug label text"

AUTO_EVIDENCE_STATUS_CODE = "AUTO_EXTRACTED"
REVIEW_STATUS_CODE = "NEED_REVIEW"
CONFIDENCE_LEVEL_CODE = "MEDIUM"

FIELD_LINK_RULES = {
    "KnownIndications": {
        "link_type_candidates": ["INDICATION", "THERAPEUTIC_INDICATION"],
        "fallback_create_code": "INDICATION",
        "fallback_create_name": "Chỉ định điều trị",
        "source_score": 0.6500,
        "formation_basis": "Keyword match in existing KnownIndications label text.",
    },
    "ContraindicationsInteractions": {
        "link_type_candidates": ["CONTRAINDICATION"],
        "fallback_create_code": "CONTRAINDICATION",
        "fallback_create_name": "Chống chỉ định",
        "source_score": 0.6000,
        "formation_basis": "Keyword match in existing ContraindicationsInteractions label text.",
    },
    "SideEffectsWarnings": {
        "link_type_candidates": ["SIDE_EFFECT", "ADVERSE_EFFECT", "SAFETY_WARNING"],
        "fallback_create_code": "SIDE_EFFECT",
        "fallback_create_name": "Tác dụng phụ",
        "source_score": 0.5500,
        "formation_basis": "Keyword match in existing SideEffectsWarnings label text.",
    },
    "MechanismOfAction": {
        "link_type_candidates": ["MECHANISTIC_RELATED", "RESEARCH_RELATED"],
        "fallback_create_code": None,
        "fallback_create_name": None,
        "source_score": 0.4500,
        "formation_basis": "Keyword match in existing MechanismOfAction text.",
    },
}

GENERIC_KEYWORDS = {
    "condition",
    "conditions",
    "disease",
    "diseases",
    "disorder",
    "disorders",
    "syndrome",
    "infection",
    "infections",
    "infectious disease",
    "cancer",
    "carcinoma",
    "tumor",
    "tumour",
    "malignancy",
}

SAFE_SHORT_KEYWORDS = {
    "flu",
    "hiv",
    "hbv",
    "hcv",
    "uti",
    "copd",
    "gerd",
    "ckd",
    "bph",
    "pcos",
}


@dataclass(frozen=True)
class DrugText:
    drug_id: int
    drug_code: str
    active_name: str
    trade_name: str | None
    fields: dict[str, str]


@dataclass(frozen=True)
class DiseaseKeywords:
    disease_id: int
    disease_code: str
    disease_name: str
    group_code: str | None
    keywords: list[str]


@dataclass(frozen=True)
class MatchResult:
    field_name: str
    link_type_code: str
    link_type_id: int
    keyword: str
    snippet: str
    start: int
    source_score: float
    formation_basis: str


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


def clean_whitespace(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalize_for_match(value: str) -> str:
    text = unicodedata.normalize("NFKC", value).casefold()
    text = text.replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def ensure_data_source(cursor: pyodbc.Cursor) -> int:
    lookup_sql = "SELECT DataSourceId FROM dbo.DataSources WHERE SourceCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, EVIDENCE_SOURCE_CODE)
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.DataSources(SourceCode, SourceName, Description)
        VALUES (?, ?, ?)
        """,
        EVIDENCE_SOURCE_CODE,
        EVIDENCE_SOURCE_NAME,
        "Local source representing text already imported into dbo.Drugs fields.",
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (EVIDENCE_SOURCE_CODE,),
        f"dbo.DataSources(SourceCode={EVIDENCE_SOURCE_CODE!r})",
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


def ensure_review_status(cursor: pyodbc.Cursor) -> int:
    lookup_sql = "SELECT ReviewStatusId FROM dbo.ReviewStatuses WHERE StatusCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, REVIEW_STATUS_CODE)
    if existing is not None:
        return existing
    cursor.execute(
        "INSERT INTO dbo.ReviewStatuses(StatusCode, StatusName) VALUES (?, ?)",
        REVIEW_STATUS_CODE,
        "Cần xem lại",
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (REVIEW_STATUS_CODE,),
        f"dbo.ReviewStatuses(StatusCode={REVIEW_STATUS_CODE!r})",
    )


def ensure_confidence_level(cursor: pyodbc.Cursor) -> int:
    lookup_sql = "SELECT ConfidenceLevelId FROM dbo.ConfidenceLevels WHERE LevelCode = ?"
    existing = fetch_one_id(cursor, lookup_sql, CONFIDENCE_LEVEL_CODE)
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.ConfidenceLevels(LevelCode, LevelName, MinScore, MaxScore)
        VALUES (?, ?, 0.5000, 0.6999)
        """,
        CONFIDENCE_LEVEL_CODE,
        "Trung bình",
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (CONFIDENCE_LEVEL_CODE,),
        f"dbo.ConfidenceLevels(LevelCode={CONFIDENCE_LEVEL_CODE!r})",
    )


def ensure_evidence_status(cursor: pyodbc.Cursor) -> int:
    lookup_sql = """
        SELECT EvidenceStatusId
        FROM dbo.EvidenceStatuses
        WHERE EvidenceStatusCode = ?
    """
    existing = fetch_one_id(cursor, lookup_sql, AUTO_EVIDENCE_STATUS_CODE)
    if existing is not None:
        return existing
    cursor.execute(
        """
        INSERT INTO dbo.EvidenceStatuses(EvidenceStatusCode, EvidenceStatusName)
        VALUES (?, ?)
        """,
        AUTO_EVIDENCE_STATUS_CODE,
        "Auto extracted from existing label text",
    )
    return require_lookup_id(
        cursor,
        lookup_sql,
        (AUTO_EVIDENCE_STATUS_CODE,),
        f"dbo.EvidenceStatuses(EvidenceStatusCode={AUTO_EVIDENCE_STATUS_CODE!r})",
    )


def get_link_type_id(cursor: pyodbc.Cursor, code: str) -> int | None:
    return fetch_one_id(
        cursor,
        "SELECT LinkTypeId FROM dbo.LinkTypes WHERE LinkTypeCode = ?",
        code,
    )


def ensure_link_type(
    cursor: pyodbc.Cursor,
    candidate_codes: list[str],
    fallback_create_code: str | None,
    fallback_create_name: str | None,
) -> tuple[str, int] | None:
    for code in candidate_codes:
        link_type_id = get_link_type_id(cursor, code)
        if link_type_id is not None:
            return code, link_type_id

    if fallback_create_code is None or fallback_create_name is None:
        return None

    cursor.execute(
        """
        INSERT INTO dbo.LinkTypes(LinkTypeCode, LinkTypeName, Description)
        VALUES (?, ?, ?)
        """,
        fallback_create_code,
        fallback_create_name,
        "Created by local label-text extraction pipeline.",
    )
    link_type_id = require_lookup_id(
        cursor,
        "SELECT LinkTypeId FROM dbo.LinkTypes WHERE LinkTypeCode = ?",
        (fallback_create_code,),
        f"dbo.LinkTypes(LinkTypeCode={fallback_create_code!r})",
    )
    return fallback_create_code, link_type_id


def load_link_type_rules(cursor: pyodbc.Cursor) -> dict[str, dict[str, Any]]:
    resolved: dict[str, dict[str, Any]] = {}
    for field_name, rule in FIELD_LINK_RULES.items():
        link_type = ensure_link_type(
            cursor,
            list(rule["link_type_candidates"]),
            rule["fallback_create_code"],
            rule["fallback_create_name"],
        )
        if link_type is None:
            LOGGER.info(
                "Skipping %s matches because no mechanistic/research link type exists.",
                field_name,
            )
            continue
        link_type_code, link_type_id = link_type
        resolved[field_name] = {
            **rule,
            "link_type_code": link_type_code,
            "link_type_id": link_type_id,
        }
    return resolved


def load_drugs(cursor: pyodbc.Cursor) -> list[DrugText]:
    rows = cursor.execute(
        """
        SELECT
            DrugId,
            DrugCode,
            ActiveName,
            TradeName,
            KnownIndications,
            ContraindicationsInteractions,
            SideEffectsWarnings,
            MechanismOfAction
        FROM dbo.Drugs
        WHERE IsDeleted = 0
        ORDER BY DrugId
        """
    ).fetchall()
    drugs: list[DrugText] = []
    for row in rows:
        fields = {
            "KnownIndications": clean_whitespace(row.KnownIndications),
            "ContraindicationsInteractions": clean_whitespace(
                row.ContraindicationsInteractions
            ),
            "SideEffectsWarnings": clean_whitespace(row.SideEffectsWarnings),
            "MechanismOfAction": clean_whitespace(row.MechanismOfAction),
        }
        drugs.append(
            DrugText(
                drug_id=int(row.DrugId),
                drug_code=row.DrugCode,
                active_name=row.ActiveName,
                trade_name=row.TradeName,
                fields=fields,
            )
        )
    return drugs


def keyword_is_safe(
    disease_code: str,
    disease_name: str,
    group_code: str | None,
    keyword: str,
) -> tuple[bool, str | None]:
    normalized = normalize_for_match(keyword)
    if not normalized:
        return False, "empty"
    if len(normalized) < 4 and normalized not in SAFE_SHORT_KEYWORDS:
        return False, "too short"
    if normalized in GENERIC_KEYWORDS:
        return False, "generic"

    normalized_name = normalize_for_match(disease_name)
    if normalized == "pain" and normalized_name != "đau":
        return False, "pain is ambiguous outside Pain"
    if normalized in {"infection", "infections"}:
        return False, "infection is too generic"
    if group_code == "CANCER" and normalized in {"cancer", "carcinoma", "tumor", "tumour"}:
        return False, "cancer keyword lacks site"
    if disease_code not in {"DIS-VN-055", "DIS-VN-028"} and normalized == "pain":
        return False, "pain is too generic"
    return True, None


def load_diseases(cursor: pyodbc.Cursor) -> tuple[list[DiseaseKeywords], int]:
    disease_rows = cursor.execute(
        """
        SELECT
            d.DiseaseId,
            d.DiseaseCode,
            d.DiseaseName,
            dg.GroupCode
        FROM dbo.Diseases d
        LEFT JOIN dbo.DiseaseGroups dg ON dg.DiseaseGroupId = d.DiseaseGroupId
        WHERE d.IsDeleted = 0
        ORDER BY d.DiseaseId
        """
    ).fetchall()
    synonym_rows = cursor.execute(
        """
        SELECT DiseaseId, SynonymName
        FROM dbo.DiseaseSynonyms
        ORDER BY DiseaseId, SynonymName
        """
    ).fetchall()

    synonyms_by_disease: dict[int, list[str]] = {}
    for row in synonym_rows:
        synonyms_by_disease.setdefault(int(row.DiseaseId), []).append(row.SynonymName)

    weak_keyword_count = 0
    diseases: list[DiseaseKeywords] = []
    for row in disease_rows:
        raw_terms = [row.DiseaseName, *synonyms_by_disease.get(int(row.DiseaseId), [])]
        keywords: list[str] = []
        seen: set[str] = set()
        for term in raw_terms:
            clean = clean_whitespace(term)
            if not clean:
                continue
            safe, reason = keyword_is_safe(
                row.DiseaseCode,
                row.DiseaseName,
                row.GroupCode,
                clean,
            )
            if not safe:
                weak_keyword_count += 1
                LOGGER.debug(
                    "Skipping keyword %r for disease %s: %s",
                    clean,
                    row.DiseaseCode,
                    reason,
                )
                continue
            key = normalize_for_match(clean)
            if key in seen:
                continue
            seen.add(key)
            keywords.append(clean)

        keywords.sort(key=lambda value: len(normalize_for_match(value)), reverse=True)
        diseases.append(
            DiseaseKeywords(
                disease_id=int(row.DiseaseId),
                disease_code=row.DiseaseCode,
                disease_name=row.DiseaseName,
                group_code=row.GroupCode,
                keywords=keywords,
            )
        )
    return diseases, weak_keyword_count


def keyword_pattern(keyword: str) -> re.Pattern[str]:
    normalized = normalize_for_match(keyword)
    parts = [part for part in re.split(r"[\s\-_/.]+", normalized) if part]
    body = r"[\s\-_/.]+".join(re.escape(part) for part in parts)
    return re.compile(rf"(?<![\w]){body}(?![\w])", re.IGNORECASE | re.UNICODE)


def evidence_snippet(text: str, start: int, end: int, radius: int = 230) -> str:
    snippet_start = max(0, start - radius)
    snippet_end = min(len(text), end + radius)
    snippet = text[snippet_start:snippet_end]
    snippet = clean_whitespace(snippet)
    return snippet[:500]


def first_keyword_match(text: str, keywords: list[str]) -> tuple[str, str, int] | None:
    if not text:
        return None
    for keyword in keywords:
        pattern = keyword_pattern(keyword)
        match = pattern.search(text)
        if match is None:
            continue
        return (
            keyword,
            evidence_snippet(text, match.start(), match.end()),
            match.start(),
        )
    return None


def find_matches_for_pair(
    drug: DrugText,
    disease: DiseaseKeywords,
    link_type_rules: dict[str, dict[str, Any]],
) -> list[MatchResult]:
    if not disease.keywords:
        return []
    matches: list[MatchResult] = []
    for field_name in [
        "KnownIndications",
        "ContraindicationsInteractions",
        "SideEffectsWarnings",
        "MechanismOfAction",
    ]:
        rule = link_type_rules.get(field_name)
        if rule is None:
            continue
        field_text = drug.fields.get(field_name, "")
        match = first_keyword_match(field_text, disease.keywords)
        if match is None:
            continue
        keyword, snippet, start = match
        matches.append(
            MatchResult(
                field_name=field_name,
                link_type_code=rule["link_type_code"],
                link_type_id=int(rule["link_type_id"]),
                keyword=keyword,
                snippet=snippet,
                start=start,
                source_score=float(rule["source_score"]),
                formation_basis=rule["formation_basis"],
            )
        )
    return matches


def existing_link_id(
    cursor: pyodbc.Cursor,
    drug_id: int,
    disease_id: int,
    link_type_id: int,
) -> int | None:
    return fetch_one_id(
        cursor,
        """
        SELECT LinkId
        FROM dbo.DrugDiseaseLinks
        WHERE DrugId = ? AND DiseaseId = ? AND LinkTypeId = ?
        """,
        drug_id,
        disease_id,
        link_type_id,
    )


def deterministic_link_code(drug_id: int, disease_id: int, link_type_id: int) -> str:
    return f"LINK-AUTO-{drug_id:06d}-{disease_id:06d}-{link_type_id:03d}"


def insert_link(
    cursor: pyodbc.Cursor,
    drug: DrugText,
    disease: DiseaseKeywords,
    match: MatchResult,
    evidence_status_id: int,
    confidence_level_id: int,
    review_status_id: int,
    user_id: int,
) -> int:
    link_code = deterministic_link_code(
        drug.drug_id,
        disease.disease_id,
        match.link_type_id,
    )
    evidence_description = (
        f"Matched keyword {match.keyword!r} in dbo.Drugs.{match.field_name}. "
        f"Snippet: {match.snippet}"
    )
    processing_note = (
        "Auto-extracted from existing imported drug label text. "
        "Needs expert review."
    )
    cursor.execute(
        """
        INSERT INTO dbo.DrugDiseaseLinks
            (LinkCode, DrugId, DiseaseId, LinkTypeId, EvidenceStatusId,
             ConfidenceLevelId, SourceScore, FormationBasis, EvidenceDescription,
             ProcessingNote, ReviewStatusId, CreatedBy, IsDeleted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """,
        link_code,
        drug.drug_id,
        disease.disease_id,
        match.link_type_id,
        evidence_status_id,
        confidence_level_id,
        match.source_score,
        truncate(match.formation_basis, 500),
        evidence_description,
        truncate(processing_note, 1000),
        review_status_id,
        user_id,
    )
    return require_lookup_id(
        cursor,
        """
        SELECT LinkId
        FROM dbo.DrugDiseaseLinks
        WHERE DrugId = ? AND DiseaseId = ? AND LinkTypeId = ?
        """,
        (drug.drug_id, disease.disease_id, match.link_type_id),
        (
            "dbo.DrugDiseaseLinks"
            f"(DrugId={drug.drug_id}, DiseaseId={disease.disease_id}, "
            f"LinkTypeId={match.link_type_id})"
        ),
    )


def evidence_reference_code(
    drug_id: int,
    disease_id: int,
    link_type_code: str,
    field_name: str,
    keyword: str,
) -> str:
    raw = f"{drug_id}|{disease_id}|{link_type_code}|{field_name}|{keyword}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]
    return f"LOCALTXT-{digest}"


def insert_evidence_reference(
    cursor: pyodbc.Cursor,
    link_id: int,
    data_source_id: int,
    drug: DrugText,
    disease: DiseaseKeywords,
    match: MatchResult,
) -> bool:
    reference_code = evidence_reference_code(
        drug.drug_id,
        disease.disease_id,
        match.link_type_code,
        match.field_name,
        match.keyword,
    )
    exists = scalar(
        cursor,
        """
        SELECT 1
        FROM dbo.LinkEvidenceReferences
        WHERE LinkId = ? AND DataSourceId = ? AND ReferenceCode = ?
        """,
        link_id,
        data_source_id,
        reference_code,
    )
    if exists is not None:
        return False

    snippet = match.snippet.replace(";", ",")
    description = (
        f"Source={EVIDENCE_SOURCE_CODE}; "
        f"FieldName={match.field_name}; "
        f"MatchedKeyword={match.keyword}; "
        f"EvidenceSnippet={snippet}; "
        "Note=Auto-extracted from existing imported drug label text. "
        "Needs expert review."
    )
    cursor.execute(
        """
        INSERT INTO dbo.LinkEvidenceReferences
            (LinkId, DataSourceId, ReferenceType, ReferenceCode, Description)
        VALUES (?, ?, 'INTERNAL', ?, ?)
        """,
        link_id,
        data_source_id,
        reference_code,
        truncate(description, 1000),
    )
    return True


def generate_links() -> dict[str, int]:
    configure_logging()
    summary = {
        "drugs_loaded": 0,
        "diseases_loaded": 0,
        "links_created": 0,
        "links_skipped_duplicate": 0,
        "links_skipped_weak_or_ambiguous_keyword": 0,
        "mechanism_matches_skipped_no_link_type": 0,
        "evidence_references_created": 0,
        "training_labels_created": 0,
    }

    conn = connect_sql_server()
    try:
        cursor = conn.cursor()
        drugs = load_drugs(cursor)
        diseases, weak_keyword_count = load_diseases(cursor)
        summary["drugs_loaded"] = len(drugs)
        summary["diseases_loaded"] = len(diseases)
        summary["links_skipped_weak_or_ambiguous_keyword"] = weak_keyword_count

        print(f"Drugs loaded: {len(drugs)}")
        print(f"Diseases loaded: {len(diseases)}")

        if len(drugs) < 10:
            raise RuntimeError("Not enough drugs. Restore/import drug data first.")
        if len(diseases) < 10:
            raise RuntimeError(
                "Not enough diseases. Run import_common_diseases_local.py first."
            )

        evidence_source_id = ensure_data_source(cursor)
        user_id = ensure_system_user(cursor)
        review_status_id = ensure_review_status(cursor)
        confidence_level_id = ensure_confidence_level(cursor)
        evidence_status_id = ensure_evidence_status(cursor)
        link_type_rules = load_link_type_rules(cursor)
        if "MechanismOfAction" not in link_type_rules:
            summary["mechanism_matches_skipped_no_link_type"] = 0

        for drug in drugs:
            for disease in diseases:
                matches = find_matches_for_pair(drug, disease, link_type_rules)
                for match in matches:
                    existing = existing_link_id(
                        cursor,
                        drug.drug_id,
                        disease.disease_id,
                        match.link_type_id,
                    )
                    if existing is not None:
                        summary["links_skipped_duplicate"] += 1
                        continue

                    link_id = insert_link(
                        cursor,
                        drug,
                        disease,
                        match,
                        evidence_status_id,
                        confidence_level_id,
                        review_status_id,
                        user_id,
                    )
                    summary["links_created"] += 1
                    if insert_evidence_reference(
                        cursor,
                        link_id,
                        evidence_source_id,
                        drug,
                        disease,
                        match,
                    ):
                        summary["evidence_references_created"] += 1

        label_summary = create_training_labels(conn, commit=False)
        summary["training_labels_created"] = (
            label_summary["positive_labels_created"]
            + label_summary["negative_labels_created"]
        )
        conn.commit()
    except Exception:
        conn.rollback()
        LOGGER.exception("Drug-disease link generation failed. Transaction rolled back.")
        raise
    finally:
        conn.close()

    LOGGER.info("Drug-disease link generation summary: %s", summary)
    return summary


def main() -> None:
    summary = generate_links()
    print("Generated local evidence-based drug-disease links.")
    print(f"links created: {summary['links_created']}")
    print(f"links skipped as duplicate: {summary['links_skipped_duplicate']}")
    print(
        "links skipped due to weak/ambiguous keyword: "
        f"{summary['links_skipped_weak_or_ambiguous_keyword']}"
    )
    print(f"evidence references created: {summary['evidence_references_created']}")
    print(f"training labels created: {summary['training_labels_created']}")


if __name__ == "__main__":
    main()
