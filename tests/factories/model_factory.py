class FakeModel:
    def __init__(self, name: str = "fake-model"):
        self.name = name

    def invoke(self, prompt: str) -> dict:
        return {"model": self.name, "prompt": prompt, "content": "ok"}


def make_model(name: str = "fake-model") -> FakeModel:
    return FakeModel(name=name)
