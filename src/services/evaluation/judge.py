"""
OmniSLM LLM-as-a-Judge.

Uses the runtime model to score RAG/Agent outputs.
"""

from src.core.interfaces.runtime import BaseRuntime
from src.services.evaluation.metrics import AnswerRelevanceMetric, FaithfulnessMetric


class LLMJudge:
    """Evaluates outputs using an LLM prompt."""
    
    def __init__(self, runtime: BaseRuntime, model: str):
        self.runtime = runtime
        self.model = model

    async def score_faithfulness(self, question: str, answer: str, context: list[str]) -> float:
        """Score faithfulness of an answer given a context."""
        context_str = "\n".join(context)
        prompt = f"""Given the following context, evaluate if the answer is faithful to it.
Score it from 0.0 to 1.0, where 1.0 means fully faithful and 0.0 means completely hallucinated.
Output ONLY the float number.

Context:
{context_str}

Question: {question}
Answer: {answer}

Score:"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.runtime.chat(
            model=self.model,
            messages=messages,
            temperature=0.0
        )
        
        try:
            content = response.get("message", {}).get("content", "0.0").strip()
            return float(content)
        except ValueError:
            return 0.0

    async def score_relevance(self, question: str, answer: str) -> float:
        """Score relevance of an answer to the question."""
        prompt = f"""Given the following question, evaluate how relevant the answer is to it.
Score it from 0.0 to 1.0, where 1.0 means perfectly relevant and 0.0 means completely irrelevant.
Output ONLY the float number.

Question: {question}
Answer: {answer}

Score:"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.runtime.chat(
            model=self.model,
            messages=messages,
            temperature=0.0
        )
        
        try:
            content = response.get("message", {}).get("content", "0.0").strip()
            return float(content)
        except ValueError:
            return 0.0
