from __future__ import annotations

import argparse
import csv
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import pyodbc

from config import BASE_DIR, LOG_DIR, SQLSERVER_CONNECTION_STRING


OUTPUT_PATH = BASE_DIR / "data" / "seed" / "candidate_diseases_from_drugs.csv"
DICTIONARY_PATH = BASE_DIR / "data" / "seed" / "disease_vietnamese_dictionary.csv"
LOG_PATH = LOG_DIR / "extract_candidate_diseases_from_drug_text.log"

SCAN_FIELDS = (
    "KnownIndications",
    "ContraindicationsInteractions",
    "SideEffectsWarnings",
    "MechanismOfAction",
)

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

TRIGGER_EXPRESSIONS = [
    "treatment of",
    "treatment for",
    "indicated for",
    "indicated in",
    "used to treat",
    "prevention of",
    "management of",
    "patients with",
    "patient with",
    "diagnosis of",
    "contraindicated in patients with",
    "contraindicated in",
    "risk of",
    "history of",
]

TRIGGER_PATTERN = re.compile(
    r"(?P<trigger>\b(?:"
    + "|".join(re.escape(expression) for expression in TRIGGER_EXPRESSIONS)
    + r")\b)\s+(?P<phrase>.{3,220}?)(?=(?:[.;\n\r]|$|\s(?:who|when|where|because|unless|except|including)\b))",
    re.IGNORECASE | re.DOTALL,
)

DIRECT_DISEASE_PATTERNS = [
    "hypertension",
    "pulmonary arterial hypertension",
    "heart failure",
    "atrial fibrillation",
    "coronary artery disease",
    "angina",
    "myocardial infarction",
    "deep vein thrombosis",
    "pulmonary embolism",
    "venous thromboembolism",
    "diabetes mellitus",
    "type 1 diabetes",
    "type 2 diabetes",
    "hypoglycemia",
    "hyperglycemia",
    "hyperthyroidism",
    "hypothyroidism",
    "obesity",
    "asthma",
    "chronic obstructive pulmonary disease",
    "COPD",
    "pneumonia",
    "bronchitis",
    "allergic rhinitis",
    "sinusitis",
    "tuberculosis",
    "hepatitis B",
    "hepatitis C",
    "HIV infection",
    "dengue",
    "malaria",
    "urinary tract infection",
    "bacterial vaginosis",
    "candidiasis",
    "sepsis",
    "migraine",
    "epilepsy",
    "seizure disorder",
    "parkinson disease",
    "alzheimer disease",
    "depression",
    "major depressive disorder",
    "anxiety disorder",
    "bipolar disorder",
    "schizophrenia",
    "attention deficit hyperactivity disorder",
    "insomnia",
    "rheumatoid arthritis",
    "osteoarthritis",
    "psoriatic arthritis",
    "ankylosing spondylitis",
    "gout",
    "osteoporosis",
    "psoriasis",
    "plaque psoriasis",
    "atopic dermatitis",
    "acne vulgaris",
    "rosacea",
    "urticaria",
    "breast cancer",
    "lung cancer",
    "colorectal cancer",
    "prostate cancer",
    "ovarian cancer",
    "leukemia",
    "lymphoma",
    "multiple myeloma",
    "renal cell carcinoma",
    "melanoma",
    "crohn's disease",
    "ulcerative colitis",
    "irritable bowel syndrome",
    "gastroesophageal reflux disease",
    "peptic ulcer disease",
    "constipation",
    "iron deficiency anemia",
    "anemia",
    "endometriosis",
    "polycystic ovary syndrome",
    "benign prostatic hyperplasia",
    "glaucoma",
    "conjunctivitis",
    "otitis media",
    "otitis externa",
]

GENERIC_REJECTS = {
    "adverse reaction",
    "adverse reactions",
    "adult",
    "adults",
    "clinical study",
    "clinical studies",
    "condition",
    "conditions",
    "contraindication",
    "contraindications",
    "disease",
    "diseases",
    "disorder",
    "disorders",
    "dose",
    "injection",
    "pediatric",
    "patient",
    "patients",
    "symptom",
    "symptoms",
    "tablet",
    "therapy",
    "treatment",
}

