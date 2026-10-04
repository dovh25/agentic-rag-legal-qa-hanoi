import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.core.logging import logger  # noqa: E402
from src.ingest.chunker import LegalChunker  # noqa: E402
from src.ingest.crawler import LegalCrawler  # noqa: E402
from src.ingest.indexer import QdrantLegalIndexer  # noqa: E402
from src.ingest.parser import VietnameseLegalParser  # noqa: E402


async def main():
    logger.info("=== Starting Automated Legal Corpus Ingestion (Corpus P0) ===")

    # Step 1: Crawl / Fetch documents
    crawler = LegalCrawler()
    manifest = await crawler.crawl_p0_corpus()
    logger.info(f"Step 1 Complete: {len(manifest)} documents acquired.")

    # Step 2: Parse and Chunk
    parser = VietnameseLegalParser()
    chunker = LegalChunker()
    all_chunks = []

    for item in manifest:
        text_file = Path(item["clean_text_path"])
        if not text_file.exists():
            logger.warning(f"Missing text file: {text_file}")
            continue

        raw_text = text_file.read_text(encoding="utf-8")
        parsed_doc = parser.parse(raw_text, item)
        chunks = chunker.chunk_document(parsed_doc)
        all_chunks.extend(chunks)

        logger.info(
            f"Parsed [{item['doc_id']}]: {len(parsed_doc.articles)} articles -> {len(chunks)} chunks."
        )

    logger.info(f"Step 2 Complete: Total {len(all_chunks)} chunks generated.")

    # Step 3: Index into Qdrant
    indexer = QdrantLegalIndexer()
    total_indexed = indexer.index_chunks(all_chunks)
    logger.info(
        f"Step 3 Complete: Indexed {total_indexed} chunks into Qdrant collection '{indexer.collection_name}'."
    )
    logger.info("=== Ingestion Pipeline Completed Successfully ===")


if __name__ == "__main__":
    asyncio.run(main())
