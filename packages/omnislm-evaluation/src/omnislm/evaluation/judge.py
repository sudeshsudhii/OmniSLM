"""
OmniSLM LLM-as-a-Judge.

Uses an LLM to evaluate outputs for faithfulness, relevance, and quality.
"""

from __future__ import annotations

import logging
from typing import Any

from omnislm.core.interfaces.runtime import BaseRuntime

logger = logging.getLogger(__name__)


class LLMJudge:
    """Evaluates LLM outputs using an LLM as a judge.

    Example:
        judge = LLMJudge(runtime=ollama, model="qwen2.5:7b")
        score = await judge.score_faithfulness(question, answer, context)
    """

    def __init__(self, runtime: BaseRuntime, model: str) -> None:
        self._runtime = runtime
        self._model = model

    async def score_faithfulness(
        self, question: str, answer: str, context: list[str]
    ) -> float:
        """Score how faithful an answer is to the provided context.

        Returns:
            Float between 0.0 (hallucinated) and 1.0 (faithful).
        """
        context_str = "\n".join(context)
        prompt = (
            "Given the context below, evaluate if the answer is faithful to it.\n"
            "Score from 0.0 to 1.0 (1.0 = fully faithful, 0.0 = hallucinated).\n"
            "Output ONLY the float number.\n\n"
            f"Context:\n{context_str}\n\n"
            f"Question: {question}\n"
            f"Answer: {answer}\n\n"
            "Score:"
        )

        return await self._get_score(prompt)

    async def score_relevance(self, question: str, answer: str) -> float:
        """Score how relevant an answer is to the question.

        Returns:
            Float between 0.0 (irrelevant) and 1.0 (perfectly relevant).
        """
        prompt = (
            "Evaluate how relevant the answer is to the question.\n"
            "Score from 0.0 to 1.0 (1.0 = perfectly relevant, 0.0 = irrelevant).\n"
            "Output ONLY the float number.\n\n"
            f"Question: {question}\n"
            f"Answer: {answer}\n\n"
            "Score:"
        )

        return await self._get_score(prompt)

    async def score_coherence(self, text: str) -> float:
        """Score the coherence and readability of a text.

        Returns:
            Float between 0.0 (incoherent) and 1.0 (well-written).
        """
        prompt = (
            "Evaluate the coherence and readability of the following text.\n"
            "Score from 0.0 to 1.0.\n"
            "Output ONLY the float number.\n\n"
            f"Text: {text}\n\n"
            "Score:"
        )

        return await self._get_score(prompt)

    async def _get_score(self, prompt: str) -> float:
        """Send a scoring prompt and parse the float result."""
        messages = [{"role": "user", "content": prompt}]
        try:
            response = await self._runtime.chat(
                model=self._model,
                messages=messages,
                temperature=0.0,
                max_tokens=10,
            )
            content = response.get("message", {}).get("content", "0.0").strip()
            # Extract first float-like string
            for word in content.split():
                try:
                    score = float(word)
                    return max(0.0, min(1.0, score))
                except ValueError:
                    continue
            return 0.0
        except Exception as e:
            logger.error("LLM Judge scoring failed: %s", e)
            return 0.0
