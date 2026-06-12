"""
OmniSLM Metrics — Prometheus instrumentation.

Framework-level metrics decoupled from FastAPI.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class OmniSLMMetrics:
    """Prometheus metrics for OmniSLM."""

    def __init__(self) -> None:
        self._initialized = False

    def initialize(self) -> None:
        """Initialize Prometheus metrics."""
        try:
            from prometheus_client import Counter, Histogram

            self.llm_generation_duration = Histogram(
                "omnislm_llm_generation_duration_seconds",
                "Time spent on LLM generation",
                ["model", "provider"],
            )
            self.llm_tokens_total = Counter(
                "omnislm_llm_tokens_total",
                "Total tokens processed",
                ["model", "provider", "token_type"],
            )
            self.rag_retrieval_duration = Histogram(
                "omnislm_rag_retrieval_duration_seconds",
                "Time spent on RAG retrieval",
            )
            self.agent_steps_total = Counter(
                "omnislm_agent_steps_total",
                "Total agent reasoning steps",
                ["agent_name"],
            )
            self._initialized = True
        except ImportError:
            logger.debug("prometheus-client not installed, metrics disabled")

    def record_generation(
        self, model: str, provider: str, duration: float, tokens: int = 0
    ) -> None:
        """Record an LLM generation event."""
        if not self._initialized:
            return
        self.llm_generation_duration.labels(model=model, provider=provider).observe(
            duration
        )
        if tokens:
            self.llm_tokens_total.labels(
                model=model, provider=provider, token_type="completion"
            ).inc(tokens)
