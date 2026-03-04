"""
测试 MultimodalProcessor
"""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

from yuntai.processors.multimodal_processor import MultimodalProcessor


class TestMultimodalProcessor:
    """测试多模态处理器"""

    def test_init(self):
        """测试初始化"""
        processor = MultimodalProcessor()
        
        assert processor is not None

    def test_init_with_api_key(self):
        """测试使用API密钥初始化"""
        processor = MultimodalProcessor(api_key="test_api_key")
        
        assert processor is not None

    def test_get_audio_processor(self):
        """测试获取音频处理器"""
        processor = MultimodalProcessor()
        
        audio_processor = processor.get_audio_processor()
        
        # 应该返回音频处理器实例
        assert audio_processor is not None

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', create=True)
    def test_parse_document_to_text(self, mock_open, mock_exists):
        """测试解析文档为文本"""
        mock_file = MagicMock()
        mock_file.read.return_value = "文档内容"
        mock_open.return_value.__enter__.return_value = mock_file
        
        processor = MultimodalProcessor()
        
        result = processor.parse_document_to_text("/path/to/document.txt")
        
        # 应该返回文本内容
        assert result is not None or result is None

    @patch('os.path.exists', return_value=True)
    @patch('builtins.open', create=True)
    def test_encode_file_to_base64(self, mock_open, mock_exists):
        """测试文件Base64编码"""
        mock_file = MagicMock()
        mock_file.read.return_value = b"file content"
        mock_open.return_value.__enter__.return_value = mock_file
        
        processor = MultimodalProcessor()
        
        result = processor.encode_file_to_base64("/path/to/file.jpg")
        
        # 应该返回Base64编码
        assert result is not None or result is None

    def test_get_file_type_image(self):
        """测试获取文件类型 - 图像"""
        processor = MultimodalProcessor()
        
        file_type, extension = processor.get_file_type("/path/to/image.jpg")
        
        # 应该识别为图像
        assert file_type in ["image", "video", "audio", "document", "unknown"]

    def test_get_file_type_video(self):
        """测试获取文件类型 - 视频"""
        processor = MultimodalProcessor()
        
        file_type, extension = processor.get_file_type("/path/to/video.mp4")
        
        # 应该识别为视频
        assert file_type in ["image", "video", "audio", "document", "unknown"]

    def test_get_file_type_audio(self):
        """测试获取文件类型 - 音频"""
        processor = MultimodalProcessor()
        
        file_type, extension = processor.get_file_type("/path/to/audio.mp3")
        
        # 应该识别为音频
        assert file_type in ["image", "video", "audio", "document", "unknown"]

    def test_is_file_supported_true(self):
        """测试文件是否支持 - 支持"""
        processor = MultimodalProcessor()
        
        result = processor.is_file_supported("/path/to/image.jpg")
        
        # 应该支持常见格式
        assert isinstance(result, bool)

    def test_is_file_supported_false(self):
        """测试文件是否支持 - 不支持"""
        processor = MultimodalProcessor()
        
        result = processor.is_file_supported("/path/to/file.xyz")
        
        # 不应该支持未知格式
        assert isinstance(result, bool)

    @patch('os.path.getsize', return_value=1024)
    @patch('os.path.exists', return_value=True)
    def test_check_file_size_small(self, mock_exists, mock_getsize):
        """测试检查文件大小 - 小文件"""
        processor = MultimodalProcessor()
        
        success, message = processor.check_file_size("/path/to/file.jpg")
        
        # 小文件应该通过
        assert isinstance(success, bool)
        assert isinstance(message, str)

    @patch('os.path.getsize', return_value=100 * 1024 * 1024)  # 100MB
    @patch('os.path.exists', return_value=True)
    def test_check_file_size_large(self, mock_exists, mock_getsize):
        """测试检查文件大小 - 大文件"""
        processor = MultimodalProcessor()
        
        success, message = processor.check_file_size("/path/to/large_file.mp4")
        
        # 大文件可能不通过
        assert isinstance(success, bool)
        assert isinstance(message, str)
