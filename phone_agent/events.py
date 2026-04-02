"""Structured event primitives for phone agent runtime."""

from __future__ import annotations

import datetime
import logging
import threading
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Callable

logger = logging.getLogger(__name__)


@dataclass
class AgentEvent:
    """Structured runtime event emitted by phone agent."""

    type: str
    payload: dict[str, Any]
    source: str = "phone_agent"
    level: str = "info"
    run_id: str | None = None
    step: int | None = None
    timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["timestamp"] = self.timestamp or datetime.datetime.now().isoformat()
        return data


class AgentEventEmitter:
    """Thread-safe event emitter."""

    def __init__(self) -> None:
        self._listeners: list[Callable[[dict[str, Any]], None]] = []
        self._lock = threading.Lock()

    def on(self, listener: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)

    def off(self, listener: Callable[[dict[str, Any]], None]) -> None:
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)

    def emit(self, event: AgentEvent | dict[str, Any]) -> None:
        payload = event.to_dict() if isinstance(event, AgentEvent) else event
        with self._lock:
            listeners = list(self._listeners)
        for listener in listeners:
            try:
                listener(payload)
            except Exception as exc:
                logger.warning("Agent event listener failed: %s", str(exc))


_GLOBAL_EMITTER = AgentEventEmitter()


def get_global_event_emitter() -> AgentEventEmitter:
    """Return global singleton emitter."""
    return _GLOBAL_EMITTER


def new_run_id() -> str:
    """Create a unique run id for one agent execution."""
    return uuid.uuid4().hex


def emit_agent_event(
    event_type: str,
    payload: dict[str, Any] | None = None,
    *,
    source: str = "phone_agent",
    level: str = "info",
    run_id: str | None = None,
    step: int | None = None,
) -> None:
    """Emit one structured event through the global emitter."""
    _GLOBAL_EMITTER.emit(
        AgentEvent(
            type=event_type,
            payload=payload or {},
            source=source,
            level=level,
            run_id=run_id,
            step=step,
        )
    )
