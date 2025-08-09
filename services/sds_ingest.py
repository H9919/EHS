# services/sds_ingest.py - FIXED VERSION with optional embeddings support
import io
import json
import time
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import fitz  # PyMuPDF

# Import embeddings with proper fallback handling
try:
    from .embeddings import embed_texts, is_sbert_available
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    print("⚠ Embeddings service not available - SDS will work without embeddings")
    EMBEDDINGS_AVAILABLE = False

DATA_DIR = Path("data")
sds_dir = DATA_DIR / "sds"
INDEX_JSON = sds_dir / "index.json"

def load_index():
    """Load SDS index with error handling"""
    sds_dir.mkdir(parents=True, exist_ok=True)
    if INDEX_JSON.exists():
        try:
            return json.loads(INDEX_JSON.read_text())
        except json.JSONDecodeError:
            print("Warning: Corrupted SDS index, creating new one")
            return {}
    return {}

def save_index(obj):
    """Save SDS index with backup"""
    sds_dir.mkdir(parents=True, exist_ok=True)
    
    # Create backup if index exists
    if INDEX_JSON.exists():
        backup_path = INDEX_JSON.with_suffix('.json.backup')
        try:
            INDEX_JSON.replace(backup_path)
        except:
            pass  # Ignore backup errors
    
    INDEX_JSON.write_text(json.dumps(obj, indent=2))

def _sha256_bytes(b: bytes) -> str:
    """Calculate SHA256 hash of bytes"""
    return hashlib.sha256(b).hexdigest()

