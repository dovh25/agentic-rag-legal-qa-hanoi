---
name: legal-corpus-ingest
description: >-
  Procedures and guidelines for parsing Vietnamese legal documents (Land Law, Hanoi decrees,
  land pricing tables), chunking hierarchically by Điều/Khoản, extracting metadata,
  generating BGE-M3 embeddings, and indexing into Qdrant collection legal_chunks.
---

# Legal Corpus Ingestion Skill

This skill provides step-by-step instructions for ingesting, validating, chunking, and indexing Vietnamese legal documents relating to land laws, planning, recovery, compensation, and resettlement in Hanoi.

---

## 1. Document Sourcing & Hierarchy

### Official Sources
Always download legal documents from verified government gazette repositories:
- **National portal**: [vanban.chinhphu.vn](https://vanban.chinhphu.vn)
- **Hanoi City Gazette**: [congbao.hanoi.gov.vn](https://congbao.hanoi.gov.vn)

### Document Hierarchy
1. **Luật (Laws)**: Luật Đất đai số 31/2024/QH15.
2. **Nghị định (Decrees)**: Nghị định 88/2024/NĐ-CP, Nghị định 102/2024/NĐ-CP.
3. **Thông tư (Circulars)**: Hướng dẫn thi hành của Bộ Tài nguyên và Môi trường / Bộ Tài chính.
4. **Văn bản địa phương TP. Hà Nội**:
   - Nghị quyết số 52/2025/NQ-HĐND (Bảng giá đất TP. Hà Nội).
   - Quyết định số 61/2024/QĐ-UBND (Bồi thường, hỗ trợ, tái định cư trên địa bàn Hà Nội).

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

## 3. Metadata Extraction Schema

Every indexed chunk in Qdrant must contain the following payload metadata:

```json
{
  "doc_id": "uuid-v4",
  "doc_number": "31/2024/QH15",
  "doc_title": "Luật Đất đai năm 2024",
  "doc_type": "law",
  "issuing_body": "Quốc hội",
  "effective_from": "2024-08-01",
  "effective_to": null,
  "legal_status": "active",
  "scope": "national",
  "administrative_area": ["Toàn quốc", "Hà Nội"],
  "chapter": "VI",
  "article": "79",
  "clause": "1",
  "source_url": "https://vanban.chinhphu.vn/?classid=1&docid=211189",
  "chunk_id": "31-2024-QH15-d79-k1",
  "corpus_version": "2026-10-04.1"
}
```

---

## 4. Qdrant Collection & Indexing Configuration

Collection name: `legal_chunks`

| Parameter | Specification |
|---|---|
| **Dense Vector Dimension** | 1024 (`BAAI/bge-m3`) |
| **Distance Metric** | Cosine |
| **Sparse Vector** | BM25 / Lexical weights |
| **Payload Indexed Fields** | `legal_status` (keyword), `doc_number` (keyword), `article` (keyword), `administrative_area` (keyword), `effective_from` (datetime/integer) |

### Verification Command
Verify Qdrant is active and healthy:
```bash
curl -s http://localhost:6333/collections/legal_chunks | jq .
```
