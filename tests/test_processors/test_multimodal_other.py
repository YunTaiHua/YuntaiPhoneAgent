"""
测试 multimodal_other.py - 多模态其他功能
"""
import pytest
import os
from unittest.mock import MagicMock, patch, mock_open
import tempfile

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')


class TestMultimodalOtherInit:
    """测试 MultimodalOther 初始化"""

    def test_init_with_defaults(self):
        """测试使用默认值初始化"""
        with patch('yuntai.processors.multimodal_other.ZHIPU_API_KEY', 'test_key'), \
             patch('yuntai.processors.multimodal_other.PROJECT_ROOT', '/fake/project'), \
             patch('yuntai.processors.multimodal_other.TEMP_DIR', '/fake/temp'), \
             patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            
            processor = MultimodalOther()
            
            assert processor.api_key == 'test_key'
            assert processor.project_root == '/fake/project'

    def test_init_with_custom_values(self):
        """测试使用自定义值初始化"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            
            processor = MultimodalOther(api_key='custom_key', project_root='/custom/project')
            
            assert processor.api_key == 'custom_key'
            assert processor.project_root == '/custom/project'

    def test_image_sizes_defined(self):
        """测试图像尺寸定义"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            
            processor = MultimodalOther()
            
            assert len(processor.image_sizes) > 0
            assert "1280x1280" in processor.image_sizes

    def test_video_sizes_defined(self):
        """测试视频尺寸定义"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            
            processor = MultimodalOther()
            
            assert len(processor.video_sizes) > 0
            assert "1920x1080" in processor.video_sizes

    def test_video_fps_defined(self):
        """测试视频帧率定义"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            
            processor = MultimodalOther()
            
            assert 30 in processor.video_fps
            assert 60 in processor.video_fps


