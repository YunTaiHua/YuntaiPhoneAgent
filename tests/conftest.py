"""
共享测试fixtures
提供测试所需的mock对象和临时资源
"""
import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# 设置测试所需的环境变量（必须在导入yuntai模块之前）
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')

import json
import tempfile
from unittest.mock import MagicMock, patch
from typing import Generator

import pytest


@pytest.fixture(scope="session")
def project_root():
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_json_file(temp_dir):
    """创建临时JSON文件"""
    filepath = os.path.join(temp_dir, "test_data.json")
    yield filepath


@pytest.fixture
def temp_history_file(temp_dir):
    """创建临时对话历史文件"""
    filepath = os.path.join(temp_dir, "conversation_history.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({"sessions": [], "free_chats": []}, f)
    yield filepath


@pytest.fixture
def temp_forever_memory_file(temp_dir):
    """创建临时永久记忆文件"""
    filepath = os.path.join(temp_dir, "forever_memory.txt")
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("测试记忆内容\n第二行记忆\n")
    yield filepath


@pytest.fixture
def mock_env_vars():
    """Mock环境变量"""
    env_vars = {
        'ZHIPU_API_KEY': 'test_api_key_12345',
        'GPT_SOVITS_ROOT': '/fake/gpt-sovits',
        'SCRCPY_PATH': '/fake/scrcpy',
        'FFMPEG_PATH': '/fake/ffmpeg',
        'FOREVER_MEMORY_FILE': '/fake/forever.txt',
    }
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_zhipu_client():
    """Mock智谱AI客户端"""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="测试回复内容"))]
    )
    return mock_client


@pytest.fixture
def mock_chat_model():
    """Mock聊天模型"""
    mock_model = MagicMock()
    mock_model.invoke.return_value = MagicMock(content="这是测试回复")
    return mock_model


@pytest.fixture
def mock_file_manager():
    """Mock文件管理器"""
    manager = MagicMock()
    manager.read_forever_memory.return_value = "测试永久记忆内容"
    manager.get_recent_free_chats.return_value = [
        {"user_input": "你好", "assistant_reply": "你好呀！", "timestamp": "2026-01-01 12:00:00"}
    ]
    manager.get_recent_conversation_history.return_value = []
    manager.save_conversation_history.return_value = None
    return manager


@pytest.fixture
def mock_tts_manager():
    """Mock TTS管理器"""
    manager = MagicMock()
    manager.tts_enabled = False
    manager.speak_text_intelligently.return_value = None
    return manager


@pytest.fixture
def sample_conversation_history():
    """示例对话历史数据"""
    return {
        "sessions": [
            {
                "type": "chat_session",
                "timestamp": "2026-01-15 10:30:00",
                "target_app": "微信",
                "target_object": "张三",
                "reply_generated": "好的，明天见！",
                "cycle": 1
            },
            {
                "type": "chat_session",
                "timestamp": "2026-01-15 09:00:00",
                "target_app": "QQ",
                "target_object": "李四",
                "reply_generated": "收到，谢谢！",
                "cycle": 1
            }
        ],
        "free_chats": [
            {
                "type": "free_chat",
                "timestamp": "2026-01-15 08:00:00",
                "user_input": "今天天气怎么样？",
                "assistant_reply": "今天是个晴天，温度适宜。"
            },
            {
                "type": "free_chat",
                "timestamp": "2026-01-14 20:00:00",
                "user_input": "帮我写一首诗",
                "assistant_reply": "春风拂面花满枝，..."
            }
        ]
    }


@pytest.fixture
def sample_chat_history():
    """示例聊天历史列表"""
    return [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"},
        {"role": "user", "content": "今天天气如何"},
        {"role": "assistant", "content": "今天天气晴朗，温度适宜。"},
    ]


@pytest.fixture(autouse=True)
def reset_global_state():
    """重置全局状态"""
    yield
    import yuntai.core.utils as utils_module
    utils_module.tts_page_synthesizing = False
    utils_module.is_tts_synthesizing = False
    utils_module.is_playing_audio = False
    utils_module.tts_synthesized_files = []


def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
