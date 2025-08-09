# services/sds_ingest.py - Enhanced with better text extraction and duplicate detection
import io
import json
import time
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import fitz  # PyMuPDF
from .embeddings import embed_texts

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
        INDEX_JSON.replace(backup_path)
    
    INDEX_JSON.write_text(json.dumps(obj, indent=2))

def _sha256_bytes(b: bytes) -> str:
    """Calculate SHA256 hash of bytes"""
    return hashlib.sha256(b).hexdigest()

def _extract_text_enhanced(pdf_bytes: bytes) -> Dict:
    """Enhanced text extraction with table and metadata extraction"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    extracted_data = {
        "text": [],
        "tables": [],
        "images": [],
        "metadata": {}
    }
    
    # Extract document metadata
    extracted_data["metadata"] = {
        "page_count": len(doc),
        "title": doc.metadata.get("title", ""),
        "author": doc.metadata.get("author", ""),
        "subject": doc.metadata.get("subject", ""),
        "creator": doc.metadata.get("creator", "")
    }
    
    for page_num, page in enumerate(doc):
        # Extract text
        page_text = page.get_text()
        extracted_data["text"].append({
            "page": page_num + 1,
            "content": page_text
        })
        
        # Extract tables
        tables = page.find_tables()
        for table_num, table in enumerate(tables):
            try:
                table_data = table.extract()
                extracted_data["tables"].append({
                    "page": page_num + 1,
                    "table": table_num + 1,
                    "data": table_data
                })
            except:
                pass
        
        # Extract images (metadata only)
        images = page.get_images()
        for img_num, img in enumerate(images):
            extracted_data["images"].append({
                "page": page_num + 1,
                "image": img_num + 1,
                "xref": img[0],
                "width": img[2],
                "height": img[3]
            })
    
    doc.close()
    return extracted_data

def _clean_product_name(raw_name: str) -> str:
    """Clean and normalize product name for duplicate detection"""
    if not raw_name:
        return "Unknown Product"
    
    # Remove common SDS prefixes/suffixes
    clean_name = raw_name.strip()
    
    # Remove SDS-specific terms
    sds_terms = [
        "safety data sheet", "sds", "msds", "material safety data sheet",
        "product data sheet", "safety datasheet"
    ]
    
    for term in sds_terms:
        clean_name = re.sub(re.escape(term), "", clean_name, flags=re.IGNORECASE)
    
    # Remove version numbers and revision dates
    clean_name = re.sub(r'version\s+\d+(\.\d+)*', '', clean_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'rev\s+\d+', '', clean_name, flags=re.IGNORECASE)
    clean_name = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4}', '', clean_name)  # Remove dates
    
    # Remove extra whitespace and normalize
    clean_name = ' '.join(clean_name.split())
    
    # Convert to title case
    return clean_name.title() if clean_name else "Unknown Product"

def _guess_product_name_enhanced(extracted_data: Dict) -> Tuple[str, str]:
    """Enhanced product name extraction using multiple strategies"""
    all_text = ""
    for page_data in extracted_data["text"]:
        all_text += page_data["content"] + "\n"
    
    lines = all_text.split('\n')
    
    # Strategy 1: Look for product name patterns
    product_patterns = [
        r'product\s+name[:\s]+([^\n\r]+)',
        r'trade\s+name[:\s]+([^\n\r]+)',
        r'chemical\s+name[:\s]+([^\n\r]+)',
        r'product[:\s]+([^\n\r]+)',
        r'material[:\s]+([^\n\r]+)'
    ]
    
    for pattern in product_patterns:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            product_name = match.group(1).strip()
            if len(product_name) > 3 and len(product_name) < 100:
                return _clean_product_name(product_name), "pattern_match"
    
    # Strategy 2: Look for chemical identifiers
    cas_pattern = r'CAS[#\s]*(\d{2,7}-\d{2}-\d)'
    cas_match = re.search(cas_pattern, all_text, re.IGNORECASE)
    if cas_match:
        cas_number = cas_match.group(1)
        # Try to find chemical name near CAS number
        cas_context = all_text[max(0, cas_match.start()-200):cas_match.end()+200]
        context_lines = cas_context.split('\n')
        for line in context_lines:
            if cas_number not in line and len(line.strip()) > 5 and len(line.strip()) < 80:
                if not re.search(r'cas|section|page|\d+\.\d+', line, re.IGNORECASE):
                    return _clean_product_name(line.strip()), "cas_context"
    
    # Strategy 3: Use document title from metadata
    title = extracted_data["metadata"].get("title", "")
    if title and len(title) > 3:
        return _clean_product_name(title), "metadata_title"
    
    # Strategy 4: Look at first meaningful line
    for line in lines[:20]:  # Check first 20 lines
        line = line.strip()
        if (len(line) > 10 and len(line) < 100 and 
            not re.search(r'safety|data|sheet|page|section|\d+', line, re.IGNORECASE)):
            return _clean_product_name(line), "first_line"
    
    # Fallback
    return "Unknown Product", "fallback"

def _detect_duplicates(new_record: Dict, existing_index: Dict) -> List[Dict]:
    """Detect potential duplicates using multiple criteria"""
    duplicates = []
    
    new_hash = new_record.get("file_hash")
    new_name = new_record.get("cleaned_product_name", "")
    new_size = new_record.get("file_size", 0)
    
    for existing_id, existing_record in existing_index.items():
        similarity_score = 0
        match_reasons = []
        
        # Exact file hash match (100% duplicate)
        if existing_record.get("file_hash") == new_hash:
            similarity_score = 100
            match_reasons.append("Identical file hash")
        else:
            # Product name similarity
            existing_name = existing_record.get("cleaned_product_name", "")
            if existing_name and new_name:
                name_similarity = _calculate_name_similarity(new_name, existing_name)
                similarity_score += name_similarity * 0.6
                if name_similarity > 80:
                    match_reasons.append(f"Product name similarity: {name_similarity}%")
            
            # File size similarity (within 10%)
            existing_size = existing_record.get("file_size", 0)
            if existing_size and new_size:
                size_diff = abs(existing_size - new_size) / max(existing_size, new_size)
                if size_diff < 0.1:  # Within 10%
                    similarity_score += 20
                    match_reasons.append("Similar file size")
            
            # Content similarity (placeholder for now)
            # Could implement text similarity here
        
        if similarity_score > 70:
            duplicates.append({
                "existing_id": existing_id,
                "existing_record": existing_record,
                "similarity_score": similarity_score,
                "match_reasons": match_reasons
            })
    
    return duplicates

def _calculate_name_similarity(name1: str, name2: str) -> float:
    """Calculate similarity between two product names"""
    if not name1 or not name2:
        return 0.0
    
    name1_clean = name1.lower().strip()
    name2_clean = name2.lower().strip()
    
    # Exact match
    if name1_clean == name2_clean:
        return 100.0
    
    # Calculate Jaccard similarity of words
    words1 = set(name1_clean.split())
    words2 = set(name2_clean.split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    jaccard_similarity = (intersection / union) * 100 if union > 0 else 0
    
    # Boost score if one name contains the other
    if name1_clean in name2_clean or name2_clean in name1_clean:
        jaccard_similarity = min(100, jaccard_similarity + 20)
    
    return jaccard_similarity

def _chunk_enhanced(text: str, size: int = 1200, overlap: int = 150) -> List[str]:
    """Enhanced text chunking with smart boundary detection"""
    if not text or len(text) < size:
        return [text] if text else []
    
    chunks = []
    i = 0
    
    while i < len(text):
        end_pos = min(i + size, len(text))
        
        # Try to find a good breaking point (sentence or paragraph boundary)
        if end_pos < len(text):
            # Look for sentence endings within the last 200 characters
            search_start = max(end_pos - 200, i)
            sentence_breaks = []
            
            for pattern in ['. ', '.\n', '?\n', '!\n']:
                pos = text.rfind(pattern, search_start, end_pos)
                if pos > i:
                    sentence_breaks.append(pos + len(pattern))
            
            if sentence_breaks:
                end_pos = max(sentence_breaks)
        
        chunk = text[i:end_pos].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move to next position with overlap
        i = end_pos - overlap
        if i >= len(text):
            break
    
    return chunks[:50]  # Limit to 50 chunks

def _extract_chemical_info(text: str) -> Dict:
    """Extract key chemical information from SDS text"""
    chemical_info = {
        "cas_numbers": [],
        "hazard_statements": [],
        "precautionary_statements": [],
        "signal_words": [],
        "ghs_symbols": []
    }
    
    # Extract CAS numbers
    cas_pattern = r'(\d{2,7}-\d{2}-\d)'
    chemical_info["cas_numbers"] = list(set(re.findall(cas_pattern, text)))
    
    # Extract hazard statements (H-codes)
    h_pattern = r'H\d{3}[:\s]*([^\n\r\.]+)'
    chemical_info["hazard_statements"] = list(set(re.findall(h_pattern, text, re.IGNORECASE)))
    
    # Extract precautionary statements (P-codes)
    p_pattern = r'P\d{3}[:\s]*([^\n\r\.]+)'
    chemical_info["precautionary_statements"] = list(set(re.findall(p_pattern, text, re.IGNORECASE)))
    
    # Extract signal words
    signal_words = ["DANGER", "WARNING"]
    for word in signal_words:
        if word in text.upper():
            chemical_info["signal_words"].append(word)
    
    # Extract GHS symbols/pictograms
    ghs_symbols = [
        "explosive", "flammable", "oxidizing", "compressed gas", "corrosive",
        "toxic", "harmful", "health hazard", "environmental hazard"
    ]
    
    for symbol in ghs_symbols:
        if symbol.lower() in text.lower():
            chemical_info["ghs_symbols"].append(symbol)
    
    return chemical_info

def ingest_single_pdf_enhanced(file_stream, filename: str = "upload.pdf") -> Dict:
    """Enhanced PDF ingestion with duplicate detection and chemical info extraction"""
    raw = file_stream.read()
    file_hash = _sha256_bytes(raw)
    file_size = len(raw)
    
    index = load_index()
    
    # Check for exact duplicates by hash
    for rec in index.values():
        if rec.get("file_hash") == file_hash:
            return {
                "status": "duplicate",
                "message": "File already exists in library",
                "existing_record": rec
            }
    
    try:
        # Enhanced text extraction
        extracted_data = _extract_text_enhanced(raw)
        
        # Combine all text for processing
        all_text = "\n".join([page["content"] for page in extracted_data["text"]])
        
        # Extract product name with confidence scoring
        product_name, extraction_method = _guess_product_name_enhanced(extracted_data)
        cleaned_product_name = _clean_product_name(product_name)
        
        # Extract chemical information
        chemical_info = _extract_chemical_info(all_text)
        
        # Create preliminary record for duplicate detection
        preliminary_record = {
            "cleaned_product_name": cleaned_product_name,
            "file_hash": file_hash,
            "file_size": file_size,
            "product_name": product_name
        }
        
        # Check for potential duplicates
        duplicates = _detect_duplicates(preliminary_record, index)
        
        if duplicates:
            # Return duplicate information for user decision
            return {
                "status": "potential_duplicate",
                "message": f"Found {len(duplicates)} potential duplicate(s)",
                "duplicates": duplicates,
                "new_record": preliminary_record,
                "require_confirmation": True
            }
        
        # Save file
        out_name = f"{file_hash[:16]}-{filename}"
        out_path = sds_dir / out_name
        with open(out_path, "wb") as f:
            f.write(raw)
        
        # Enhanced chunking and embedding
        chunks = _chunk_enhanced(all_text)
        embeddings = embed_texts(chunks).tolist()
        
        # Create complete record
        sid = file_hash[:12]
        record = {
            "id": sid,
            "file_path": str(out_path.resolve()),
            "file_name": filename,
            "file_hash": file_hash,
            "file_size": file_size,
            "product_name": product_name,
            "cleaned_product_name": cleaned_product_name,
            "extraction_method": extraction_method,
            "created_ts": time.time(),
            "text_len": len(all_text),
            "chunks": chunks,
            "embeddings": embeddings,
            "metadata": extracted_data["metadata"],
            "chemical_info": chemical_info,
            "table_count": len(extracted_data["tables"]),
            "image_count": len(extracted_data["images"]),
            "version": "2.0"  # Enhanced version
        }
        
        # Save to index
        index[sid] = record
        save_index(index)
        
        return {
            "status": "success",
            "message": "SDS successfully ingested",
            "record": record
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error processing PDF: {str(e)}"
        }

# Enhanced SDS Chat System
class SDSChatSystem:
    """Enhanced SDS chat with context and citation tracking"""
    
    def __init__(self):
        self.conversation_history = {}  # Per-SDS conversation history
    
    def chat_with_sds(self, sds_id: str, question: str, user_context: Dict = None) -> Dict:
        """Enhanced SDS chat with better context and citations"""
        try:
            index = load_index()
            sds_record = index.get(sds_id)
            
            if not sds_record:
                return {
                    "status": "error",
                    "message": "SDS not found"
                }
            
            # Get or create conversation history for this SDS
            if sds_id not in self.conversation_history:
                self.conversation_history[sds_id] = []
            
            # Perform semantic search
            answer_data = self._semantic_search(sds_record, question, user_context)
            
            # Store conversation
            self.conversation_history[sds_id].append({
                "question": question,
                "answer": answer_data["answer"],
                "citations": answer_data["citations"],
                "timestamp": datetime.now().isoformat(),
                "confidence": answer_data["confidence"]
            })
            
            return {
                "status": "success",
                "answer": answer_data["answer"],
                "citations": answer_data["citations"],
                "confidence": answer_data["confidence"],
                "sds_info": {
                    "product_name": sds_record.get("product_name"),
                    "cas_numbers": sds_record.get("chemical_info", {}).get("cas_numbers", [])
                },
                "related_questions": self._generate_related_questions(sds_record, question)
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing question: {str(e)}"
            }
    
    def _semantic_search(self, sds_record: Dict, question: str, context: Dict = None) -> Dict:
        """Enhanced semantic search with multiple strategies"""
        chunks = sds_record.get("chunks", [])
        embeddings = sds_record.get("embeddings", [])
        
        if not chunks or not embeddings:
            return {
                "answer": "Unable to search this SDS - no indexed content available",
                "citations": [],
                "confidence": 0.0
            }
        
        try:
            from .embeddings import embed_query, cosine_sim
            import numpy as np
            
            # Convert question to embedding
            question_embedding = embed_query(question)
            
            # Calculate similarities
            similarities = []
            for i, chunk_embedding in enumerate(embeddings):
                chunk_emb = np.array(chunk_embedding, dtype=np.float32)
                similarity = cosine_sim(question_embedding, chunk_emb)
                similarities.append((i, similarity, chunks[i]))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Get top relevant chunks
            top_chunks = similarities[:3]
            
            # Keyword matching boost
            question_lower = question.lower()
            keyword_boosted = []
            
            for idx, sim, chunk in similarities[:10]:  # Check top 10 for keywords
                chunk_lower = chunk.lower()
                keyword_boost = 0
                
                # Check for specific SDS keywords
                if any(word in chunk_lower for word in ["ppe", "personal protective equipment"]):
                    if any(word in question_lower for word in ["ppe", "protection", "equipment"]):
                        keyword_boost += 0.2
                
                if any(word in chunk_lower for word in ["first aid", "emergency"]):
                    if any(word in question_lower for word in ["first aid", "emergency", "exposure"]):
                        keyword_boost += 0.2
                
                if any(word in chunk_lower for word in ["storage", "handling"]):
                    if any(word in question_lower for word in ["store", "handle", "storage"]):
                        keyword_boost += 0.15
                
                boosted_sim = min(1.0, sim + keyword_boost)
                keyword_boosted.append((idx, boosted_sim, chunk))
            
            # Re-sort with keyword boost
            keyword_boosted.sort(key=lambda x: x[1], reverse=True)
            final_chunks = keyword_boosted[:3]
            
            # Combine answers with citations
            answer_parts = []
            citations = []
            
            for i, (chunk_idx, similarity, chunk) in enumerate(final_chunks):
                if similarity > 0.3:  # Only include relevant chunks
                    answer_parts.append(chunk[:500])  # Limit chunk size
                    citations.append({
                        "chunk_index": chunk_idx,
                        "similarity": float(similarity),
                        "page": self._estimate_page_number(chunk_idx, len(chunks)),
                        "preview": chunk[:100] + "..." if len(chunk) > 100 else chunk
                    })
            
            if not answer_parts:
                return {
                    "answer": "I couldn't find specific information about your question in this SDS. Please try rephrasing your question or ask about a different topic.",
                    "citations": [],
                    "confidence": 0.0
                }
            
            # Combine answer parts
            combined_answer = "\n\n".join(answer_parts)
            if len(combined_answer) > 1500:
                combined_answer = combined_answer[:1500] + "..."
            
            # Calculate confidence
            avg_similarity = sum(sim for _, sim, _ in final_chunks) / len(final_chunks)
            confidence = min(1.0, avg_similarity * 1.2)  # Boost confidence slightly
            
            return {
                "answer": combined_answer,
                "citations": citations,
                "confidence": confidence
            }
            
        except Exception as e:
            return {
                "answer": f"Error searching SDS content: {str(e)}",
                "citations": [],
                "confidence": 0.0
            }
    
    def _estimate_page_number(self, chunk_index: int, total_chunks: int) -> int:
        """Estimate page number from chunk index"""
        # Rough estimation assuming even distribution
        estimated_page = max(1, int((chunk_index / total_chunks) * 10))  # Assume ~10 page document
        return estimated_page
    
    def _generate_related_questions(self, sds_record: Dict, current_question: str) -> List[str]:
        """Generate related questions based on SDS content and current question"""
        chemical_info = sds_record.get("chemical_info", {})
        product_name = sds_record.get("product_name", "this chemical")
        
        related_questions = [
            f"What PPE is required when working with {product_name}?",
            f"How should {product_name} be stored safely?",
            f"What are the first aid measures for {product_name} exposure?",
            f"What are the physical properties of {product_name}?",
            f"How should spills of {product_name} be cleaned up?"
        ]
        
        # Add CAS-specific questions if available
        if chemical_info.get("cas_numbers"):
            cas = chemical_info["cas_numbers"][0]
            related_questions.append(f"What is the hazard classification for CAS {cas}?")
        
        # Filter out the current question
        current_lower = current_question.lower()
        filtered = [q for q in related_questions if not any(word in q.lower() for word in current_lower.split()[:3])]
        
        return filtered[:4]  # Return top 4 related questions

# Multi-SDS search functionality
def search_across_all_sds(query: str, limit: int = 5) -> List[Dict]:
    """Search across all SDS documents and return results with citations"""
    try:
        index = load_index()
        
        if not index:
            return []
        
        from .embeddings import embed_query, cosine_sim
        import numpy as np
        
        query_embedding = embed_query(query)
        all_results = []
        
        # Search each SDS
        for sds_id, sds_record in index.items():
            chunks = sds_record.get("chunks", [])
            embeddings = sds_record.get("embeddings", [])
            
            if not chunks or not embeddings:
                continue
            
            # Find best match in this SDS
            best_similarity = 0
            best_chunk = ""
            best_chunk_idx = 0
            
            for i, chunk_embedding in enumerate(embeddings):
                chunk_emb = np.array(chunk_embedding, dtype=np.float32)
                similarity = cosine_sim(query_embedding, chunk_emb)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_chunk = chunks[i]
                    best_chunk_idx = i
            
            if best_similarity > 0.3:  # Minimum relevance threshold
                all_results.append({
                    "sds_id": sds_id,
                    "product_name": sds_record.get("product_name"),
                    "similarity": best_similarity,
                    "content": best_chunk[:300] + "..." if len(best_chunk) > 300 else best_chunk,
                    "chunk_index": best_chunk_idx,
                    "file_name": sds_record.get("file_name"),
                    "cas_numbers": sds_record.get("chemical_info", {}).get("cas_numbers", [])
                })
        
        # Sort by similarity and return top results
        all_results.sort(key=lambda x: x["similarity"], reverse=True)
        return all_results[:limit]
        
    except Exception as e:
        print(f"Error in multi-SDS search: {e}")
        return []
