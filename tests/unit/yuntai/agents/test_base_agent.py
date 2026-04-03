import pytest

from yuntai.agents.base_agent import BaseAgent


class _ConcreteAgent(BaseAgent):
    def invoke(self, input_data):
        return {"echo": input_data}


def test_base_agent_is_abstract():
    with pytest.raises(TypeError):
        BaseAgent()


def test_set_model_updates_model_reference():
    agent = _ConcreteAgent(model="m1")
    assert agent.model == "m1"

    agent.set_model("m2")

    assert agent.model == "m2"


def test_concrete_invoke_path_works():
    agent = _ConcreteAgent()
    payload = {"k": "v"}
    assert agent.invoke(payload) == {"echo": payload}
