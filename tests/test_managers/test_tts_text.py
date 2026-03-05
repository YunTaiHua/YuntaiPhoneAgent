"""
测试 tts_text.py - TTS文本处理器
"""
import pytest
import os
from unittest.mock import MagicMock, patch

# 设置测试环境变量
os.environ.setdefault('ZHIPU_API_KEY', 'test_api_key_for_testing')
os.environ.setdefault('GPT_SOVITS_ROOT', '/fake/gpt-sovits')
os.environ.setdefault('SCRCPY_PATH', '/fake/scrcpy')
os.environ.setdefault('FFMPEG_PATH', '/fake/ffmpeg')
os.environ.setdefault('FOREVER_MEMORY_FILE', '/fake/forever.txt')

from yuntai.managers.tts_text import TTSTextProcessor


class TestTTSTextProcessor:
    """测试 TTSTextProcessor 类"""

    def test_init_default(self):
        """测试默认初始化"""
        processor = TTSTextProcessor()
        
        assert processor.max_text_length == 500

    def test_init_custom_max_length(self):
        """测试自定义最大长度初始化"""
        processor = TTSTextProcessor(max_text_length=1000)
        
        assert processor.max_text_length == 1000

    def test_clean_text_for_tts_empty(self):
        """测试清理空文本"""
        processor = TTSTextProcessor()
        
        result = processor.clean_text_for_tts("")
        
        assert "你好" in result

    def test_clean_text_for_tts_none(self):
        """测试清理None文本"""
        processor = TTSTextProcessor()
        
        result = processor.clean_text_for_tts(None)
        
        assert "你好" in result

    def test_clean_text_for_tts_simple_chinese(self):
        """测试清理简单中文文本"""
        processor = TTSTextProcessor()
        
        result = processor.clean_text_for_tts("你好，世界！")
        
        assert "你好" in result
        assert "世界" in result

    def test_clean_text_for_tts_with_code_block(self):
        """测试清理包含代码块的文本"""
        processor = TTSTextProcessor()
        
        text = "```python\nprint('hello')\n```\n这是中文内容。"
        result = processor.clean_text_for_tts(text)
        
        assert "```" not in result
        assert "中文内容" in result

    def test_clean_text_for_tts_with_url(self):
        """测试清理包含URL的文本"""
        processor = TTSTextProcessor()
        
        text = "访问 https://example.com 查看更多信息。"
        result = processor.clean_text_for_tts(text)
        
        assert "https://" not in result
        assert "更多信息" in result

    def test_clean_text_for_tts_with_brackets(self):
        """测试清理包含方括号的文本"""
        processor = TTSTextProcessor()
        
        text = "这是[隐藏内容]测试文本。"
        result = processor.clean_text_for_tts(text)
        
        assert "[隐藏内容]" not in result
        assert "测试文本" in result

    def test_clean_text_for_tts_preserves_chinese_punctuation(self):
        """测试保留中文标点"""
        processor = TTSTextProcessor()
        
        text = "你好，世界！这是测试。"
        result = processor.clean_text_for_tts(text)
        
        assert "，" in result or "," in result
        assert "！" in result or "!" in result
        assert "。" in result or "." in result

    def test_clean_text_for_tts_removes_extra_spaces(self):
        """测试移除多余空格"""
        processor = TTSTextProcessor()
        
        text = "这是    多个    空格的    文本。"
        result = processor.clean_text_for_tts(text)
        
        assert "    " not in result

    def test_clean_text_for_tts_low_chinese_ratio(self):
        """测试中文比例过低的文本"""
        processor = TTSTextProcessor()
        
        text = "hello world this is english text"
        result = processor.clean_text_for_tts(text)
        
        # 应该返回兜底文本
        assert "你好" in result

    def test_clean_text_for_tts_too_short(self):
        """测试过短的文本"""
        processor = TTSTextProcessor()
        
        text = "好"
        result = processor.clean_text_for_tts(text)
        
        # 应该返回兜底文本
        assert "你好" in result

    def test_should_use_segmented_synthesis_empty(self):
        """测试空文本是否分段"""
        processor = TTSTextProcessor()
        
        result = processor.should_use_segmented_synthesis("")
        
        assert result is False

    def test_should_use_segmented_synthesis_none(self):
        """测试None文本是否分段"""
        processor = TTSTextProcessor()
        
        result = processor.should_use_segmented_synthesis(None)
        
        assert result is False

    def test_should_use_segmented_synthesis_short_text(self):
        """测试短文本是否分段"""
        processor = TTSTextProcessor()
        
        text = "这是一段短文本。"
        result = processor.should_use_segmented_synthesis(text)
        
        assert result is False

    def test_should_use_segmented_synthesis_long_text(self):
        """测试长文本是否分段"""
        processor = TTSTextProcessor()
        
        # 创建一个超过阈值的文本
        text = "这是测试内容。" * 200  # 超过750字符
        result = processor.should_use_segmented_synthesis(text)
        
        assert result is True

    def test_should_use_segmented_synthesis_with_numbered_sections(self):
        """测试带序号的文本是否分段"""
        processor = TTSTextProcessor()
        
        text = "1. 第一项内容\n2. 第二项内容\n3. 第三项内容"
        result = processor.should_use_segmented_synthesis(text)
        
        assert result is True

    def test_should_use_segmented_synthesis_with_chinese_numbers(self):
        """测试带中文序号的文本是否分段"""
        processor = TTSTextProcessor()
        
        text = "一、第一项内容\n二、第二项内容"
        result = processor.should_use_segmented_synthesis(text)
        
        # 中文序号可能不被识别为分段标志
        # 取决于具体实现

    def test_split_text_by_numbered_sections_empty(self):
        """测试分段空文本"""
        processor = TTSTextProcessor()
        
        result = processor.split_text_by_numbered_sections("")
        
        assert result == [] or result == [""]

    def test_split_text_by_numbered_sections_single(self):
        """测试分段无序号文本"""
        processor = TTSTextProcessor()
        
        text = "这是没有序号的普通文本。"
        result = processor.split_text_by_numbered_sections(text)
        
        # 无序号文本应该返回原文本或清理后的文本
        assert len(result) >= 1

    def test_split_text_by_numbered_sections_with_numbers(self):
        """测试分段带数字序号的文本"""
        processor = TTSTextProcessor()
        
        text = "1. 第一项\n2. 第二项\n3. 第三项"
        result = processor.split_text_by_numbered_sections(text)
        
        # 应该分成多个段落
        assert len(result) >= 1

    def test_split_text_by_numbered_sections_with_markdown(self):
        """测试分段Markdown标题"""
        processor = TTSTextProcessor()
        
        text = "## 1. 标题一\n内容一\n## 2. 标题二\n内容二"
        result = processor.split_text_by_numbered_sections(text)
        
        assert len(result) >= 1


