from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOG_DIR = DATA_DIR / "logs"

load_dotenv(BASE_DIR / ".env")

SQLSERVER_CONNECTION_STRING = os.getenv(
    "SQLSERVER_CONNECTION_STRING",
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=localhost\\SQLEXPRESS;"
    "Database=DrugDiseaseML_DB;"
    "Trusted_Connection=yes;"
    "Encrypt=no;"
    "TrustServerCertificate=yes;",
)

OPENFDA_BASE_URL = os.getenv(
    "OPENFDA_BASE_URL",
    "https://api.fda.gov/drug/label.json",
)

RXNAV_BASE_URL = os.getenv(
    "RXNAV_BASE_URL",
    "https://rxnav.nlm.nih.gov/REST",
).rstrip("/")

IMPORT_LIMIT = int(os.getenv("IMPORT_LIMIT", "300"))
OPENFDA_PAGE_SIZE = int(os.getenv("OPENFDA_PAGE_SIZE", "100"))

DRUGCENTRAL_APPROVED_URL = os.getenv(
    "DRUGCENTRAL_APPROVED_URL",
    "https://unmtid-dbs.net/download/DrugCentral/static/FDA_Approved.csv",
)

DRUGCENTRAL_TARGETS_URL = os.getenv(
    "DRUGCENTRAL_TARGETS_URL",
    "https://unmtid-dbs.net/download/DrugCentral/2021_09_01/drug.target.interaction.tsv.gz",
)
