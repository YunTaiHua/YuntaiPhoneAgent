"""
工具函数模块测试
测试 yuntai.core.utils 模块
"""
import sys
import shutil
import subprocess
from unittest.mock import patch, MagicMock

import pytest


class TestUtilsInit:
    """测试Utils类初始化"""
    
    def test_utils_init(self):
        """测试Utils类可以正常初始化"""
        from yuntai.core.utils import Utils
        utils = Utils()
        assert utils is not None


class TestEnableWindowsColor:
    """测试Windows颜色启用"""
    
    def test_enable_windows_color_on_windows(self):
        """测试在Windows上启用颜色"""
        from yuntai.core.utils import Utils
        utils = Utils()
        with patch('sys.platform', 'win32'):
            with patch('ctypes.windll.kernel32') as mock_kernel:
                utils.enable_windows_color()
    
    def test_enable_windows_color_on_linux(self):
        """测试在非Windows上不做任何操作"""
        from yuntai.core.utils import Utils
        utils = Utils()
        with patch('sys.platform', 'linux'):
            utils.enable_windows_color()


class TestCheckSystemRequirements:
    """测试系统要求检查"""
    
    def test_check_adb_installed_success(self):
        """测试ADB已安装"""
        from yuntai.core.utils import Utils
        utils = Utils()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Android Debug Bridge version 1.0.41"
        
        with patch('shutil.which', return_value='/usr/bin/adb'):
            with patch('subprocess.run', return_value=mock_result):
                result = utils.check_system_requirements()
                assert result is True
    
    def test_check_adb_not_installed(self):
        """测试ADB未安装"""
        from yuntai.core.utils import Utils
        utils = Utils()
        
        with patch('shutil.which', return_value=None):
            result = utils.check_system_requirements()
            assert result is False
    
    def test_check_adb_timeout(self):
        """测试ADB检查超时"""
        from yuntai.core.utils import Utils
        utils = Utils()
        
        with patch('shutil.which', return_value='/usr/bin/adb'):
            with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('adb', 10)):
                result = utils.check_system_requirements()
                assert result is False


class TestCheckHdc:
    """测试HDC工具检查"""
    
    def test_check_hdc_installed(self):
        """测试HDC已安装"""
        from yuntai.core.utils import Utils
        utils = Utils()
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        
        with patch('shutil.which', return_value='/usr/bin/hdc'):
            with patch('subprocess.run', return_value=mock_result):
                result = utils.check_hdc()
                assert result is True
    
    def test_check_hdc_not_installed(self):
        """测试HDC未安装"""
        from yuntai.core.utils import Utils
        utils = Utils()
        
        with patch('shutil.which', return_value=None):
            result = utils.check_hdc()
            assert result is False
    
    def test_check_hdc_error(self):
        """测试HDC检查出错"""
        from yuntai.core.utils import Utils
        utils = Utils()
        
        with patch('shutil.which', return_value='/usr/bin/hdc'):
            with patch('subprocess.run', side_effect=Exception("Error")):
                result = utils.check_hdc()
                assert result is False


class TestCheckModelApi:
    """测试模型API检查"""
    
    def test_check_model_api_success(self):
        """测试模型API可用"""
        from yuntai.core.utils import Utils
        utils = Utils()
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch('openai.OpenAI', return_value=mock_client):
            result = utils.check_model_api(
                base_url="http://localhost:8000/v1",
                model_name="test-model",
                api_key="test-key"
            )
            assert result is True
    
    def test_check_model_api_failure(self):
        """测试模型API不可用"""
        from yuntai.core.utils import Utils
        utils = Utils()
        
        with patch('openai.OpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create.side_effect = Exception("Connection error")
            result = utils.check_model_api(
                base_url="http://localhost:8000/v1",
                model_name="test-model"
            )
            assert result is False


class TestTTSUtils:
    """测试TTS相关工具函数"""
    
    def test_load_synthesized_files_empty_dir(self, temp_dir):
        """测试从空目录加载合成文件"""
        from yuntai.core.utils import load_synthesized_files
        result = load_synthesized_files(temp_dir)
        assert result == []
    
    def test_load_synthesized_files_with_files(self, temp_dir):
        """测试从有文件的目录加载"""
        import os
        from yuntai.core.utils import load_synthesized_files
        
        for i in range(3):
            filepath = os.path.join(temp_dir, f"audio_{i}.wav")
            with open(filepath, 'w') as f:
                f.write("test")
        
        result = load_synthesized_files(temp_dir)
        assert len(result) == 3
    
    def test_get_current_tts_status(self):
        """测试获取当前TTS状态"""
        from yuntai.core.utils import get_current_tts_status
        
        status = get_current_tts_status()
        assert "tts_page_synthesizing" in status
        assert "is_tts_synthesizing" in status
        assert "is_playing_audio" in status
        assert "tts_synthesized_files_count" in status
    
    def test_cleanup_tts_resources(self):
        """测试清理TTS资源"""
        from yuntai.core.utils import cleanup_tts_resources, tts_synthesized_files
        
        tts_synthesized_files.append(("path1", "file1.wav"))
        tts_synthesized_files.append(("path2", "file2.wav"))
        
        cleanup_tts_resources()
        
        assert len(tts_synthesized_files) == 0


class TestGlobalState:
    """测试全局状态变量"""
    
    def test_initial_tts_synthesizing_state(self):
        """测试初始TTS合成状态"""
        from yuntai.core.utils import tts_page_synthesizing
        assert tts_page_synthesizing is False
    
    def test_initial_playing_audio_state(self):
        """测试初始音频播放状态"""
        from yuntai.core.utils import is_playing_audio
        assert is_playing_audio is False
    
    def test_initial_synthesized_files_state(self):
        """测试初始合成文件列表状态"""
        from yuntai.core.utils import tts_synthesized_files
        assert tts_synthesized_files == []
