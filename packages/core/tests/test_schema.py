import pytest
from pydantic import ValidationError

from flux_notifier.schema import (
    Action,
    ActionStyle,
    EventType,
    Image,
    JumpTo,
    JumpToType,
    Metadata,
    NotificationPayload,
    Priority,
)


def test_minimal_payload():
    p = NotificationPayload(title="Hello")
    assert p.title == "Hello"
    assert p.version == "1"
    assert p.event_type == EventType.INFO
    assert p.actions == []
    assert p.metadata.priority == Priority.NORMAL
    assert p.id


def test_full_payload():
    p = NotificationPayload(
        event_type=EventType.CHOICE,
        title="Deploy?",
        body="**Ready** to deploy.",
        image=Image(url="https://example.com/img.png", alt="screenshot"),
        actions=[
            Action(
                id="yes",
                label="Deploy",
                style=ActionStyle.PRIMARY,
                jump_to=JumpTo(type=JumpToType.VSCODE, target="vscode://file/main.py"),
            ),
            Action(id="no", label="Cancel", style=ActionStyle.DESTRUCTIVE),
        ],
        metadata=Metadata(source_app="opencode", priority=Priority.HIGH),
    )
    assert p.has_actions is True
    assert len(p.actions) == 2
    assert p.is_urgent is False


def test_urgent_payload():
    p = NotificationPayload(
        title="Critical",
        metadata=Metadata(priority=Priority.URGENT),
    )
    assert p.is_urgent is True


def test_title_required():
    with pytest.raises(ValidationError):
        NotificationPayload()  # type: ignore[call-arg]


def test_title_max_length():
    with pytest.raises(ValidationError):
        NotificationPayload(title="x" * 129)


def test_body_max_length():
    with pytest.raises(ValidationError):
        NotificationPayload(title="t", body="x" * 4097)


def test_actions_max_count():
    with pytest.raises(ValidationError):
        NotificationPayload(
            title="t",
            actions=[Action(id=str(i), label=str(i)) for i in range(6)],
        )


def test_duplicate_action_ids():
    with pytest.raises(ValidationError, match="action ids must be unique"):
        NotificationPayload(
            title="t",
            actions=[
                Action(id="same", label="A"),
                Action(id="same", label="B"),
            ],
        )


def test_unsupported_version():
    with pytest.raises(ValidationError, match="unsupported schema version"):
        NotificationPayload(title="t", version="2")


def test_json_roundtrip():
    p = NotificationPayload(
        title="Roundtrip",
        body="test body",
        event_type=EventType.COMPLETION,
        actions=[Action(id="ok", label="OK")],
    )
    restored = NotificationPayload.model_validate_json(p.model_dump_json())
    assert restored.title == p.title
    assert restored.id == p.id
    assert restored.actions[0].id == "ok"
