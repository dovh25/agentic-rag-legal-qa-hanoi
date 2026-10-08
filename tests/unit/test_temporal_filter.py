from datetime import date

import pytest

from src.agent.retriever import is_document_valid_on


@pytest.mark.parametrize(
    ("metadata", "target", "expected"),
    [
        ({"effective_date": "2024-08-01"}, date(2024, 7, 31), False),
        ({"effective_date": "2024-08-01"}, date(2024, 8, 1), True),
        (
            {"effective_date": "2024-08-01", "legal_status": "amended"},
            date(2024, 8, 1),
            False,
        ),
        (
            {"effective_date": "2024-08-01", "expiry_date": "2025-01-01"},
            date(2025, 1, 1),
            True,
        ),
        (
            {"effective_date": "2024-08-01", "expiry_date": "2025-01-01"},
            date(2025, 1, 2),
            False,
        ),
        ({"expiry_date": None}, date(2024, 8, 1), False),
    ],
)
def test_document_validity_date_boundaries(metadata, target, expected):
    assert is_document_valid_on(metadata, target) is expected


def test_invalid_manifest_dates_raise_instead_of_assuming_validity():
    with pytest.raises(ValueError):
        is_document_valid_on({"effective_date": "not-a-date"}, date(2024, 8, 1))
