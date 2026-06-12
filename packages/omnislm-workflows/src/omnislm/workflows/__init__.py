"""
OmniSLM Workflows — DAG-based workflow engine.

Build multi-step AI pipelines with branching, merging, and parallel execution.
"""

from omnislm.workflows.dag import DAGWorkflow
from omnislm.workflows.nodes import LLMNode, ToolNode, TransformNode

__all__ = ["DAGWorkflow", "LLMNode", "ToolNode", "TransformNode"]
