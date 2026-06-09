"""
OmniSLM Evaluation Metrics.

Definitions of metrics for RAG and Agent evaluation.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseMetric(ABC):
    """Abstract base class for evaluation metrics."""
    
    name: str
    description: str

    @abstractmethod
    async def measure(self, question: str, answer: str, context: list[str] | None = None) -> float:
        """Measure the metric and return a score between 0.0 and 1.0."""
        pass


class FaithfulnessMetric(BaseMetric):
    """Measures if the answer is factually consistent with the retrieved context."""
    
    name = "faithfulness"
    description = "Measures how grounded the answer is in the provided context."

    async def measure(self, question: str, answer: str, context: list[str] | None = None) -> float:
        raise NotImplementedError("Requires LLMJudge to implement")


class AnswerRelevanceMetric(BaseMetric):
    """Measures how relevant the answer is to the user's question."""
    
    name = "answer_relevance"
    description = "Measures how directly the answer addresses the question."

    async def measure(self, question: str, answer: str, context: list[str] | None = None) -> float:
        raise NotImplementedError("Requires LLMJudge to implement")
