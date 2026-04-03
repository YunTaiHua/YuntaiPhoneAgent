def make_event(event_type: str = "smoke", payload: dict | None = None) -> dict:
    return {
        "type": event_type,
        "payload": payload or {},
    }
