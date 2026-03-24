"""
Multi-signal reranking: fuses results from multiple retrievers and scores them.
"""
import structlog
from datetime import datetime, timezone

from src.retrieval.schemas import RetrievalResult

logger = structlog.get_logger()


class Reranker:
    """
    Fuses and reranks retrieval results from multiple sources.
    Scoring signals: base relevance, recency, importance, diversity.
    """

    def rerank(
        self,
        results: list[RetrievalResult],
        recency_weight: float = 0.3,
        importance_weight: float = 0.2,
        diversity_factor: float = 0.1,
        min_score: float = 0.3,
    ) -> list[RetrievalResult]:
        """
        Rerank results using multiple signals.

        Scoring formula:
          final_score = base_relevance * (1 - recency_weight - importance_weight)
                      + recency_score * recency_weight
                      + importance_score * importance_weight
                      - diversity_penalty
        """
        if not results:
            return []

        scored = []
        seen_contents: list[str] = []

        for result in results:
            base = result.relevance_score

            # Recency score (0-1, exponential decay)
            recency = self._recency_score(result.created_at)

            # Importance score (from metadata if available)
            importance = result.metadata.get("importance", 0.5)

            # Diversity penalty (penalize similar content)
            diversity_penalty = self._diversity_penalty(result.content, seen_contents, diversity_factor)

            # Final score
            base_weight = 1.0 - recency_weight - importance_weight
            final_score = (
                base * base_weight
                + recency * recency_weight
                + importance * importance_weight
                - diversity_penalty
            )

            result.relevance_score = max(0.0, min(1.0, final_score))
            scored.append(result)
            seen_contents.append(result.content)

        # Filter by minimum score and sort
        scored = [r for r in scored if r.relevance_score >= min_score]
        scored.sort(key=lambda r: r.relevance_score, reverse=True)

        logger.debug("reranking_complete", input=len(results), output=len(scored))
        return scored

    def _recency_score(self, created_at: datetime | None) -> float:
        """Score based on how recent the item is. 1.0 = now, decays over time."""
        if created_at is None:
            return 0.5
        now = datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_hours = (now - created_at).total_seconds() / 3600
        # Exponential decay: half-life of 168 hours (1 week)
        return 2 ** (-age_hours / 168)

    def _diversity_penalty(
        self, content: str, seen: list[str], factor: float
    ) -> float:
        """Penalize content that is too similar to already-seen results."""
        if not seen or factor == 0:
            return 0.0
        # Simple overlap check: fraction of words in common
        content_words = set(content.lower().split())
        max_overlap = 0.0
        for prev in seen:
            prev_words = set(prev.lower().split())
            if not content_words or not prev_words:
                continue
            overlap = len(content_words & prev_words) / max(len(content_words), len(prev_words))
            max_overlap = max(max_overlap, overlap)
        return max_overlap * factor
