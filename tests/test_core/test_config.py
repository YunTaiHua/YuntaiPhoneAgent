"""
配置模块测试
测试 yuntai.core.config 模块
"""
import os
import sys
from unittest.mock import patch, MagicMock

import pytest


class TestAppVersion:
    """测试应用版本号"""
    
    def test_app_version_format(self, mock_env_vars):
        """测试版本号格式正确"""
        from yuntai.core.config import APP_VERSION
        parts = APP_VERSION.split('.')
        assert len(parts) == 3
        for part in parts:
            assert part.isdigit()


class TestThemeColors:
    """测试主题颜色配置"""
    
    def test_primary_color(self, mock_env_vars):
        """测试主色调"""
        from yuntai.core.config import ThemeColors
        assert ThemeColors.PRIMARY == "#4361ee"
    
    def test_secondary_color(self, mock_env_vars):
        """测试次要色调"""
        from yuntai.core.config import ThemeColors
        assert ThemeColors.SECONDARY == "#7209b7"
    
    def test_all_colors_are_hex(self, mock_env_vars):
        """测试所有颜色都是有效的十六进制格式"""
        from yuntai.core.config import ThemeColors
        color_attrs = ['PRIMARY', 'SECONDARY', 'ACCENT', 'SUCCESS', 
                       'WARNING', 'DANGER', 'BG_DARK', 'BG_CARD', 
                       'BG_HOVER', 'TEXT_PRIMARY', 'TEXT_SECONDARY', 'TEXT_DISABLED']
        for attr in color_attrs:
            color = getattr(ThemeColors, attr)
            assert color.startswith('#'), f"{attr} should start with #"
            assert len(color) == 7, f"{attr} should be 7 characters long"


class TestShortcuts:
    """测试快捷键配置"""
    
    def test_shortcuts_dictionary_exists(self, mock_env_vars):
        """测试快捷键字典存在"""
        from yuntai.core.config import SHORTCUTS
        assert isinstance(SHORTCUTS, dict)
        assert len(SHORTCUTS) > 0
    
    def test_shortcut_keys_are_single_char(self, mock_env_vars):
        """测试快捷键都是单字符"""
        from yuntai.core.config import SHORTCUTS
        for key in SHORTCUTS.keys():
            assert len(key) == 1, f"Shortcut key '{key}' should be single character"
    
    def test_shortcut_values_are_valid(self, mock_env_vars):
        """测试快捷键值都是打开应用的指令"""
        from yuntai.core.config import SHORTCUTS
        for key, value in SHORTCUTS.items():
            assert '打开' in value, f"Shortcut {key}: {value} should contain '打开'"


class TestSystemConfig:
    """测试系统配置"""
    
    def test_max_history_length(self, mock_env_vars):
        """测试历史记录最大长度"""
        from yuntai.core.config import MAX_HISTORY_LENGTH
        assert MAX_HISTORY_LENGTH == 50
    
    def test_max_cycle_times(self, mock_env_vars):
        """测试最大循环次数"""
        from yuntai.core.config import MAX_CYCLE_TIMES
        assert MAX_CYCLE_TIMES == 30
    
    def test_max_retry_times(self, mock_env_vars):
        """测试最大重试次数"""
        from yuntai.core.config import MAX_RETRY_TIMES
        assert MAX_RETRY_TIMES == 3
    
    def test_wait_interval(self, mock_env_vars):
        """测试等待间隔"""
        from yuntai.core.config import WAIT_INTERVAL
        assert WAIT_INTERVAL == 1


class TestTTSConfig:
    """测试TTS配置"""
    
    def test_tts_ref_language(self, mock_env_vars):
        """测试TTS参考语言"""
        from yuntai.core.config import TTS_REF_LANGUAGE
        assert TTS_REF_LANGUAGE == "中文"
    
    def test_tts_target_language(self, mock_env_vars):
        """测试TTS目标语言"""
        from yuntai.core.config import TTS_TARGET_LANGUAGE
        assert TTS_TARGET_LANGUAGE == "中文"
    
    def test_tts_max_segment_length(self, mock_env_vars):
        """测试TTS最大分段长度"""
        from yuntai.core.config import TTS_MAX_SEGMENT_LENGTH
        assert TTS_MAX_SEGMENT_LENGTH == 500
    
    def test_tts_enable_parallel(self, mock_env_vars):
        """测试TTS并行合成开关"""
        from yuntai.core.config import TTS_ENABLE_PARALLEL
        assert TTS_ENABLE_PARALLEL is True


