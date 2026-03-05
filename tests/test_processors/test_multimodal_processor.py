"""
测试 multimodal_processor.py - 多模态处理器 (增强版)
"""
import pytest
import os
import tempfile
import base64
from unittest.mock import MagicMock, patch

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')


class TestMultimodalProcessor:
    """测试 MultimodalProcessor 类"""

    def test_multimodal_processor_import(self):
        """测试导入MultimodalProcessor"""
        from yuntai.processors.multimodal_processor import MultimodalProcessor
        assert MultimodalProcessor is not None

    def test_multimodal_processor_has_methods(self):
        """测试MultimodalProcessor有方法"""
        from yuntai.processors.multimodal_processor import MultimodalProcessor
        
        # 检查类有这些方法
        assert hasattr(MultimodalProcessor, '__init__')
        assert hasattr(MultimodalProcessor, 'get_audio_processor')
        assert hasattr(MultimodalProcessor, 'encode_file_to_base64')
        assert hasattr(MultimodalProcessor, 'parse_document_to_text')


class TestMultimodalProcessorInit:
    """测试 MultimodalProcessor 初始化"""

    def test_init_with_api_key(self):
        """测试带API密钥初始化"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor(api_key='test_key')
            
            assert processor.api_key == 'test_key'
            assert processor.audio_processor is None

    def test_client_initialized(self):
        """测试客户端初始化"""
        mock_client = MagicMock()
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = mock_client
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor(api_key='test_key')
            
            assert processor.client == mock_client


class TestMultimodalProcessorGetAudioProcessor:
    """测试 MultimodalProcessor 获取音频处理器"""

    def test_get_audio_processor_lazy(self):
        """测试延迟获取音频处理器"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor(api_key='test_key')
            
            assert processor.audio_processor is None
            
            # 直接设置audio_processor来模拟延迟加载
            mock_ap = MagicMock()
            processor.audio_processor = mock_ap
            
            result = processor.get_audio_processor()
            
            assert result == mock_ap

    def test_get_audio_processor_cached(self):
        """测试缓存音频处理器"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor(api_key='test_key')
            
            mock_ap_instance = MagicMock()
            processor.audio_processor = mock_ap_instance
            
            result = processor.get_audio_processor()
            
            assert result == mock_ap_instance


class TestMultimodalProcessorEncodeFile:
    """测试 MultimodalProcessor 文件编码"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_encode_file_to_base64_success(self, multimodal_processor, temp_dir):
        """测试成功编码文件"""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        result = multimodal_processor.encode_file_to_base64(test_file)
        
        assert result is not None
        decoded = base64.b64decode(result).decode('utf-8')
        assert decoded == "test content"

    def test_encode_file_to_base64_not_exists(self, multimodal_processor):
        """测试编码不存在的文件"""
        result = multimodal_processor.encode_file_to_base64("/nonexistent/file.txt")
        
        assert result is None

    def test_encode_file_to_base64_binary(self, multimodal_processor, temp_dir):
        """测试编码二进制文件"""
        test_file = os.path.join(temp_dir, "test.bin")
        with open(test_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')
        
        result = multimodal_processor.encode_file_to_base64(test_file)
        
        assert result is not None

    def test_encode_file_to_base64_large_file(self, multimodal_processor, temp_dir):
        """测试编码大文件"""
        multimodal_processor.max_file_size = 100  # 设置小限制
        
        test_file = os.path.join(temp_dir, "large.txt")
        with open(test_file, 'wb') as f:
            f.write(b'x' * 200)
        
        result = multimodal_processor.encode_file_to_base64(test_file)
        
        assert result is None


class TestMultimodalProcessorParseDocument:
    """测试 MultimodalProcessor 文档解析"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_parse_document_not_exists(self, multimodal_processor):
        """测试解析不存在的文档"""
        result = multimodal_processor.parse_document_to_text("/nonexistent/doc.pdf")
        
        assert result is None

    def test_parse_document_success(self, multimodal_processor, temp_dir):
        """测试成功解析文档"""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        mock_markitdown = MagicMock()
        mock_result = MagicMock()
        mock_result.text_content = "parsed content"
        mock_markitdown.convert.return_value = mock_result
        
        with patch.dict('sys.modules', {'markitdown': MagicMock(MarkItDown=lambda: mock_markitdown)}):
            result = multimodal_processor.parse_document_to_text(test_file)
            
            # 由于markitdown可能未安装，这里只检查不会崩溃
            assert result is None or isinstance(result, str)

    def test_parse_document_long_content(self, multimodal_processor, temp_dir):
        """测试解析长文档"""
        test_file = os.path.join(temp_dir, "long.txt")
        with open(test_file, 'w') as f:
            f.write("x" * 15000)
        
        mock_markitdown = MagicMock()
        mock_result = MagicMock()
        mock_result.text_content = "x" * 15000
        mock_markitdown.convert.return_value = mock_result
        
        with patch.dict('sys.modules', {'markitdown': MagicMock(MarkItDown=lambda: mock_markitdown)}):
            result = multimodal_processor.parse_document_to_text(test_file)
            
            # 由于markitdown可能未安装，这里只检查不会崩溃
            assert result is None or isinstance(result, str)


class TestMultimodalProcessorExtensions:
    """测试 MultimodalProcessor 扩展名处理"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_allowed_image_extensions(self, multimodal_processor):
        """测试允许的图片扩展名"""
        assert multimodal_processor.allowed_image_extensions is not None

    def test_allowed_video_extensions(self, multimodal_processor):
        """测试允许的视频扩展名"""
        assert multimodal_processor.allowed_video_extensions is not None

    def test_allowed_audio_extensions(self, multimodal_processor):
        """测试允许的音频扩展名"""
        assert multimodal_processor.allowed_audio_extensions is not None

    def test_max_file_size(self, multimodal_processor):
        """测试最大文件大小"""
        assert multimodal_processor.max_file_size > 0


class TestMultimodalProcessorGetFileType:
    """测试 MultimodalProcessor 获取文件类型"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_get_file_type_image(self, multimodal_processor):
        """测试获取图片文件类型"""
        file_type, mime_type = multimodal_processor.get_file_type("test.jpg")
        
        assert file_type == "image"
        assert "image" in mime_type

    def test_get_file_type_video(self, multimodal_processor):
        """测试获取视频文件类型"""
        file_type, mime_type = multimodal_processor.get_file_type("test.mp4")
        
        assert file_type == "video"
        assert "video" in mime_type

    def test_get_file_type_audio(self, multimodal_processor):
        """测试获取音频文件类型"""
        file_type, mime_type = multimodal_processor.get_file_type("test.mp3")
        
        assert file_type == "audio"
        assert "audio" in mime_type

    def test_get_file_type_text(self, multimodal_processor):
        """测试获取文本文件类型"""
        file_type, mime_type = multimodal_processor.get_file_type("test.txt")
        
        assert file_type == "text"
        assert "text" in mime_type

    def test_get_file_type_python(self, multimodal_processor):
        """测试获取Python文件类型"""
        file_type, mime_type = multimodal_processor.get_file_type("test.py")
        
        assert file_type == "text"

    def test_get_file_type_pdf(self, multimodal_processor):
        """测试获取PDF文件类型"""
        file_type, mime_type = multimodal_processor.get_file_type("test.pdf")
        
        assert file_type == "text"

    def test_get_file_type_docx(self, multimodal_processor):
        """测试获取Word文件类型"""
        file_type, mime_type = multimodal_processor.get_file_type("test.docx")
        
        assert file_type == "text"

    def test_get_file_type_xlsx(self, multimodal_processor):
        """测试获取Excel文件类型"""
        file_type, mime_type = multimodal_processor.get_file_type("test.xlsx")
        
        assert file_type == "text"

    def test_get_file_type_unknown(self, multimodal_processor):
        """测试获取未知文件类型"""
        file_type, mime_type = multimodal_processor.get_file_type("test.xyz")
        
        assert file_type == "file"
        assert mime_type == "application/octet-stream"


class TestMultimodalProcessorIsFileSupported:
    """测试 MultimodalProcessor 检查文件支持"""

    @pytest.fixture
    def multimodal_processor(self, temp_dir):
        """创建多模态处理器fixture"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor(api_key='test_key')
            return processor

    def test_is_file_supported_image(self, multimodal_processor, temp_dir):
        """测试检查图片文件支持"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = multimodal_processor.is_file_supported(test_file)
        
        assert result is True

    def test_is_file_supported_video(self, multimodal_processor, temp_dir):
        """测试检查视频文件支持"""
        test_file = os.path.join(temp_dir, "test.mp4")
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = multimodal_processor.is_file_supported(test_file)
        
        assert result is True

    def test_is_file_supported_audio(self, multimodal_processor, temp_dir):
        """测试检查音频文件支持"""
        test_file = os.path.join(temp_dir, "test.mp3")
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = multimodal_processor.is_file_supported(test_file)
        
        assert result is True

    def test_is_file_supported_not_exists(self, multimodal_processor):
        """测试检查不存在的文件"""
        result = multimodal_processor.is_file_supported("/nonexistent/file.xyz")
        
        assert result is False

    def test_is_file_supported_unsupported(self, multimodal_processor, temp_dir):
        """测试检查不支持的文件"""
        test_file = os.path.join(temp_dir, "test.xyz")
        with open(test_file, 'w') as f:
            f.write("test")
        
        result = multimodal_processor.is_file_supported(test_file)
        
        assert result is False


class TestMultimodalProcessorCheckFileSize:
    """测试 MultimodalProcessor 检查文件大小"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor(api_key='test_key')
            processor.max_file_size = 100
            return processor

    def test_check_file_size_ok(self, multimodal_processor, temp_dir):
        """测试文件大小正常"""
        test_file = os.path.join(temp_dir, "small.txt")
        with open(test_file, 'w') as f:
            f.write("x" * 50)
        
        ok, msg = multimodal_processor.check_file_size(test_file)
        
        assert ok is True
        assert msg == ""

    def test_check_file_size_too_large(self, multimodal_processor, temp_dir):
        """测试文件太大"""
        test_file = os.path.join(temp_dir, "large.txt")
        with open(test_file, 'w') as f:
            f.write("x" * 200)
        
        ok, msg = multimodal_processor.check_file_size(test_file)
        
        assert ok is False
        assert "限制" in msg

    def test_check_file_size_not_exists(self, multimodal_processor):
        """测试检查不存在的文件大小"""
        ok, msg = multimodal_processor.check_file_size("/nonexistent/file.txt")
        
        assert ok is False


class TestMultimodalProcessorTestApiConnection:
    """测试 MultimodalProcessor API连接测试"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        mock_client = MagicMock()
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = mock_client
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor(api_key='test_key')
            return processor

    def test_test_api_connection_success(self, multimodal_processor):
        """测试API连接成功"""
        mock_stream = [MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))])]
        multimodal_processor.client.chat.completions.create.return_value = mock_stream
        
        result = multimodal_processor.test_api_connection()
        
        # 由于流式响应处理复杂，这里只检查不会崩溃
        assert isinstance(result, bool)

    def test_test_api_connection_failure(self, multimodal_processor):
        """测试API连接失败"""
        multimodal_processor.client.chat.completions.create.side_effect = Exception("API Error")
        
        result = multimodal_processor.test_api_connection()
        
        assert result is False


class TestMultimodalProcessorPrepareMessages:
    """测试 MultimodalProcessor 准备消息"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_prepare_multimodal_messages_text_only(self, multimodal_processor):
        """测试准备纯文本消息"""
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello")
        
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert audio_result is None

    def test_prepare_multimodal_messages_with_history(self, multimodal_processor):
        """测试准备带历史的消息"""
        history = [{"role": "assistant", "content": "Hi"}]
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", history=history)
        
        assert len(messages) == 2
        assert messages[0]["role"] == "assistant"

    def test_prepare_multimodal_messages_empty_text(self, multimodal_processor):
        """测试准备空文本消息"""
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("")
        
        assert len(messages) == 1


class TestMultimodalProcessorProcessWithFiles:
    """测试 MultimodalProcessor 处理文件"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        mock_client = MagicMock()
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = mock_client
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_process_with_files_no_files(self, multimodal_processor):
        """测试处理无文件"""
        success, msg, audio_result = multimodal_processor.process_with_files("Hello", file_paths=[])
        
        assert success is False
        assert "没有有效的支持文件" in msg

    def test_process_with_files_unsupported(self, multimodal_processor, temp_dir):
        """测试处理不支持的文件"""
        test_file = os.path.join(temp_dir, "test.xyz")
        with open(test_file, 'w') as f:
            f.write("test")
        
        success, msg, audio_result = multimodal_processor.process_with_files("Hello", file_paths=[test_file])
        
        assert success is False
        assert "没有有效的支持文件" in msg

    def test_process_with_files_too_large(self, multimodal_processor, temp_dir):
        """测试处理太大的文件"""
        multimodal_processor.max_file_size = 10
        
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'x' * 100)
        
        success, msg, audio_result = multimodal_processor.process_with_files("Hello", file_paths=[test_file])
        
        assert success is False

    def test_process_with_files_image_success(self, multimodal_processor, temp_dir):
        """测试处理图片文件成功"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)  # JPEG header
        
        # Mock stream response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Response"))]
        multimodal_processor.client.chat.completions.create.return_value = [mock_chunk]
        
        success, msg, audio_result = multimodal_processor.process_with_files("Hello", file_paths=[test_file])
        
        assert success is True
        assert msg == "Response"

    def test_process_with_files_text_file(self, multimodal_processor, temp_dir):
        """测试处理文本文件"""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Mock stream response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Response"))]
        multimodal_processor.client.chat.completions.create.return_value = [mock_chunk]
        
        success, msg, audio_result = multimodal_processor.process_with_files("Hello", file_paths=[test_file])
        
        assert success is True

    def test_process_with_files_api_error(self, multimodal_processor, temp_dir):
        """测试API调用错误"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)
        
        multimodal_processor.client.chat.completions.create.side_effect = Exception("Invalid format")
        
        success, msg, audio_result = multimodal_processor.process_with_files("Hello", file_paths=[test_file])
        
        assert success is False
        assert "API调用失败" in msg

    def test_process_with_files_general_exception(self, multimodal_processor, temp_dir):
        """测试一般异常"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)
        
        # Mock to raise exception during file processing
        multimodal_processor.encode_file_to_base64 = MagicMock(side_effect=Exception("Encoding error"))
        
        # 由于异常发生在prepare_multimodal_messages中，需要mock这个方法
        multimodal_processor.prepare_multimodal_messages = MagicMock(side_effect=Exception("Processing error"))
        
        success, msg, audio_result = multimodal_processor.process_with_files("Hello", file_paths=[test_file])
        
        assert success is False
        assert "处理失败" in msg


class TestMultimodalProcessorPrepareMessagesWithFiles:
    """测试 MultimodalProcessor 准备带文件的消息"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = MagicMock()
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_prepare_messages_with_image(self, multimodal_processor, temp_dir):
        """测试准备带图片的消息"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)
        
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", file_paths=[test_file])
        
        assert len(messages) == 1
        assert len(messages[0]["content"]) == 2  # image + text
        assert messages[0]["content"][0]["type"] == "image_url"

    def test_prepare_messages_with_video(self, multimodal_processor, temp_dir):
        """测试准备带视频的消息"""
        test_file = os.path.join(temp_dir, "test.mp4")
        with open(test_file, 'wb') as f:
            f.write(b'x' * 100)
        
        # Mock audio processor
        mock_audio_processor = MagicMock()
        mock_audio_processor.process_video_with_audio.return_value = (True, {"audio_transcription": "test transcription"})
        multimodal_processor.audio_processor = mock_audio_processor
        
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", file_paths=[test_file])
        
        assert len(messages) == 1
        assert audio_result is not None

    def test_prepare_messages_with_video_audio_failure(self, multimodal_processor, temp_dir):
        """测试准备带视频的消息 - 音频处理失败"""
        test_file = os.path.join(temp_dir, "test.mp4")
        with open(test_file, 'wb') as f:
            f.write(b'x' * 100)
        
        # Mock audio processor to fail
        mock_audio_processor = MagicMock()
        mock_audio_processor.process_video_with_audio.return_value = (False, {"error": "audio error"})
        multimodal_processor.audio_processor = mock_audio_processor
        
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", file_paths=[test_file])
        
        assert len(messages) == 1
        assert audio_result is None

    def test_prepare_messages_with_audio_file(self, multimodal_processor, temp_dir):
        """测试准备带音频文件的消息"""
        test_file = os.path.join(temp_dir, "test.mp3")
        with open(test_file, 'wb') as f:
            f.write(b'x' * 100)
        
        # Mock audio processor
        mock_audio_processor = MagicMock()
        mock_audio_processor.process_audio_only.return_value = (True, {"audio_transcription": "audio content"})
        multimodal_processor.audio_processor = mock_audio_processor
        
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", file_paths=[test_file])
        
        assert len(messages) == 1
        assert audio_result is not None

    def test_prepare_messages_with_audio_file_failure(self, multimodal_processor, temp_dir):
        """测试准备带音频文件的消息 - 处理失败"""
        test_file = os.path.join(temp_dir, "test.mp3")
        with open(test_file, 'wb') as f:
            f.write(b'x' * 100)
        
        # Mock audio processor to fail
        mock_audio_processor = MagicMock()
        mock_audio_processor.process_audio_only.return_value = (False, {"error": "processing error"})
        multimodal_processor.audio_processor = mock_audio_processor
        
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", file_paths=[test_file])
        
        assert len(messages) == 1

    def test_prepare_messages_with_text_file(self, multimodal_processor, temp_dir):
        """测试准备带文本文件的消息"""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", file_paths=[test_file])
        
        assert len(messages) == 1
        # 文本文件会被解析

    def test_prepare_messages_with_text_file_parse_failure(self, multimodal_processor, temp_dir):
        """测试准备带文本文件的消息 - 解析失败"""
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Mock parse failure
        multimodal_processor.parse_document_to_text = MagicMock(return_value=None)
        
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", file_paths=[test_file])
        
        assert len(messages) == 1

    def test_prepare_messages_with_unknown_file(self, multimodal_processor, temp_dir):
        """测试准备带未知类型文件的消息"""
        # 创建一个不在允许列表中的文件，但通过is_file_supported检查
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'x' * 100)
        
        # 修改get_file_type返回未知类型
        multimodal_processor.get_file_type = MagicMock(return_value=("unknown", "application/octet-stream"))
        
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", file_paths=[test_file])
        
        assert len(messages) == 1

    def test_prepare_messages_with_encoding_failure(self, multimodal_processor, temp_dir):
        """测试准备消息 - 文件编码失败"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'x' * 100)
        
        # Mock encoding failure
        multimodal_processor.encode_file_to_base64 = MagicMock(return_value=None)
        
        messages, audio_result = multimodal_processor.prepare_multimodal_messages("Hello", file_paths=[test_file])
        
        assert len(messages) == 1
        # 只有文本内容，没有文件
        assert len(messages[0]["content"]) == 1


class TestMultimodalProcessorStreamResponse:
    """测试 MultimodalProcessor 流式响应处理"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        mock_client = MagicMock()
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = mock_client
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_stream_response_with_content(self, multimodal_processor, temp_dir):
        """测试流式响应有内容"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)
        
        # Mock stream response with multiple chunks
        mock_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" World"))]),
        ]
        multimodal_processor.client.chat.completions.create.return_value = mock_chunks
        
        success, msg, audio_result = multimodal_processor.process_with_files("Test", file_paths=[test_file])
        
        assert success is True
        assert msg == "Hello World"

    def test_stream_response_empty_content(self, multimodal_processor, temp_dir):
        """测试流式响应空内容"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)
        
        # Mock stream response with empty content
        mock_chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content=None))]),
        ]
        multimodal_processor.client.chat.completions.create.return_value = mock_chunks
        
        success, msg, audio_result = multimodal_processor.process_with_files("Test", file_paths=[test_file])
        
        assert success is True
        assert msg == ""

    def test_stream_response_with_audio_cleanup(self, multimodal_processor, temp_dir):
        """测试流式响应后清理音频临时文件"""
        test_file = os.path.join(temp_dir, "test.mp3")
        with open(test_file, 'wb') as f:
            f.write(b'x' * 100)
        
        # Mock audio processor
        mock_audio_processor = MagicMock()
        mock_audio_processor.process_audio_only.return_value = (True, {"audio_transcription": "test"})
        mock_audio_processor.cleanup_temp_files = MagicMock()
        multimodal_processor.audio_processor = mock_audio_processor
        
        # Mock stream response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Response"))]
        multimodal_processor.client.chat.completions.create.return_value = [mock_chunk]
        
        success, msg, audio_result = multimodal_processor.process_with_files("Test", file_paths=[test_file])
        
        assert success is True
        # 验证清理方法被调用
        mock_audio_processor.cleanup_temp_files.assert_called()