GENERIC_CONTAINS = [
    "adverse reaction",
    "clinical study",
    "dose adjustment",
    "dosage",
    "tablet",
    "capsule",
    "injection",
    "placebo",
    "monotherapy",
    "combination therapy",
    "use in specific populations",
    "not recommended",
    "safety and effectiveness",
]

LEADING_NOISE_PATTERN = re.compile(
    r"^(?:the\s+|a\s+|an\s+|acute\s+or\s+chronic\s+|chronic\s+or\s+acute\s+|"
    r"mild\s+to\s+moderate\s+|moderate\s+to\s+severe\s+|severe\s+|acute\s+|"
    r"chronic\s+|recurrent\s+|active\s+|suspected\s+|confirmed\s+|"
    r"adult\s+|pediatric\s+|paediatric\s+|patients?\s+(?:with|who have)\s+)+",
    re.IGNORECASE,
)

TRAILING_NOISE_PATTERN = re.compile(
    r"\s+(?:in|among|for|of|to|with|without|who|when|where|including|"
    r"associated with|due to|caused by)\s+.*$",
    re.IGNORECASE,
)

SPLIT_PATTERN = re.compile(
    r"\s*(?:,|;|/|\band\b|\bor\b|\bincluding\b|\bsuch as\b|\bespecially\b)\s+",
    re.IGNORECASE,
)

GROUP_HINTS = [
    ("CANCER", re.compile(r"\b(cancer|carcinoma|tumou?r|leukemia|lymphoma|melanoma|myeloma|neoplasm)\b", re.I)),
    ("CARDIO", re.compile(r"\b(hypertension|heart|atrial|angina|coronary|myocardial|stroke|thrombosis|embolism|vascular)\b", re.I)),
    ("METABOLIC", re.compile(r"\b(diabetes|thyroid|hyperglycemia|hypoglycemia|obesity|cholesterol|lipid)\b", re.I)),
    ("RESPIRATORY", re.compile(r"\b(asthma|pulmonary|pneumonia|bronchitis|COPD|respiratory)\b", re.I)),
    ("INFECTIOUS", re.compile(r"\b(infection|bacterial|fungal|viral|hepatitis|HIV|tuberculosis|malaria|dengue|sepsis|candidiasis)\b", re.I)),
    ("DIGESTIVE", re.compile(r"\b(gastric|gastro|ulcer|colitis|crohn|constipation|bowel|reflux|diarrhea)\b", re.I)),
    ("UROLOGY", re.compile(r"\b(urinary|renal|kidney|prostatic|prostate|bladder|cystitis)\b", re.I)),
    ("NEURO", re.compile(r"\b(migraine|epilepsy|seizure|parkinson|alzheimer|neuropath|multiple sclerosis)\b", re.I)),
    ("MENTAL", re.compile(r"\b(depression|anxiety|bipolar|schizophrenia|insomnia|attention deficit)\b", re.I)),
    ("DERMATOLOGY", re.compile(r"\b(psoriasis|dermatitis|eczema|acne|rosacea|urticaria|skin)\b", re.I)),
    ("AUTOIMMUNE", re.compile(r"\b(rheumatoid|psoriatic arthritis|ankylosing|lupus|autoimmune)\b", re.I)),
]


@dataclass(frozen=True)
class DrugRow:
    drug_id: int
    drug_name: str
    fields: dict[str, str]


@dataclass
class CandidateEvidence:
    canonical_name: str
    matched_keywords: set[str] = field(default_factory=set)
    evidence_fields: set[str] = field(default_factory=set)
    evidence_keys: set[tuple[int, str]] = field(default_factory=set)
    sample_drug_names: list[str] = field(default_factory=list)
    snippets: list[str] = field(default_factory=list)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_keys)


@dataclass(frozen=True)
class VietnameseDiseaseMapping:
    disease_name_vi: str
    keywords_vi: list[str]
    group_code: str


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


