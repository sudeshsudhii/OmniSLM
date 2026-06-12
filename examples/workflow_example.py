"""
OmniSLM Workflow Example.

Demonstrates building a multi-step DAG workflow.

Usage:
    pip install omnislm[workflows]
    python workflow_example.py
"""

import asyncio
from omnislm.core.types import WorkflowState
from omnislm.workflows import DAGWorkflow, TransformNode


def extract_step(state: WorkflowState) -> WorkflowState:
    """Extract data."""
    state.set("raw_text", "The quick brown fox jumps over the lazy dog.")
    return state


def transform_step(state: WorkflowState) -> WorkflowState:
    """Transform data."""
    raw = state.get("raw_text", "")
    state.set("word_count", len(raw.split()))
    state.set("uppercase", raw.upper())
    return state


def summarize_step(state: WorkflowState) -> WorkflowState:
    """Summarize results."""
    state.set("summary", f"Processed {state.get('word_count')} words")
    return state


async def main():
    """Run a workflow example."""
    
    # Build the DAG
    workflow = DAGWorkflow("text_pipeline", "Text Processing Pipeline")
    
    workflow.add_node(TransformNode("extract", extract_step))
    workflow.add_node(TransformNode("transform", transform_step, dependencies=["extract"]))
    workflow.add_node(TransformNode("summarize", summarize_step, dependencies=["transform"]))
    
    workflow.add_edge("extract", "transform")
    workflow.add_edge("transform", "summarize")
    
    # Validate
    errors = workflow.validate()
    if errors:
        print(f"Validation errors: {errors}")
        return
    
    # Execute
    print("🔄 Running workflow...")
    result = await workflow.execute()
    
    print(f"Summary: {result.get('summary')}")
    print(f"Word count: {result.get('word_count')}")
    print(f"Uppercase: {result.get('uppercase')}")
    print(f"Completed nodes: {result.completed_nodes}")


if __name__ == "__main__":
    asyncio.run(main())