class TestMultimodalOtherGenerateImage:
    """测试 MultimodalOther 图像生成"""

    @pytest.fixture
    def processor(self):
        """创建处理器fixture"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            return MultimodalOther(api_key='test_key')

    def test_generate_image_success(self, processor):
        """测试图像生成成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"url": "http://example.com/image.png"}]}
        
        with patch('requests.post', return_value=mock_response):
            result = processor.generate_image("测试图像")
            
            assert result["success"] is True
            assert "data" in result

    def test_generate_image_api_failure(self, processor):
        """测试图像生成API失败"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        with patch('requests.post', return_value=mock_response):
            result = processor.generate_image("测试图像")
            
            assert result["success"] is False
            assert "失败" in result["message"]

    def test_generate_image_exception(self, processor):
        """测试图像生成异常"""
        with patch('requests.post', side_effect=Exception("network error")):
            result = processor.generate_image("测试图像")
            
            assert result["success"] is False

    def test_generate_image_with_size(self, processor):
        """测试图像生成带尺寸"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"url": "http://example.com/image.png"}]}
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = processor.generate_image("测试图像", size="1024x1024")
            
            assert result["success"] is True
            # 验证调用参数
            call_args = mock_post.call_args
            assert call_args[1]['json']['size'] == "1024x1024"

    def test_generate_image_with_quality(self, processor):
        """测试图像生成带质量"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"url": "http://example.com/image.png"}]}
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = processor.generate_image("测试图像", quality="hd")
            
            assert result["success"] is True
            call_args = mock_post.call_args
            assert call_args[1]['json']['quality'] == "hd"


class TestMultimodalOtherDownloadImage:
    """测试 MultimodalOther 图像下载"""

    @pytest.fixture
    def processor(self, tmp_path):
        """创建处理器fixture"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            proc = MultimodalOther(api_key='test_key')
            proc.image_output_dir = str(tmp_path)
            return proc

    def test_download_image_success(self, processor):
        """测试图像下载成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake image data"
        
        with patch('requests.get', return_value=mock_response):
            result = processor.download_image("http://example.com/image.png", "test_image")
            
            assert result.endswith(".png")

    def test_download_image_without_filename(self, processor):
        """测试图像下载无文件名"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake image data"
        
        with patch('requests.get', return_value=mock_response), \
             patch('time.time', return_value=1234567890):
            result = processor.download_image("http://example.com/image.png")
            
            assert result.endswith(".png")

    def test_download_image_failure(self, processor):
        """测试图像下载失败"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch('requests.get', return_value=mock_response):
            with pytest.raises(Exception):
                processor.download_image("http://example.com/image.png")

    def test_download_image_exception(self, processor):
        """测试图像下载异常"""
        with patch('requests.get', side_effect=Exception("network error")):
            with pytest.raises(Exception):
                processor.download_image("http://example.com/image.png")


class TestMultimodalOtherGenerateVideo:
    """测试 MultimodalOther 视频生成"""

    @pytest.fixture
    def processor(self):
        """创建处理器fixture"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            return MultimodalOther(api_key='test_key')

    def test_generate_video_success(self, processor):
        """测试视频生成成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "task123",
            "task_status": "PROCESSING"
        }
        
        with patch('requests.post', return_value=mock_response):
            result = processor.generate_video("测试视频")
            
            assert result["success"] is True
            assert result["task_id"] == "task123"

    def test_generate_video_with_single_image(self, processor):
        """测试视频生成带单张图片"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "task123",
            "task_status": "PROCESSING"
        }
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = processor.generate_video(
                "测试视频",
                image_urls=["http://example.com/image1.png"]
            )
            
            assert result["success"] is True
            call_args = mock_post.call_args
            assert "image_url" in call_args[1]['json']

    def test_generate_video_with_two_images(self, processor):
        """测试视频生成带两张图片"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "task123",
            "task_status": "PROCESSING"
        }
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = processor.generate_video(
                "测试视频",
                image_urls=["http://example.com/image1.png", "http://example.com/image2.png"]
            )
            
            assert result["success"] is True
            call_args = mock_post.call_args
            assert "image_urls" in call_args[1]['json']

    def test_generate_video_too_many_images(self, processor):
        """测试视频生成图片过多"""
        result = processor.generate_video(
            "测试视频",
            image_urls=["http://example.com/1.png", "http://example.com/2.png", "http://example.com/3.png"]
        )
        
        assert result["success"] is False
        assert "最多支持2张图片" in result["message"]

    def test_generate_video_invalid_url(self, processor):
        """测试视频生成无效URL"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "task123",
            "task_status": "PROCESSING"
        }
        
        with patch('requests.post', return_value=mock_response):
            result = processor.generate_video(
                "测试视频",
                image_urls=["invalid_url"]
            )
            
            # 无效URL应该被过滤
            assert result["success"] is True

    def test_generate_video_api_failure(self, processor):
        """测试视频生成API失败"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = '{"error": {"message": "Bad Request"}}'
        
        with patch('requests.post', return_value=mock_response):
            result = processor.generate_video("测试视频")
            
            assert result["success"] is False

    def test_generate_video_task_failed(self, processor):
        """测试视频生成任务失败"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "task123",
            "task_status": "FAIL",
            "error": {"message": "生成失败", "code": "ERROR"}
        }
        
        with patch('requests.post', return_value=mock_response):
            result = processor.generate_video("测试视频")
            
            assert result["success"] is False
            assert "FAIL" in result["task_status"]

    def test_generate_video_no_task_id(self, processor):
        """测试视频生成无任务ID"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        
        with patch('requests.post', return_value=mock_response):
            result = processor.generate_video("测试视频")
            
            assert result["success"] is False
            assert "任务ID" in result["message"]

    def test_generate_video_exception(self, processor):
        """测试视频生成异常"""
        with patch('requests.post', side_effect=Exception("network error")):
            result = processor.generate_video("测试视频")
            
            assert result["success"] is False

    def test_generate_video_with_params(self, processor):
        """测试视频生成带参数"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "task123",
            "task_status": "PROCESSING"
        }
        
        with patch('requests.post', return_value=mock_response) as mock_post:
            result = processor.generate_video(
                "测试视频",
                size="1080x1920",
                fps=60,
                quality="speed",
                with_audio=False
            )
            
            assert result["success"] is True
            call_args = mock_post.call_args
            assert call_args[1]['json']['size'] == "1080x1920"
            assert call_args[1]['json']['fps'] == 60


