"""
OmniSLM Workflow Interfaces.

Contracts for the DAG-based workflow engine.
"""

from abc import ABC, abstractmethod
from typing import Any

from omnislm.core.types import WorkflowState


class BaseNode(ABC):
    """Abstract base class for workflow nodes.

    Nodes are the atomic units of a workflow DAG.
    Each node receives state, performs an action, and returns updated state.
    """

    @property
    @abstractmethod
    def node_id(self) -> str:
        """Unique identifier for this node within a workflow."""

    @property
    @abstractmethod
    def node_type(self) -> str:
        """Type of node (e.g., 'llm', 'tool', 'branch', 'merge', 'transform')."""

    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute this node's logic and return updated state.

        Args:
            state: The current workflow state.

        Returns:
            Updated workflow state after execution.
        """

    def get_dependencies(self) -> list[str]:
        """Return node IDs that must complete before this node runs.

        Override to specify execution ordering in the DAG.
        """
        return []


class BaseWorkflow(ABC):
    """Abstract base class for workflow definitions.

    A workflow is a directed acyclic graph (DAG) of nodes
    that are executed in dependency order.
    """

    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """Unique identifier for this workflow."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable workflow name."""

    @abstractmethod
    def get_nodes(self) -> list[BaseNode]:
        """Return all nodes in this workflow."""

    @abstractmethod
    def get_edges(self) -> list[tuple[str, str]]:
        """Return edges as (source_node_id, target_node_id) tuples."""

    @abstractmethod
    async def execute(
        self, initial_state: WorkflowState | None = None
    ) -> WorkflowState:
        """Execute the full workflow and return final state."""

    @abstractmethod
    def validate(self) -> list[str]:
        """Validate the workflow DAG (check for cycles, missing nodes, etc.).

        Returns:
            List of validation error messages (empty if valid).
        """
