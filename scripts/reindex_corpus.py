#!/usr/bin/env python3
"""Re-index corpus with dense + sparse vectors for BM25 hybrid search."""

import asyncio
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.ingest.indexer import QdrantLegalIndexer
from src.ingest.parser import VietnameseLegalParser
from src.ingest.chunker import LegalChunker
from src.core.logging import logger
from src.core.config import get_settings


async def reindex_corpus(manifest_path: str = "data/corpus/raw/manifest.json"):
    """Re-index all documents in manifest with dense + sparse vectors."""
    settings = get_settings()
    
    # Create versioned collection name
    versioned_collection = f"legal_chunks_{settings.CORPUS_VERSION.replace('.', '_').replace('-', '_')}"
    logger.info(f"Re-indexing corpus to versioned collection: {versioned_collection}")
    
    # Initialize indexer with versioned collection
    indexer = QdrantLegalIndexer(collection_name=versioned_collection)
    
    # Ensure collection exists with sparse vector support
    if not indexer.ensure_collection():
        logger.error("Failed to create versioned collection")
        return False
    
    # Load manifest
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    
    parser = VietnameseLegalParser()
    chunker = LegalChunker(corpus_version=settings.CORPUS_VERSION)
    
    total_chunks = 0
    
    for doc_meta in manifest:
        doc_id = doc_meta["doc_id"]
        text_path = Path(doc_meta["clean_text_path"])
        
        if not text_path.exists():
            logger.warning(f"Text file not found for {doc_id}: {text_path}")
            continue
        
        logger.info(f"Processing {doc_id}: {doc_meta['document_title']}")
        
        # Read text content
        text = text_path.read_text(encoding="utf-8")
        
        # Parse document
        parsed_doc = parser.parse(text, doc_meta)
        
        # Chunk document
        chunks = chunker.chunk_document(parsed_doc)
        logger.info(f"  Created {len(chunks)} chunks")
        
        # Index chunks
        indexed = await indexer.index_chunks(chunks)
        total_chunks += indexed
        logger.info(f"  Indexed {indexed} chunks")
    
    # Promote alias to new collection
    logger.info(f"Promoting alias 'legal_chunks' to '{versioned_collection}'")
    indexer.promote_alias(versioned_collection, settings.QDRANT_ACTIVE_ALIAS)
    
    logger.info(f"Re-indexing complete. Total chunks indexed: {total_chunks}")
    return True


if __name__ == "__main__":
    success = asyncio.run(reindex_corpus())
    sys.exit(0 if success else 1)