def split_terms(value: str | None) -> list[str]:
    if not value:
        return []
    result: list[str] = []
    seen: set[str] = set()
    for part in value.split(";"):
        text = clean_whitespace(part)
        if not text:
            continue
        key = text.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def load_vietnamese_dictionary(
    path: Path = DICTIONARY_PATH,
) -> dict[str, VietnameseDiseaseMapping]:
    if not path.exists():
        LOGGER.warning("Vietnamese disease dictionary not found: %s", path)
        return {}

    dictionary: dict[str, VietnameseDiseaseMapping] = {}
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
            mapping = VietnameseDiseaseMapping(
                disease_name_vi=name_vi,
                keywords_vi=split_terms(row.get("KeywordsVi")),
                group_code=clean_whitespace(row.get("GroupCode")).upper() or "OTHER",
            )
            for key in {
                normalize_text(name_en),
                normalize_name_for_compare(name_en),
            }:
                dictionary.setdefault(key, mapping)
    return dictionary


def find_vietnamese_mapping(
    dictionary: dict[str, VietnameseDiseaseMapping],
    disease_name_en: str,
) -> VietnameseDiseaseMapping | None:
    for key in {
        normalize_text(disease_name_en),
        normalize_name_for_compare(disease_name_en),
    }:
        mapping = dictionary.get(key)
        if mapping is not None:
            return mapping
    return None


def display_name(value: str) -> str:
    normalized = normalize_text(value)
    upper_terms = {"hiv", "copd", "gerd", "adhd", "uti", "bph", "pcos", "covid-19"}
    lower_terms = {"of", "and", "or", "with", "in", "type"}
    words = []
    for word in normalized.split():
        if word in upper_terms:
            words.append(word.upper())
        elif word in lower_terms:
            words.append(word)
        elif word == "crohn's":
            words.append("Crohn's")
        else:
            words.append(word[:1].upper() + word[1:])
    text = " ".join(words)
    text = text.replace("Type 1", "type 1").replace("Type 2", "type 2")
    return text


def snippet_around(text: str, start: int, end: int, radius: int = 180) -> str:
    snippet = text[max(0, start - radius) : min(len(text), end + radius)]
    return clean_whitespace(snippet)[:500]


def phrase_has_disease_signal(value: str) -> bool:
    text = normalize_text(value)
    if not text:
        return False
    disease_terms = [
        "cancer",
        "carcinoma",
        "infection",
        "syndrome",
        "disease",
        "disorder",
        "deficiency",
        "arthritis",
        "dermatitis",
        "psoriasis",
        "asthma",
        "diabetes",
        "hypertension",
        "failure",
        "fibrillation",
        "pneumonia",
        "migraine",
        "epilepsy",
        "depression",
        "anxiety",
        "hepatitis",
        "tuberculosis",
        "glaucoma",
        "anemia",
        "ulcer",
        "colitis",
        "thrombosis",
        "embolism",
        "endometriosis",
        "hyperplasia",
        "acne",
        "rosacea",
        "urticaria",
    ]
    return any(re.search(rf"\b{re.escape(term)}\b", text) for term in disease_terms)


def reject_reason(candidate: str) -> str | None:
    text = normalize_text(candidate)
    if len(text) < 4:
        return "too short"
    if text in GENERIC_REJECTS:
        return "generic"
    if text in {"pain", "infection", "infections", "cancer", "tumor", "tumour", "carcinoma"}:
        return "unsafe generic medical term"
    if len(text.split()) > 7:
        return "too long"
    if any(term in text for term in GENERIC_CONTAINS):
        return "non-disease wording"
    if re.search(r"\b(mg|ml|mcg|tablet|capsule|injection|dose|dosing|daily|twice|once)\b", text):
        return "dosage/form wording"
    if not phrase_has_disease_signal(text):
        return "no disease signal"
    return None


