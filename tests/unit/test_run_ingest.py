import asyncio
from pathlib import Path

import pytest

from scripts import run_ingest


def test_ingestion_fails_when_crawler_omits_a_registered_document(monkeypatch):
    class FakeCrawler:
        async def crawl_p0_corpus(self):
            return []

    monkeypatch.setattr(run_ingest, "LegalCrawler", FakeCrawler)

    with pytest.raises(RuntimeError, match="Incomplete or duplicated P0 crawl"):
        asyncio.run(run_ingest.main("p0"))


def test_ingestion_fails_when_crawled_text_is_missing(monkeypatch, tmp_path: Path):
    class FakeCrawler:
        async def crawl_p0_corpus(self):
            return [
                {
                    "doc_id": source.doc_id,
                    "clean_text_path": str(tmp_path / f"{source.doc_id}.txt"),
                }
                for source in run_ingest.P0_CORPUS_REGISTRY
            ]

    monkeypatch.setattr(run_ingest, "LegalCrawler", FakeCrawler)

    with pytest.raises(FileNotFoundError, match="Missing crawled legal text"):
        asyncio.run(run_ingest.main("p0"))
