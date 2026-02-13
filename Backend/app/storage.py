# storage.py
import hashlib, json, os
from pathlib import Path
from .config import settings

def ensure_dirs():
    Path(settings.pdf_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.artifacts_dir).mkdir(parents=True, exist_ok=True)

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def pdf_path(doc_id: str) -> str:
    return os.path.join(settings.pdf_dir, f"{doc_id}.pdf")

def artifact_path(doc_id: str) -> str:
    return os.path.join(settings.artifacts_dir, f"{doc_id}.json")

def save_pdf(doc_id: str, b: bytes):
    with open(pdf_path(doc_id), "wb") as f:
        f.write(b)

def load_artifact(doc_id: str) -> dict:
    with open(artifact_path(doc_id), "r", encoding="utf-8") as f:
        return json.load(f)

def save_artifact(doc_id: str, obj: dict):
    with open(artifact_path(doc_id), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