def clean_candidate_phrase(value: str) -> str | None:
    text = clean_whitespace(value)
    text = re.sub(r"\([^)]{1,80}\)", " ", text)
    text = re.sub(r"\[[^]]{1,80}\]", " ", text)
    text = clean_whitespace(text.strip(" ,:;-"))
    text = LEADING_NOISE_PATTERN.sub("", text)
    text = TRAILING_NOISE_PATTERN.sub("", text)
    text = clean_whitespace(text.strip(" ,:;-"))
    if not text:
        return None
    if reject_reason(text):
        return None
    return display_name(text)


def pieces_from_trigger_phrase(phrase: str) -> Iterable[str]:
    base = clean_whitespace(phrase)
    if not base:
        return []
    pieces = [base]
    pieces.extend(part for part in SPLIT_PATTERN.split(base) if part)
    return pieces


def direct_pattern() -> re.Pattern[str]:
    sorted_terms = sorted(DIRECT_DISEASE_PATTERNS, key=len, reverse=True)
    bodies = []
    for term in sorted_terms:
        parts = [part for part in re.split(r"[\s\-_/.]+", term) if part]
        bodies.append(r"[\s\-_/.]+".join(re.escape(part) for part in parts))
    return re.compile(r"(?<![\w])(?P<term>" + "|".join(bodies) + r")(?![\w])", re.I)


DIRECT_PATTERN = direct_pattern()


