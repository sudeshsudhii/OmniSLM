"""
OmniSLM Metrics.

Prometheus metrics instrumentation.
"""

from fastapi import FastAPI
from prometheus_client import Counter, Histogram

try:
    from prometheus_fastapi_instrumentator import Instrumentator
except ImportError:
    Instrumentator = None


# Custom domain metrics
llm_generation_duration_seconds = Histogram(
    "omnislm_llm_generation_duration_seconds",
    "Time spent waiting for LLM generation",
    ["model", "provider"]
)

llm_tokens_total = Counter(
    "omnislm_llm_tokens_total",
    "Total tokens processed by LLMs",
    ["model", "provider", "token_type"]  # token_type = prompt|completion
)

rag_retrieval_duration_seconds = Histogram(
    "omnislm_rag_retrieval_duration_seconds",
    "Time spent retrieving documents from vector DB"
)


def setup_metrics(app: FastAPI) -> None:
    """Instrument FastAPI app with Prometheus metrics."""
    if Instrumentator:
        instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=[".*admin.*", "/metrics", "/healthz", "/readyz"],
            inprogress_name="omnislm_http_requests_inprogress",
            inprogress_labels=True,
        )
        instrumentator.instrument(app).expose(app, include_in_schema=False)
