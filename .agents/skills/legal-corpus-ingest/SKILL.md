---
name: legal-corpus-ingest
description: >-
  Procedures and guidelines for parsing Vietnamese legal documents (Land Law, Hanoi decrees,
  land pricing tables), chunking hierarchically by Điều/Khoản, extracting metadata,
  generating Gemini embeddings, and indexing into a versioned Qdrant collection.
---

# Legal Corpus Ingestion Skill

This skill provides step-by-step instructions for ingesting, validating, chunking, and indexing Vietnamese legal documents relating to land laws, planning, recovery, compensation, and resettlement in Hanoi, aligned with [docs/PRD.md](../../docs/PRD.md) and [docs/Brief.md](../../docs/Brief.md).

---

## 1. Document Sourcing & Hierarchy

### Official Sources & Automated Crawler (ADR-0003)
Dữ liệu được tự động thu thập từ các cổng công báo điện tử chính thức qua module `src/ingest/crawler.py`:
- **Cổng Thông tin điện tử Chính phủ / Cổng VBPL**: [vanban.chinhphu.vn](https://vanban.chinhphu.vn) hoặc [vbpl.vn](https://vbpl.vn)
- **Công báo điện tử TP. Hà Nội**: [congbao.hanoi.gov.vn](https://congbao.hanoi.gov.vn)
- Snapshot lưu trữ: `data/corpus/raw/{doc_id}.html` kèm SHA-256 checksum để đảm bảo tính toàn vẹn (Data Provenance).

### Corpus Tiers (PRD Section 4)
1. **Tier P0 (Core / MVP Mandatory)**:
   - Luật Đất đai số 31/2024/QH15.
   - Nghị định số 88/2024/NĐ-CP (Bồi thường, hỗ trợ, tái định cư).
   - Nghị định số 102/2024/NĐ-CP (Quy định chi tiết thi hành Luật Đất đai).
   - Quyết định số 61/2024/QĐ-UBND TP. Hà Nội (Quy định chi tiết các nội dung bồi thường, hỗ trợ, TĐC tại Hà Nội).
   - Nghị quyết số 52/2025/NQ-HĐND TP. Hà Nội (Bảng giá đất Hà Nội).
2. **Tier P1 (Extended)**:
   - Nghị định số 71/2024/NĐ-CP (Quy định về giá đất).
   - Nghị định số 101/2024/NĐ-CP (Đăng ký, cấp Giấy chứng nhận quyền sử dụng đất).
   - Thông tư số 10/2024/TT-BTNMT.
3. **Tier P2 (Deep Specialization)**:
   - Văn bản hướng dẫn nghiệp vụ của Bộ Tài nguyên & Môi trường.
   - Án lệ và quyết định giải quyết tranh chấp đất đai tại Hà Nội.

---

## 2. Chunking Strategy (Hierarchical by Điều / Khoản)

Do not use arbitrary token chunking (e.g. fixed 500 characters) on legal texts, as this breaks legal definitions and creates hallucination risks.

### Chunking Rules
1. **Primary Unit**: Each chunk must represent a single **Khoản (Clause)** or an entire **Điều (Article)** if the article has no clauses.
2. **Context Header Injection**: Prepend each chunk with full structural breadcrumbs:
   ```text
   [Văn bản: Luật Đất đai 31/2024/QH15] > [Chương VI: Thu hồi đất, trưng dụng đất] > [Điều 79: Thu hồi đất để phát triển kinh tế - xã hội vì lợi ích quốc gia, công cộng] > [Khoản 1]
   Nội dung khoản: ...
   ```
3. **Table Data (Bảng giá đất)**:
   - Chunk by District (Quận/Huyện) > Đường/Phố/Khu vực > Vị trí 1-4.
   - Retain complete header and price metadata in every table row chunk.

---

## 3. Metadata Extraction Schema (PRD Section 8.1)

Every indexed chunk in Qdrant must contain the following payload metadata:

```json
{
  "doc_id": "uuid-v4",
  "document_title": "Luật Đất đai năm 2024",
  "document_number": "31/2024/QH15",
  "document_type": "luat",
  "issuing_body": "Quốc hội",
  "issued_date": "2024-01-18",
  "effective_date": "2024-08-01",
  "expiry_date": null,
  "replaced_by": null,
  "legal_status": "active",
  "legal_domain": ["dat_dai", "quy_hoach", "boi_thuong", "tai_dinh_cu"],
  "applicable_district": null,
  "scope": "national",
  "administrative_area": ["Toàn quốc", "Hà Nội"],
  "chapter": "VI",
  "article_ref": "Điều 79",
  "clause": "Khoản 1",
  "chunk_index": 12,
  "source_url": "https://vanban.chinhphu.vn/?classid=1&docid=211189",
  "chunk_id": "31-2024-QH15-d79-k1",
  "corpus_version": "2026-10-04.1"
}
```

---

## 4. Qdrant Collection & Indexing Configuration

Collection name: `legal_chunks_gemini_embedding_001_v1` (current default; see ADR-0005)

| Parameter | Specification |
|---|---|
| **Dense Vector Dimension** | 768 (`gemini-embedding-001`; see ADR-0005) |
| **Distance Metric** | Cosine |
| **Sparse Vector** | BM25 / Lexical weights |
| **Payload Indexed Fields** | `legal_status` (keyword), `document_number` (keyword), `article_ref` (keyword), `administrative_area` (keyword), `effective_date` (datetime/integer) |

### Verification Command
Verify Qdrant is active and healthy:
```bash
curl -s http://localhost:6333/collections/legal_chunks_gemini_embedding_001_v1 | jq .
```
