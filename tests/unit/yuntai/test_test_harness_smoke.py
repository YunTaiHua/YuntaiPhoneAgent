import os


def test_test_env_has_fake_api_key():
    assert os.getenv("ZHIPU_API_KEY") == "test-key"
