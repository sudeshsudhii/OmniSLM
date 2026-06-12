"""
OmniSLM RAG — Retrieval-Augmented Generation pipeline.

Provides loaders, chunkers, embedders, retrievers, rerankers,
and vector store adapters for building RAG applications.
"""

from omnislm.rag.pipeline import RAGPipeline

__all__ = ["RAGPipeline"]