class TestMultimodalOtherCheckVideoResult:
    """测试 MultimodalOther 检查视频结果"""

    @pytest.fixture
    def processor(self):
        """创建处理器fixture"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            return MultimodalOther(api_key='test_key')

    def test_check_video_result_success(self, processor):
        """测试检查视频结果 - 成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_status": "SUCCESS",
            "video_result": [{
                "cover_image_url": "http://example.com/cover.png",
                "url": "http://example.com/video.mp4"
            }]
        }
        
        with patch('requests.get', return_value=mock_response):
            result = processor.check_video_result("task123")
            
            assert result["success"] is True
            assert result["status"] == "SUCCESS"
            assert result["video_url"] == "http://example.com/video.mp4"

    def test_check_video_result_processing(self, processor):
        """测试检查视频结果 - 处理中"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_status": "PROCESSING"
        }
        
        with patch('requests.get', return_value=mock_response):
            result = processor.check_video_result("task123")
            
            assert result["success"] is False
            assert result["status"] == "PROCESSING"

    def test_check_video_result_fail(self, processor):
        """测试检查视频结果 - 失败"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_status": "FAIL",
            "error": {"message": "生成失败"}
        }
        
        with patch('requests.get', return_value=mock_response):
            result = processor.check_video_result("task123")
            
            assert result["success"] is False
            assert result["status"] == "FAIL"

    def test_check_video_result_unknown_status(self, processor):
        """测试检查视频结果 - 未知状态"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_status": "UNKNOWN"
        }
        
        with patch('requests.get', return_value=mock_response):
            result = processor.check_video_result("task123")
            
            assert result["success"] is False
            assert "未知状态" in result["message"]

    def test_check_video_result_empty_video_result(self, processor):
        """测试检查视频结果 - 空视频结果"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_status": "SUCCESS",
            "video_result": []
        }
        
        with patch('requests.get', return_value=mock_response):
            result = processor.check_video_result("task123")
            
            assert result["success"] is False
            assert "格式错误" in result["message"]

    def test_check_video_result_api_error(self, processor):
        """测试检查视频结果 - API错误"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        
        with patch('requests.get', return_value=mock_response):
            result = processor.check_video_result("task123")
            
            assert result["success"] is False

    def test_check_video_result_exception(self, processor):
        """测试检查视频结果 - 异常"""
        with patch('requests.get', side_effect=Exception("network error")):
            result = processor.check_video_result("task123")
            
            assert result["success"] is False


class TestMultimodalOtherDownloadVideo:
    """测试 MultimodalOther 视频下载"""

    @pytest.fixture
    def processor(self, tmp_path):
        """创建处理器fixture"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            proc = MultimodalOther(api_key='test_key')
            proc.video_output_dir = str(tmp_path)
            return proc

    def test_download_video_success(self, processor):
        """测试视频下载成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content = lambda chunk_size: [b"fake video data"]
        
        with patch('requests.get', return_value=mock_response):
            result = processor.download_video("http://example.com/video.mp4")
            
            assert result["success"] is True
            assert "video_path" in result

    def test_download_video_with_cover(self, processor):
        """测试视频下载带封面"""
        mock_video_response = MagicMock()
        mock_video_response.status_code = 200
        mock_video_response.headers = {'content-length': '1024'}
        mock_video_response.iter_content = lambda chunk_size: [b"fake video data"]
        
        mock_cover_response = MagicMock()
        mock_cover_response.status_code = 200
        mock_cover_response.content = b"fake cover data"
        
        def mock_get(url, **kwargs):
            if "cover" in url:
                return mock_cover_response
            return mock_video_response
        
        with patch('requests.get', side_effect=mock_get):
            result = processor.download_video(
                "http://example.com/video.mp4",
                cover_url="http://example.com/cover.png"
            )
            
            assert result["success"] is True
            assert result["cover_path"] is not None

    def test_download_video_failure(self, processor):
        """测试视频下载失败"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        with patch('requests.get', return_value=mock_response):
            result = processor.download_video("http://example.com/video.mp4")
            
            assert result["success"] is False

    def test_download_video_exception(self, processor):
        """测试视频下载异常"""
        with patch('requests.get', side_effect=Exception("network error")):
            result = processor.download_video("http://example.com/video.mp4")
            
            assert result["success"] is False

    def test_download_video_with_filename(self, processor):
        """测试视频下载带文件名"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content = lambda chunk_size: [b"fake video data"]
        
        with patch('requests.get', return_value=mock_response):
            result = processor.download_video(
                "http://example.com/video.mp4",
                filename="custom_video"
            )
            
            assert result["success"] is True
            assert "custom_video" in result["video_path"]


class TestMultimodalOtherWaitForVideo:
    """测试 MultimodalOther 等待视频完成"""

    @pytest.fixture
    def processor(self):
        """创建处理器fixture"""
        with patch('os.makedirs'):
            from yuntai.processors.multimodal_other import MultimodalOther
            return MultimodalOther(api_key='test_key')

    def test_wait_for_video_completion_success(self, processor):
        """测试等待视频完成 - 成功"""
        success_result = {
            "success": True,
            "status": "SUCCESS",
            "video_url": "http://example.com/video.mp4"
        }
        
        with patch.object(processor, 'check_video_result', return_value=success_result), \
             patch('time.sleep'):
            result = processor.wait_for_video_completion("task123", max_attempts=1)
            
            assert result["success"] is True

    def test_wait_for_video_completion_fail(self, processor):
        """测试等待视频完成 - 失败"""
        fail_result = {
            "success": False,
            "status": "FAIL",
            "message": "生成失败"
        }
        
        with patch.object(processor, 'check_video_result', return_value=fail_result), \
             patch('time.sleep'):
            result = processor.wait_for_video_completion("task123", max_attempts=1)
            
            assert result["status"] == "FAIL"

    def test_wait_for_video_completion_with_callback(self, processor):
        """测试等待视频完成 - 带回调"""
        success_result = {
            "success": True,
            "status": "SUCCESS",
            "video_url": "http://example.com/video.mp4"
        }
        
        callback_calls = []
        
        def callback(event_type, attempt, task_id, status, interval):
            callback_calls.append((event_type, attempt, task_id, status))
        
        with patch.object(processor, 'check_video_result', return_value=success_result), \
             patch('time.sleep'):
            result = processor.wait_for_video_completion(
                "task123", max_attempts=1, callback=callback
            )
            
            assert result["success"] is True
            assert len(callback_calls) > 0

    def test_wait_for_video_completion_timeout(self, processor):
        """测试等待视频完成 - 超时"""
        processing_result = {
            "success": False,
            "status": "PROCESSING",
            "message": "处理中"
        }
        
        with patch.object(processor, 'check_video_result', return_value=processing_result), \
             patch('time.sleep'):
            result = processor.wait_for_video_completion("task123", max_attempts=2)
            
            assert result["success"] is False
            assert "超时" in result["message"]


class TestMultimodalOtherConstants:
    """测试 MultimodalOther 常量"""

    def test_chunk_size(self):
        """测试块大小"""
        from yuntai.processors.multimodal_other import CHUNK_SIZE
        assert CHUNK_SIZE == 8192

    def test_timeout(self):
        """测试超时"""
        from yuntai.processors.multimodal_other import TIMEOUT
        assert TIMEOUT == 30

    def test_max_image_count(self):
        """测试最大图像数量"""
        from yuntai.processors.multimodal_other import MAX_IMAGE_COUNT
        assert MAX_IMAGE_COUNT == 2

    def test_max_attempts(self):
        """测试最大尝试次数"""
        from yuntai.processors.multimodal_other import MAX_ATTEMPTS
        assert MAX_ATTEMPTS == 100
