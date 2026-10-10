import argparse
import asyncio
import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.logging import logger  # noqa: E402
from src.ingest.chunker import LegalChunker  # noqa: E402
from src.ingest.crawler import (  # noqa: E402
    P0_CORPUS_REGISTRY,
    P1_CORPUS_REGISTRY,
    LegalCrawler,
)
from src.ingest.indexer import QdrantLegalIndexer  # noqa: E402
from src.ingest.parser import VietnameseLegalParser  # noqa: E402
from src.ingest.validation import validate_records  # noqa: E402


def _document_payload(item: dict) -> dict:
    return {
        "doc_id": item["doc_id"],
        "doc_number": item["document_number"],
        "doc_title": item["document_title"],
        "doc_type": {
            "luat": "law",
            "nghi_dinh": "decree",
            "quyet_dinh": "decision",
            "nghi_quyet": "resolution",
            "thong_tu": "circular",
        }.get(item["document_type"], item["document_type"]),
        "effective_from": item["effective_date"],
        "effective_to": item.get("expiry_date"),
        "issuing_body": item["issuing_body"],
        "issued_date": item["issued_date"],
        "legal_domain": item["legal_domain"],
        "administrative_area": item["administrative_area"],
        "applicable_district": item.get("applicable_district"),
        "source_url": item["source_url"],
        "legal_status": "active" if item["status"] != "fallback_unverified" else "expired",
        "scope": item.get("scope", "national"),
        "source_authority": item.get("source_authority", "unknown"),
        "corpus_tier": item.get("corpus_tier", "P0"),
        "snapshot_sha256": item["sha256"],
        "parser_version": item.get("parser_version", "parser-v2"),
        "corpus_version": item.get("corpus_version", "2026-10-09.1"),
    }


async def build_corpus(args: argparse.Namespace) -> int:
    registry = list(P0_CORPUS_REGISTRY)
    if args.include_p1:
        registry.extend(P1_CORPUS_REGISTRY)

    crawler = LegalCrawler()
    if args.use_existing_manifest:
        manifest = json.loads(crawler.manifest_path.read_text(encoding="utf-8"))
        expected_ids = {source.doc_id for source in registry}
        manifest = [item for item in manifest if item["doc_id"] in expected_ids]
        if {item["doc_id"] for item in manifest} != expected_ids:
            logger.error("Existing manifest does not contain the requested registry.")
            return 2
    else:
        manifest = await crawler.crawl_corpus(registry)
    blocked = [
        item
        for item in manifest
        if item["status"]
        in {
            "fallback_unverified",
            "official_unextractable",
            "official_mismatch",
            "official_unavailable",
        }
    ]
    if blocked and (not args.allow_unverified or args.promote):
        logger.error(
            "Refusing production build: {} snapshots are not verified text "
            "(fallback or scanned PDF). --allow-unverified is local-only.",
            len(blocked),
        )
        return 2

    parser = VietnameseLegalParser()
    chunker = LegalChunker(corpus_version=args.corpus_version)
    all_chunks = []
    for item in manifest:
        text_file = Path(item["clean_text_path"])
        if not text_file.exists():
            logger.error("Missing clean text snapshot: %s", text_file)
            return 2
        parsed_doc = parser.parse(text_file.read_text(encoding="utf-8"), item)
        all_chunks.extend(chunker.chunk_document(parsed_doc))

    document_records = [_document_payload(item) for item in manifest]
    chunk_fields = {
        "doc_id",
        "doc_number",
        "doc_title",
        "doc_type",
        "issuing_body",
        "issued_date",
        "effective_from",
        "effective_to",
        "legal_status",
        "replaced_by",
        "amended_by",
        "legal_domain",
        "scope",
        "applicable_district",
        "administrative_area",
        "chapter",
        "chapter_title",
        "section",
        "section_title",
        "article",
        "article_title",
        "clause",
        "point",
        "source_url",
        "source_authority",
        "snapshot_sha256",
        "source_fetched_at",
        "quote_text",
        "chunk_id",
        "chunk_index",
        "corpus_tier",
        "corpus_version",
    }
    chunk_records = [
        {key: value for key, value in chunk.metadata.items() if key in chunk_fields}
        | {"chunk_id": chunk.chunk_id}
        for chunk in all_chunks
    ]
    report = validate_records(document_records, chunk_records)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report.write(report_path)
    logger.info(
        "Corpus validation: documents={} chunks={} issues={}",
        report.documents,
        report.chunks,
        len(report.issues),
    )
    if not report.valid or args.validate_only:
        return 0 if report.valid else 2

    indexer = QdrantLegalIndexer()
    if not indexer.recreate_versioned_collection(args.target_collection):
        return 2
    indexer.collection_name = args.target_collection
    indexed = await indexer.index_chunks(all_chunks)
    if indexed != len(all_chunks):
        logger.error("Indexed %d/%d chunks; refusing promotion.", indexed, len(all_chunks))
        return 2

    if args.promote:
        indexer.promote_alias(args.target_collection, args.alias)
        logger.info("Promoted %s to alias %s", args.target_collection, args.alias)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build and version the legal corpus.")
    parser.add_argument("--include-p1", action="store_true", help="Include the P1 registry.")
    parser.add_argument("--allow-unverified", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--promote", action="store_true")
    parser.add_argument("--corpus-version", default="2026-10-09.1")
    parser.add_argument("--target-collection", default="legal_chunks_v2")
    parser.add_argument("--alias", default="legal_chunks")
    parser.add_argument("--report", default="data/corpus/validation-report.json")
    parser.add_argument(
        "--use-existing-manifest",
        action="store_true",
        help="Use the current manifest and snapshots without refetching official sources.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(asyncio.run(build_corpus(parse_args())))