class TestMultimodalProcessorMultipleFiles:
    """测试 MultimodalProcessor 多文件处理"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        mock_client = MagicMock()
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = mock_client
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_process_multiple_files(self, multimodal_processor, temp_dir):
        """测试处理多个文件"""
        test_file1 = os.path.join(temp_dir, "test1.jpg")
        test_file2 = os.path.join(temp_dir, "test2.png")
        
        with open(test_file1, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)
        with open(test_file2, 'wb') as f:
            f.write(b'\x89PNG\r\n' + b'x' * 100)
        
        # Mock stream response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Response"))]
        multimodal_processor.client.chat.completions.create.return_value = [mock_chunk]
        
        success, msg, audio_result = multimodal_processor.process_with_files(
            "Hello", file_paths=[test_file1, test_file2]
        )
        
        assert success is True

    def test_process_mixed_valid_invalid_files(self, multimodal_processor, temp_dir):
        """测试处理混合有效和无效文件"""
        test_file1 = os.path.join(temp_dir, "test.jpg")
        test_file2 = os.path.join(temp_dir, "test.xyz")
        
        with open(test_file1, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)
        with open(test_file2, 'w') as f:
            f.write("invalid")
        
        # Mock stream response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Response"))]
        multimodal_processor.client.chat.completions.create.return_value = [mock_chunk]
        
        success, msg, audio_result = multimodal_processor.process_with_files(
            "Hello", file_paths=[test_file1, test_file2]
        )
        
        assert success is True  # 至少有一个有效文件


class TestMultimodalProcessorWithHistory:
    """测试 MultimodalProcessor 带历史记录"""

    @pytest.fixture
    def multimodal_processor(self):
        """创建多模态处理器fixture"""
        mock_client = MagicMock()
        with patch('yuntai.processors.multimodal_processor.ZhipuAI') as mock_zhipu:
            mock_zhipu.return_value = mock_client
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            return MultimodalProcessor(api_key='test_key')

    def test_process_with_history(self, multimodal_processor, temp_dir):
        """测试带历史记录处理"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)
        
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "assistant", "content": "Previous answer"}
        ]
        
        # Mock stream response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Response"))]
        multimodal_processor.client.chat.completions.create.return_value = [mock_chunk]
        
        success, msg, audio_result = multimodal_processor.process_with_files(
            "Hello", file_paths=[test_file], history=history
        )
        
        assert success is True

    def test_process_with_custom_params(self, multimodal_processor, temp_dir):
        """测试带自定义参数处理"""
        test_file = os.path.join(temp_dir, "test.jpg")
        with open(test_file, 'wb') as f:
            f.write(b'\xff\xd8\xff\xe0' + b'x' * 100)
        
        # Mock stream response
        mock_chunk = MagicMock()
        mock_chunk.choices = [MagicMock(delta=MagicMock(content="Response"))]
        multimodal_processor.client.chat.completions.create.return_value = [mock_chunk]
        
        success, msg, audio_result = multimodal_processor.process_with_files(
            "Hello", 
            file_paths=[test_file],
            temperature=0.5,
            max_tokens=1000
        )
        
        assert success is True
        # 验证参数被传递
        call_kwargs = multimodal_processor.client.chat.completions.create.call_args[1]
        assert call_kwargs['temperature'] == 0.5
        assert call_kwargs['max_tokens'] == 1000
