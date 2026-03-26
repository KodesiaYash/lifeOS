"""
Embedding service abstraction for generating vector embeddings.
"""

import structlog

from src.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    """
    Generates text embeddings using the configured model (OpenAI text-embedding-3-small by default).
    Provides caching and batching for efficiency.
    """

    def __init__(
        self,
        model: str | None = None,
        dimensions: int | None = None,
    ) -> None:
        self.model = model or settings.DEFAULT_EMBEDDING_MODEL
        self.dimensions = dimensions or settings.EMBEDDING_DIMENSIONS

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding for a single text string."""
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        import openai

        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            response = await client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions,
            )
            embeddings = [item.embedding for item in response.data]
            logger.debug(
                "embeddings_generated",
                count=len(texts),
                model=self.model,
                dimensions=self.dimensions,
            )
            return embeddings
        except Exception:
            logger.exception("embedding_error", model=self.model, batch_size=len(texts))
            raise
