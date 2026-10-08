from types import SimpleNamespace

from qdrant_client.http import models as qmodels

from src.ingest.indexer import QdrantLegalIndexer


def test_indexer_migrates_date_payload_indexes_to_datetime():
    existing_schema = {
        "effective_date": SimpleNamespace(data_type=qmodels.PayloadSchemaType.KEYWORD)
    }
    deleted = []
    created = []

    class FakeClient:
        def get_collections(self):
            return SimpleNamespace(
                collections=[SimpleNamespace(name="legal_chunks")]
            )

        def get_collection(self, collection_name):
            return SimpleNamespace(payload_schema=existing_schema)

        def delete_payload_index(self, **kwargs):
            deleted.append(kwargs["field_name"])

        def create_payload_index(self, **kwargs):
            created.append((kwargs["field_name"], kwargs["field_schema"]))

    indexer = QdrantLegalIndexer()
    client = FakeClient()
    indexer.client = client
    indexer.connect = lambda: client

    assert indexer.ensure_collection() is True
    assert deleted == ["effective_date"]
    assert ("effective_date", qmodels.PayloadSchemaType.DATETIME) in created
    assert ("expiry_date", qmodels.PayloadSchemaType.DATETIME) in created
