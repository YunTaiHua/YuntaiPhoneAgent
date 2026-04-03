def make_state(**overrides):
    state = {
        "task_id": "task-1",
        "status": "pending",
        "retries": 0,
        "context": {},
    }
    state.update(overrides)
    return state
