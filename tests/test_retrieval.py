import pytest

from app.services.chunking_service import chunk_text


def test_chunk_text_applies_overlap():
    chunks = chunk_text("one two three four five", chunk_size=3, overlap=1)
    assert chunks == ["one two three", "three four five"]


def test_chunk_text_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        chunk_text("text", chunk_size=2, overlap=2)
