"""
OmniSLM RAG Pipeline Example.

Demonstrates building a RAG application that ingests documents
and answers questions based on them.

Usage:
    pip install omnislm[rag]
    python rag_pipeline.py
"""

from omnislm import OmniSLM
from omnislm.rag import RAGPipeline
from omnislm.rag.loaders import TextLoader
from omnislm.rag.chunkers import RecursiveChunker
from omnislm.runtimes import OllamaRuntime


async def main():
    """Run a RAG pipeline example."""
    
    # 1. Setup the runtime
    runtime = OllamaRuntime(base_url="http://localhost:11434")
    await runtime.initialize()
    
    # 2. For a full implementation, you'd set up:
    # embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    # vector_store = QdrantAdapter(url="http://localhost:6333")
    # chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=200)
    
    # 3. Create the pipeline
    # pipeline = RAGPipeline(
    #     embedder=embedder,
    #     vector_store=vector_store,
    #     chunker=chunker,
    #     runtime=runtime,
    # )
    
    # 4. Ingest documents
    # await pipeline.ingest([TextLoader("my_document.txt")])
    
    # 5. Query
    # answer = await pipeline.query(
    #     "What is the main topic?",
    #     model="qwen2.5:7b",
    # )
    # print(f"Answer: {answer}")

    print("RAG pipeline example (requires Qdrant + embedder setup)")
    print("See docs for full setup guide.")
    
    await runtime.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