def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF with error handling"""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text_parts = []
        
        for page in doc:
            try:
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(page_text)
            except Exception as e:
                print(f"Warning: Failed to extract text from page: {e}")
                continue
        
        doc.close()
        return "\n".join(text_parts)
        
    except Exception as e:
        print(f"ERROR: Failed to extract text from PDF: {e}")
        return ""

def _guess_product_name(text: str, filename: str = "") -> str:
    """Guess product name from text content and filename"""
    if not text:
        # Fallback to filename
        if filename:
            name = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
            return ' '.join(word.capitalize() for word in name.split())
        return "Unknown Product"
    
    lines = text.split('\n')[:20]  # Check first 20 lines
    
    # Look for product name patterns
    patterns = [
        r'product\s+name[:\s]+([^\n\r]+)',
        r'trade\s+name[:\s]+([^\n\r]+)',
        r'chemical\s+name[:\s]+([^\n\r]+)',
        r'product[:\s]+([^\n\r]+)',
        r'material[:\s]+([^\n\r]+)'
    ]
    
    for pattern in patterns:
        for line in lines:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                product_name = match.group(1).strip()
                if 3 < len(product_name) < 100:
                    return _clean_product_name(product_name)
    
    # Look for chemical identifiers
    cas_pattern = r'CAS[#\s]*(\d{2,7}-\d{2}-\d)'
    for line in lines:
        cas_match = re.search(cas_pattern, line, re.IGNORECASE)
        if cas_match:
            # Try to find chemical name near CAS number
            for nearby_line in lines:
                if cas_match.group(1) not in nearby_line and 5 < len(nearby_line.strip()) < 80:
                    if not re.search(r'cas|section|page|\d+\.\d+', nearby_line, re.IGNORECASE):
                        return _clean_product_name(nearby_line.strip())
    
    # Use first meaningful line
    for line in lines:
        line = line.strip()
        if 10 < len(line) < 100 and not re.search(r'safety|data|sheet|page|section|\d+', line, re.IGNORECASE):
            return _clean_product_name(line)
    
    # Final fallback
    return "Unknown Product"

def _clean_product_name(raw_name: str) -> str:
    """Clean and normalize product name"""
    if not raw_name:
        return "Unknown Product"
    
    clean_name = raw_name.strip()
    
    # Remove SDS-specific terms
    sds_terms = [
        "safety data sheet", "sds", "msds", "material safety data sheet",
        "product data sheet", "safety datasheet"
    ]
    
    for term in sds_terms:
        clean_name = re.sub(re.escape(term), "", clean_name, flags=re.IGNORECASE)
    
    # Remove version numbers and dates
    clean_name = re.sub(r'version\s+\d+(\.\d+)*', '', clean_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'rev\s+\d+', '', clean_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}', '', clean_name)
    
    # Remove extra whitespace
    clean_name = ' '.join(clean_name.split())
    
    return clean_name.title() if clean_name else "Unknown Product"

def _chunk_text(text: str, size: int = 1000, overlap: int = 100) -> List[str]:
    """Chunk text into overlapping segments"""
    if not text or len(text) < size:
        return [text] if text else []
    
    chunks = []
    i = 0
    
    while i < len(text):
        end = min(i + size, len(text))
        
        # Try to break at sentence boundaries
        if end < len(text):
            # Look for sentence endings within last 200 chars
            search_start = max(end - 200, i)
            for pattern in ['. ', '.\n', '?\n', '!\n']:
                pos = text.rfind(pattern, search_start, end)
                if pos > i:
                    end = pos + len(pattern)
                    break
        
        chunk = text[i:end].strip()
        if chunk:
            chunks.append(chunk)
        
        i = end - overlap
        if i >= len(text):
            break
    
    return chunks[:50]  # Limit to 50 chunks

def ingest_single_pdf(file_stream, filename: str = "upload.pdf") -> Dict:
    """Ingest single PDF with enhanced error handling and optional embeddings"""
    try:
        # Read file
        raw = file_stream.read()
        file_hash = _sha256_bytes(raw)
        
        # Check for existing file
        index = load_index()
        for rec in index.values():
            if rec.get("file_hash") == file_hash:
                print(f"File already exists: {filename}")
                return rec
        
        # Extract text
        text = _extract_text_from_pdf(raw)
        if not text:
            print(f"Warning: No text extracted from {filename}")
        
        # Guess product name
        product_name = _guess_product_name(text, filename)
        print(f"Detected product: {product_name}")
        
        # Save file
        out_name = f"{file_hash[:16]}-{filename}"
        out_path = sds_dir / out_name
        
        try:
            with open(out_path, "wb") as f:
                f.write(raw)
        except Exception as e:
            print(f"ERROR: Failed to save file {out_path}: {e}")
            raise
        
        # Create chunks
        chunks = _chunk_text(text)
        print(f"Created {len(chunks)} text chunks")
        
        # Generate embeddings if available
        embeddings = []
        if EMBEDDINGS_AVAILABLE and chunks:
            try:
                if is_sbert_available():
                    embeddings = embed_texts(chunks).tolist()
                    print(f"Generated {len(embeddings)} embeddings")
                else:
                    print("SBERT not available - skipping embeddings")
            except Exception as e:
                print(f"Warning: Failed to generate embeddings: {e}")
                embeddings = []
        else:
            print("Embeddings not available - SDS will work without semantic search")
        
        # Create record
        sid = file_hash[:12]
        record = {
            "id": sid,
            "file_path": str(out_path.resolve()),
            "file_name": filename,
            "file_hash": file_hash,
            "product_name": product_name,
            "created_ts": time.time(),
            "text_len": len(text),
            "chunks": chunks,
            "embeddings": embeddings,  # Empty list if embeddings not available
            "has_embeddings": bool(embeddings)
        }
        
        # Save to index
        index[sid] = record
        save_index(index)
        
        print(f"✓ Successfully ingested SDS: {product_name} (ID: {sid})")
        return record
        
    except Exception as e:
        print(f"ERROR: Failed to ingest PDF {filename}: {e}")
        import traceback
        traceback.print_exc()
        raise

def search_sds_by_name(query: str, limit: int = 10) -> List[Dict]:
    """Search SDS by product name (basic text search)"""
    try:
        index = load_index()
        if not index:
            return []
        
        query_lower = query.lower()
        results = []
        
        for sds_id, sds_record in index.items():
            product_name = sds_record.get("product_name", "").lower()
            
            # Simple text matching
            if query_lower in product_name:
                results.append({
                    "id": sds_id,
                    "product_name": sds_record.get("product_name"),
                    "file_name": sds_record.get("file_name"),
                    "score": 1.0 if query_lower == product_name else 0.5
                })
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
        
    except Exception as e:
        print(f"ERROR: SDS search failed: {e}")
        return []

def get_sds_stats() -> Dict:
    """Get SDS library statistics"""
    try:
        index = load_index()
        total_sds = len(index)
        with_embeddings = sum(1 for rec in index.values() if rec.get("has_embeddings", False))
        
        return {
            "total_sds": total_sds,
            "with_embeddings": with_embeddings,
            "embeddings_enabled": EMBEDDINGS_AVAILABLE and is_sbert_available() if EMBEDDINGS_AVAILABLE else False
        }
    except Exception as e:
        print(f"ERROR: Failed to get SDS stats: {e}")
        return {"total_sds": 0, "with_embeddings": 0, "embeddings_enabled": False}
