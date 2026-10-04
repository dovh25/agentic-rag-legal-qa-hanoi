import pytest
from pydantic import ValidationError

from src.models.schemas import LegalCitation, LegalQARequest, LegalQAResponse, ResponseStatus


def test_legal_qa_request_valid():
    req = LegalQARequest(
        query="Quy định về bồi thường thu hồi đất nông nghiệp tại Hà Nội?",
        district="Long Biên",
        as_of_date="2024-08-01",
    )
    assert req.query.startswith("Quy định")
    assert req.district == "Long Biên"


def test_legal_qa_request_too_short():
    with pytest.raises(ValidationError):
        LegalQARequest(query="a")


def test_legal_citation_schema():
    citation = LegalCitation(
        doc_id="Luat-Dat-dai-2024",
        title="Luật Đất đai 2024",
        article="Điều 79",
        snippet="Nhà nước thu hồi đất...",
    )
    assert citation.doc_id == "Luat-Dat-dai-2024"
    assert citation.clause is None


def test_legal_qa_response_schema():
    resp = LegalQAResponse(
        query="Thu hồi đất",
        status=ResponseStatus.ANSWERED,
        answer="Nội dung giải thích...",
        citations=[],
        reasoning_steps=["Step 1"],
    )
    assert resp.status == ResponseStatus.ANSWERED