class TestModelConfig:
    """测试模型配置"""
    
    def test_zhipu_model_names(self, mock_env_vars):
        """测试智谱模型名称"""
        from yuntai.core.config import ZHIPU_MODEL, ZHIPU_CHAT_MODEL, ZHIPU_JUDGEMENT_MODEL
        assert ZHIPU_MODEL == "autoglm-phone"
        assert ZHIPU_CHAT_MODEL == "glm-4.6v-flash"
        assert ZHIPU_JUDGEMENT_MODEL == "glm-4.6v-flash"
    
    def test_zhipu_api_base_url(self, mock_env_vars):
        """测试智谱API基础URL"""
        from yuntai.core.config import ZHIPU_API_BASE_URL
        assert "bigmodel.cn" in ZHIPU_API_BASE_URL


class TestFileExtensions:
    """测试文件扩展名配置"""
    
    def test_allowed_image_extensions(self, mock_env_vars):
        """测试允许的图片扩展名"""
        from yuntai.core.config import ALLOWED_IMAGE_EXTENSIONS
        assert '.jpg' in ALLOWED_IMAGE_EXTENSIONS
        assert '.png' in ALLOWED_IMAGE_EXTENSIONS
        assert '.gif' in ALLOWED_IMAGE_EXTENSIONS
    
    def test_allowed_video_extensions(self, mock_env_vars):
        """测试允许的视频扩展名"""
        from yuntai.core.config import ALLOWED_VIDEO_EXTENSIONS
        assert '.mp4' in ALLOWED_VIDEO_EXTENSIONS
        assert '.avi' in ALLOWED_VIDEO_EXTENSIONS
    
    def test_allowed_audio_extensions(self, mock_env_vars):
        """测试允许的音频扩展名"""
        from yuntai.core.config import ALLOWED_AUDIO_EXTENSIONS
        assert '.mp3' in ALLOWED_AUDIO_EXTENSIONS
        assert '.wav' in ALLOWED_AUDIO_EXTENSIONS


class TestDeviceTypeConfig:
    """测试设备类型配置"""
    
    def test_device_type_constants(self, mock_env_vars):
        """测试设备类型常量"""
        from yuntai.core.config import DEVICE_TYPE_ANDROID, DEVICE_TYPE_HARMONY
        assert DEVICE_TYPE_ANDROID == "android"
        assert DEVICE_TYPE_HARMONY == "harmony"


class TestValidateConfig:
    """测试配置验证函数"""
    
    def test_validate_config_with_missing_paths(self, mock_env_vars):
        """测试缺少路径时的配置验证"""
        from yuntai.core.config import validate_config
        with patch('os.path.exists', return_value=False):
            result = validate_config()
            assert result is False
    
    def test_validate_config_with_all_valid(self, mock_env_vars):
        """测试所有配置有效时的验证"""
        from yuntai.core.config import validate_config
        with patch('os.path.exists', return_value=True):
            result = validate_config()
            assert result is True


class TestCheckRequiredEnvVars:
    """测试必需环境变量检查"""
    
    def test_check_required_env_vars_missing(self):
        """测试缺少必需环境变量时抛出异常"""
        with patch.dict(os.environ, {}, clear=True):
            from yuntai.core.config import check_required_env_vars
            with pytest.raises(ValueError) as excinfo:
                check_required_env_vars()
            assert "ZHIPU_API_KEY" in str(excinfo.value)
    
    def test_check_required_env_vars_present(self, mock_env_vars):
        """测试存在必需环境变量时正常通过"""
        from yuntai.core.config import check_required_env_vars
        check_required_env_vars()
