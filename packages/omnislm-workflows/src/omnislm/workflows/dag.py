"""
OmniSLM DAG Workflow.

Executes a directed acyclic graph of nodes in topological order.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque

from omnislm.core.exceptions import WorkflowCycleError
from omnislm.core.interfaces.workflow import BaseNode, BaseWorkflow
from omnislm.core.types import WorkflowState

logger = logging.getLogger(__name__)


class DAGWorkflow(BaseWorkflow):
    """A workflow defined as a directed acyclic graph (DAG).

    Nodes are executed in topological order, respecting dependencies.

    Example:
        workflow = DAGWorkflow("my_workflow", "My Pipeline")
        workflow.add_node(extract_node)
        workflow.add_node(transform_node)
        workflow.add_edge("extract", "transform")
        result = await workflow.execute()
    """

    def __init__(self, workflow_id: str, name: str = "") -> None:
        self._workflow_id = workflow_id
        self._name = name or workflow_id
        self._nodes: dict[str, BaseNode] = {}
        self._edges: list[tuple[str, str]] = []

    @property
    def workflow_id(self) -> str:
        return self._workflow_id

    @property
    def name(self) -> str:
        return self._name

    def add_node(self, node: BaseNode) -> "DAGWorkflow":
        """Add a node to the workflow."""
        self._nodes[node.node_id] = node
        return self

    def add_edge(self, from_id: str, to_id: str) -> "DAGWorkflow":
        """Add a dependency edge: from_id must complete before to_id."""
        self._edges.append((from_id, to_id))
        return self

    def get_nodes(self) -> list[BaseNode]:
        return list(self._nodes.values())

    def get_edges(self) -> list[tuple[str, str]]:
        return list(self._edges)

    def validate(self) -> list[str]:
        """Validate the DAG for cycles and missing nodes."""
        errors = []

        # Check for missing nodes in edges
        for src, dst in self._edges:
            if src not in self._nodes:
                errors.append(f"Edge source '{src}' not found in nodes")
            if dst not in self._nodes:
                errors.append(f"Edge target '{dst}' not found in nodes")

        # Check for cycles using Kahn's algorithm
        if not errors:
            try:
                self._topological_sort()
            except WorkflowCycleError:
                errors.append("DAG contains a cycle")

        return errors

    async def execute(
        self, initial_state: WorkflowState | None = None
    ) -> WorkflowState:
        """Execute the workflow in topological order."""
        errors = self.validate()
        if errors:
            raise ValueError(f"Workflow validation failed: {'; '.join(errors)}")

        state = initial_state or WorkflowState()
        execution_order = self._topological_sort()

        logger.info(
            "Executing workflow '%s' (%d nodes)", self._name, len(execution_order)
        )

        for node_id in execution_order:
            node = self._nodes[node_id]
            logger.debug("Executing node: %s (%s)", node_id, node.node_type)

            try:
                state = await node.execute(state)
                state.completed_nodes.append(node_id)
            except Exception as e:
                logger.error("Node '%s' failed: %s", node_id, e)
                state.errors.append(f"Node '{node_id}' failed: {e}")
                break

        return state

    def _topological_sort(self) -> list[str]:
        """Kahn's algorithm for topological sorting."""
        in_degree: dict[str, int] = defaultdict(int)
        adjacency: dict[str, list[str]] = defaultdict(list)

        for node_id in self._nodes:
            in_degree.setdefault(node_id, 0)

        for src, dst in self._edges:
            adjacency[src].append(dst)
            in_degree[dst] += 1

        queue: deque[str] = deque(
            nid for nid, deg in in_degree.items() if deg == 0
        )
        result: list[str] = []

        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            for neighbor in adjacency[node_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self._nodes):
            raise WorkflowCycleError()

        return result
