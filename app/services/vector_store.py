from collections.abc import Sequence


def upsert_chunks(document_id: int, chunks: Sequence[str], embeddings: Sequence[Sequence[float]]) -> None:
    raise NotImplementedError("Configure a vector database before indexing documents.")


def search_chunks(
    query_embedding: Sequence[float],
    owner_id: int,
    limit: int = 5,
) -> list[dict[str, object]]:
    raise NotImplementedError("Configure a vector database before retrieving documents.")