def load_drugs(cursor: pyodbc.Cursor) -> list[DrugRow]:
    rows = cursor.execute(
        """
        SELECT
            DrugId,
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
    drugs: list[DrugRow] = []
    for row in rows:
        trade_name = clean_whitespace(row.TradeName)
        active_name = clean_whitespace(row.ActiveName)
        name = active_name if not trade_name else f"{active_name} ({trade_name})"
        drugs.append(
            DrugRow(
                drug_id=int(row.DrugId),
                drug_name=name,
                fields={
                    "KnownIndications": clean_whitespace(row.KnownIndications),
                    "ContraindicationsInteractions": clean_whitespace(
                        row.ContraindicationsInteractions
                    ),
                    "SideEffectsWarnings": clean_whitespace(row.SideEffectsWarnings),
                    "MechanismOfAction": clean_whitespace(row.MechanismOfAction),
                },
            )
        )
    return drugs


def load_existing_disease_terms(cursor: pyodbc.Cursor) -> set[str]:
    rows = cursor.execute(
        """
        SELECT DiseaseName AS Term
        FROM dbo.Diseases
        WHERE IsDeleted = 0
        UNION
        SELECT SynonymName AS Term
        FROM dbo.DiseaseSynonyms
        """
    ).fetchall()
    return {
        normalize_name_for_compare(clean_whitespace(row.Term))
        for row in rows
        if clean_whitespace(row.Term)
    }


def add_evidence(
    candidates: dict[str, CandidateEvidence],
    candidate_name: str,
    matched_keyword: str,
    drug: DrugRow,
    field_name: str,
    snippet: str,
) -> None:
    key = normalize_name_for_compare(candidate_name)
    item = candidates.setdefault(key, CandidateEvidence(canonical_name=display_name(candidate_name)))
    item.matched_keywords.add(display_name(matched_keyword))
    item.evidence_fields.add(field_name)
    item.evidence_keys.add((drug.drug_id, field_name))
    if drug.drug_name not in item.sample_drug_names and len(item.sample_drug_names) < 5:
        item.sample_drug_names.append(drug.drug_name)
    if snippet and len(item.snippets) < 3:
        item.snippets.append(snippet)


def extract_from_text(
    drug: DrugRow,
    field_name: str,
    text: str,
    existing_terms: set[str],
    candidates: dict[str, CandidateEvidence],
) -> int:
    extracted = 0
    if not text:
        return extracted

    for match in TRIGGER_PATTERN.finditer(text):
        phrase = match.group("phrase")
        for piece in pieces_from_trigger_phrase(phrase):
            candidate_name = clean_candidate_phrase(piece)
            if candidate_name is None:
                continue
            key = normalize_name_for_compare(candidate_name)
            if key in existing_terms:
                continue
            add_evidence(
                candidates,
                candidate_name,
                candidate_name,
                drug,
                field_name,
                snippet_around(text, match.start("phrase"), match.end("phrase")),
            )
            extracted += 1

    for match in DIRECT_PATTERN.finditer(text):
        candidate_name = clean_candidate_phrase(match.group("term"))
        if candidate_name is None:
            continue
        key = normalize_name_for_compare(candidate_name)
        if key in existing_terms:
            continue
        add_evidence(
            candidates,
            candidate_name,
            match.group("term"),
            drug,
            field_name,
            snippet_around(text, match.start(), match.end()),
        )
        extracted += 1

    return extracted


def infer_group_code(candidate_name: str) -> str:
    for group_code, pattern in GROUP_HINTS:
        if pattern.search(candidate_name):
            return group_code
    return "OTHER"


def write_candidates_csv(
    candidates: dict[str, CandidateEvidence],
    min_evidence: int,
    output_path: Path,
    dictionary: dict[str, VietnameseDiseaseMapping],
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    filtered = [
        item
        for item in candidates.values()
        if item.evidence_count >= min_evidence
    ]
    filtered.sort(key=lambda item: (-item.evidence_count, item.canonical_name.casefold()))

    with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for index, item in enumerate(filtered, start=1):
            mapping = find_vietnamese_mapping(dictionary, item.canonical_name)
            writer.writerow(
                {
                    "CandidateDiseaseCode": f"CAND-DIS-{index:04d}",
                    "CandidateDiseaseNameEn": item.canonical_name,
                    "CandidateDiseaseNameVi": ""
                    if mapping is None
                    else mapping.disease_name_vi,
                    "SuggestedGroupCode": infer_group_code(item.canonical_name)
                    if mapping is None
                    else mapping.group_code,
                    "MatchedKeyword": "; ".join(sorted(item.matched_keywords)),
                    "EvidenceField": "; ".join(sorted(item.evidence_fields)),
                    "EvidenceCount": item.evidence_count,
                    "SampleDrugNames": "; ".join(item.sample_drug_names),
                    "EvidenceSnippet": " || ".join(item.snippets)[:1000],
                    "Action": "NEED_REVIEW",
                }
            )
    return len(filtered)


def extract_candidate_diseases(min_evidence: int, output_path: Path) -> dict[str, int]:
    configure_logging()
    conn = connect_sql_server()
    try:
        cursor = conn.cursor()
        drugs = load_drugs(cursor)
        existing_terms = load_existing_disease_terms(cursor)
        dictionary = load_vietnamese_dictionary()
        candidates: dict[str, CandidateEvidence] = {}
        raw_mentions = 0

        for drug in drugs:
            for field_name in SCAN_FIELDS:
                raw_mentions += extract_from_text(
                    drug,
                    field_name,
                    drug.fields.get(field_name, ""),
                    existing_terms,
                    candidates,
                )

        written = write_candidates_csv(
            candidates,
            min_evidence,
            output_path,
            dictionary,
        )
    finally:
        conn.close()

    summary = {
        "drugs_loaded": len(drugs),
        "existing_disease_terms": len(existing_terms),
        "vietnamese_dictionary_terms": len(dictionary),
        "raw_mentions_extracted": raw_mentions,
        "unique_new_candidates": len(candidates),
        "candidates_written": written,
    }
    LOGGER.info("Candidate extraction summary: %s", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract review-only disease candidates from existing dbo.Drugs text. "
            "No external APIs are called."
        )
    )
    parser.add_argument(
        "--min-evidence",
        type=int,
        default=2,
        help="Minimum distinct drug/field evidence count required for CSV output.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Output CSV path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.min_evidence < 1:
        raise ValueError("--min-evidence must be at least 1.")
    output_path = args.output
    if not output_path.is_absolute():
        output_path = BASE_DIR / output_path
    summary = extract_candidate_diseases(args.min_evidence, output_path)
    print(f"Candidate disease CSV written: {output_path}")
    for key, value in summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
