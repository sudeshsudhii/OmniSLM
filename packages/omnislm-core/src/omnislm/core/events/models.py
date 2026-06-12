"""
OmniSLM Event Models.

Definitions for domain events across the framework.
"""

from datetime import datetime, timezone
from typing import Any
import uuid

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    event_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str


# ---- Document Events ----


class DocumentIngestedEvent(DomainEvent):
    """Emitted when a document finishes ingestion."""

    event_type: str = "document.ingested"
    document_id: str
    chunks_created: int
    collection: str = ""


# ---- Agent Events ----


class AgentStepCompletedEvent(DomainEvent):
    """Emitted when an agent completes a reasoning step."""

    event_type: str = "agent.step_completed"
    agent_name: str
    session_id: str
    step_number: int = 0
    tool_used: str | None = None
    observation: str | None = None


class AgentRunCompletedEvent(DomainEvent):
    """Emitted when an agent finishes running."""

    event_type: str = "agent.run_completed"
    agent_name: str
    session_id: str
    total_steps: int = 0
    success: bool = True


# ---- Runtime Events ----


class RuntimeConnectedEvent(DomainEvent):
    """Emitted when a runtime becomes available."""

    event_type: str = "runtime.connected"
    runtime_name: str


class RuntimeDisconnectedEvent(DomainEvent):
    """Emitted when a runtime becomes unavailable."""

    event_type: str = "runtime.disconnected"
    runtime_name: str
    reason: str = ""


# ---- Plugin Events ----


class PluginLoadedEvent(DomainEvent):
    """Emitted when a plugin is loaded."""

    event_type: str = "plugin.loaded"
    plugin_name: str
    plugin_version: str = ""


class PluginErrorEvent(DomainEvent):
    """Emitted when a plugin encounters an error."""

    event_type: str = "plugin.error"
    plugin_name: str
    error_message: str


# ---- Memory Events ----


class MemoryAddedEvent(DomainEvent):
    """Emitted when a memory is stored."""

    event_type: str = "memory.added"
    session_id: str
    memory_tier: str
    content_length: int = 0


# ---- Workflow Events ----


class WorkflowStartedEvent(DomainEvent):
    """Emitted when a workflow begins execution."""

    event_type: str = "workflow.started"
    workflow_id: str
    workflow_name: str = ""


class WorkflowCompletedEvent(DomainEvent):
    """Emitted when a workflow finishes execution."""

    event_type: str = "workflow.completed"
    workflow_id: str
    workflow_name: str = ""
    success: bool = True
    nodes_executed: int = 0
