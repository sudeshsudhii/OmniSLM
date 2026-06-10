"""
OmniSLM Event Models.

Definitions for domain events in the system.
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


class DocumentIngestedEvent(DomainEvent):
    """Event emitted when a document finishes ingestion."""
    
    event_type: str = "document.ingested"
    document_id: str
    chunks_created: int


class AgentStepCompletedEvent(DomainEvent):
    """Event emitted when an agent completes a ReAct step."""
    
    event_type: str = "agent.step_completed"
    session_id: str
    tool_used: str | None
    observation: str | None
