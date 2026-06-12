"""
OmniSLM Runtimes — LLM inference runtime adapters.

Provides adapters for Ollama, vLLM, llama.cpp, Transformers, and ONNX Runtime.
Runtimes are swapped via configuration — no code changes needed.
"""

from omnislm.runtimes.manager import RuntimeManager
from omnislm.runtimes.ollama import OllamaRuntime

__all__ = [
    "RuntimeManager",
    "OllamaRuntime",
]