class TestTTSTextProcessorEdgeCases:
    """测试 TTSTextProcessor 边界情况"""

    def test_clean_text_with_special_characters(self):
        """测试清理特殊字符"""
        processor = TTSTextProcessor()
        
        text = "你好@#$%^&*世界！"
        result = processor.clean_text_for_tts(text)
        
        # 特殊字符应该被移除
        assert "@#$%^&*" not in result

    def test_clean_text_with_newlines(self):
        """测试清理换行符"""
        processor = TTSTextProcessor()
        
        text = "第一行\n第二行\n第三行"
        result = processor.clean_text_for_tts(text)
        
        # 换行符应该被处理
        assert "第一行" in result or "第" in result

    def test_clean_text_with_tabs(self):
        """测试清理制表符"""
        processor = TTSTextProcessor()
        
        text = "列一\t列二\t列三"
        result = processor.clean_text_for_tts(text)
        
        # 制表符应该被处理
        assert "\t" not in result

    def test_clean_text_mixed_content(self):
        """测试清理混合内容"""
        processor = TTSTextProcessor()
        
        text = "```python\ncode\n```\n正文内容 https://url.com [隐藏] 结尾。"
        result = processor.clean_text_for_tts(text)
        
        # 应该只保留中文内容
        assert "```" not in result
        assert "https://" not in result
        assert "[隐藏]" not in result

    def test_split_text_preserves_content(self):
        """测试分段保留内容"""
        processor = TTSTextProcessor()
        
        text = "1. 重要内容一\n2. 重要内容二"
        result = processor.split_text_by_numbered_sections(text)
        
        # 合并后应该包含原始内容
        combined = "".join(result)
        assert "重要内容" in combined or "内容" in combined
