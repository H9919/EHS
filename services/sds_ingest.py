import io
import json
import time
import hashlib
from pathlib import Path
import fitz  # PyMuPDF

DATA_DIR = Path("data")
sds_dir = DATA_DIR / "sds"
INDEX_JSON = sds_dir / "index.json"

def load_index():
    sds_dir.mkdir(parents=True, exist_ok=True)
    if INDEX_JSON.exists():
        return json.loads(INDEX_JSON.read_text())
    return {}

def save_index(obj):
    sds_dir.mkdir(parents=True, exist_ok=True)
    INDEX_JSON.write_text(json.dumps(obj, indent=2))

def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()

def _extract_text(pdf_bytes: bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    text = []
    for page in doc:
        text.append(page.get_text())
    return "\n".join(text)

def _guess_product_name(text: str):
    # extremely simple heuristic: first non-empty line
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line[:120]
    return "Unknown Product"

def ingest_single_pdf(file_stream, filename: str = "upload.pdf"):
    raw = file_stream.read()
    file_hash = _sha256_bytes(raw)
    index = load_index()

    # duplicate by hash
    for rec in index.values():
        if rec.get("file_hash") == file_hash:
            return rec  # already ingested

    text = _extract_text(raw)
    product_name = _guess_product_name(text)

    # write file
    out_name = f"{file_hash[:16]}-{filename}"
    out_path = sds_dir / out_name
    with open(out_path, "wb") as f:
        f.write(raw)

    sid = file_hash[:12]
    record = {
        "id": sid,
        "file_path": str(out_path.resolve()),
        "file_name": filename,
        "file_hash": file_hash,
        "product_name": product_name,
        "created_ts": time.time(),
        "text_len": len(text),
        # naive “chunks” for SDS chat — in real system use proper chunking/embeddings
        "chunks": [text[i:i+2000] for i in range(0, len(text), 2000)][:20]
    }
    index[sid] = record
    save_index(index)
    return record

