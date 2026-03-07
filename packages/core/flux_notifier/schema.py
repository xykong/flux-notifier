from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


class EventType(StrEnum):
    COMPLETION = "completion"
    CHOICE = "choice"
    STEP = "step"
    INPUT_REQUIRED = "input_required"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class ActionStyle(StrEnum):
    PRIMARY = "primary"
    DESTRUCTIVE = "destructive"
    DEFAULT = "default"


class JumpToType(StrEnum):
    URL = "url"
    VSCODE = "vscode"
    PYCHARM = "pycharm"
    TERMINAL = "terminal"


class Priority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class JumpTo(BaseModel):
    type: JumpToType
    target: str


class Action(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=64)
    style: ActionStyle = ActionStyle.DEFAULT
    jump_to: JumpTo | None = None


class Image(BaseModel):
    url: str
    alt: str | None = None
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)


class Metadata(BaseModel):
    source_app: str | None = None
    session_id: str | None = None
    priority: Priority = Priority.NORMAL
    ttl: int | None = Field(default=None, gt=0)
    tags: list[str] = Field(default_factory=list)


class NotificationPayload(BaseModel):
    version: str = "1"
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: EventType = EventType.INFO
    title: Annotated[str, Field(min_length=1, max_length=128)]
    body: str | None = Field(default=None, max_length=4096)
    image: Image | None = None
    actions: list[Action] = Field(default_factory=list, max_length=5)
    metadata: Metadata = Field(default_factory=Metadata)

    @field_validator("version")
    @classmethod
    def version_must_be_supported(cls, v: str) -> str:
        if v != "1":
            raise ValueError(f"unsupported schema version: {v!r} (only '1' is supported)")
        return v

    @model_validator(mode="after")
    def action_ids_must_be_unique(self) -> NotificationPayload:
        ids = [a.id for a in self.actions]
        if len(ids) != len(set(ids)):
            raise ValueError("action ids must be unique within a notification")
        return self

    @property
    def has_actions(self) -> bool:
        return len(self.actions) > 0

    @property
    def is_urgent(self) -> bool:
        return self.metadata.priority == Priority.URGENT


class UserResponse(BaseModel):
    notification_id: str
    action_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_terminal: str | None = None
    timeout: bool = False


class DeliveryResult(BaseModel):
    notification_id: str
    delivered: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
