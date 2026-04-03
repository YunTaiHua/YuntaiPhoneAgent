import yuntai.models.zhipu_model as zm


def test_get_zhipu_client_is_singleton(monkeypatch):
    created = []

    class _Client:
        def __init__(self, api_key):
            created.append(api_key)

    monkeypatch.setattr(zm, "ZhipuAI", _Client)
    zm._zhipu_client = None

    c1 = zm.get_zhipu_client()
    c2 = zm.get_zhipu_client()

    assert c1 is c2
    assert created == [zm.ZHIPU_API_KEY]


def test_get_models_create_expected_chatopenai_configs(monkeypatch):
    captured = []

    class _Model:
        def __init__(self, **kwargs):
            captured.append(kwargs)

    monkeypatch.setattr(zm, "ChatOpenAI", _Model)

    jm = zm.get_judgement_model()
    cm = zm.get_chat_model()
    pm = zm.get_phone_model()

    assert jm is not None and cm is not None and pm is not None
    assert captured[0]["model"] == zm.ZHIPU_JUDGEMENT_MODEL
    assert captured[0]["temperature"] == 0.1
    assert captured[1]["model"] == zm.ZHIPU_CHAT_MODEL
    assert captured[1]["temperature"] == 0.7
    assert captured[2]["model"] == zm.ZHIPU_MODEL
    assert captured[2]["temperature"] == 0.3
    assert all(item["base_url"] == zm.ZHIPU_API_BASE_URL for item in captured)


def test_zhipu_model_config_info_contains_all_models():
    info = zm.ZhipuModelConfig.get_model_info()
    assert info == {
        "judgement_model": zm.ZhipuModelConfig.JUDGEMENT_MODEL,
        "chat_model": zm.ZhipuModelConfig.CHAT_MODEL,
        "phone_model": zm.ZhipuModelConfig.PHONE_MODEL,
    }
