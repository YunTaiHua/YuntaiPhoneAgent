"""
TTS文本处理器 - 负责TTS文本清洗、分段逻辑
"""

from __future__ import annotations

import re
from typing import Any


class TTSTextProcessor:
    """TTS文本处理器"""

    def __init__(self, max_text_length: int = 500) -> None:
        """
        初始化文本处理器

        Args:
            max_text_length: 单个文本片段最大长度
        """
        self.max_text_length: int = max_text_length

    def clean_text_for_tts(self, text: str) -> str:
        """清理文本，但不丢失开头部分"""
        if not text:
            return "你好，我是小芸，很高兴为您服务"

        original_text = text

        text = re.sub(r'```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'```', '', text)

        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\[.*?\]', '', text)

        text = re.sub(r'[^\w\u4e00-\u9fff\s\.,，。!！?？:：;；、\'\"\(\)（）《》【】\-]', '', text)

        text = ' '.join(text.split())

        cleaned_text = text.strip()

        chinese_char_count = len([c for c in cleaned_text if '\u4e00' <= c <= '\u9fff'])
        total_char_count = len(cleaned_text)

        if total_char_count == 0 or (total_char_count > 0 and chinese_char_count / total_char_count < 0.1) or len(cleaned_text) < 2:
            print(f"⚠️  清理后的文本质量不佳（中文字符占比: {chinese_char_count}/{total_char_count}），使用兜底文本")
            return "你好，我是小芸，很高兴为您服务"

        return cleaned_text

    def should_use_segmented_synthesis(self, text: str) -> bool:
        """
        判断是否应该使用分段合成

        Args:
            text: 要判断的文本

        Returns:
            True如果应该使用分段合成
        """
        if not text:
            return False

        cleaned_text = self.clean_text_for_tts(text)

        if len(cleaned_text) > self.max_text_length * 1.5:
            return True

        numbered_patterns: list[str] = [r'\d+\.\s', r'\d+、\s', r'\(\d+\)\s']
        for pattern in numbered_patterns:
            if len(re.findall(pattern, cleaned_text)) >= 2:
                return True

        return False

    def split_text_by_numbered_sections(self, text: str) -> list[str]:
        """
        按序号分段文本（改进版）

        Args:
            text: 要分段的文本

        Returns:
            分段后的文本列表
        """
        segments: list[str] = []

        patterns: list[tuple[str, int]] = [
            (r'### (\d+\.)', 3),
            (r'## (\d+\.)', 2),
            (r'(\d+\.\s)', 1),
            (r'(\d+、\s)', 1),
            (r'\((\d+)\)\s', 1),
            (r'一、', 1),
            (r'二、', 1),
            (r'三、', 1),
            (r'四、', 1),
            (r'五、', 1),
            (r'首先', 1),
            (r'其次', 1),
            (r'再次', 1),
            (r'最后', 1),
        ]

        best_pattern: str | None = None
        best_matches: list[Any] = []

        for pattern, priority in patterns:
            matches = list(re.finditer(pattern, text))
            if len(matches) >= 2:
                if not best_matches or (
                len(matches) > len(best_matches) and priority >= patterns[patterns.index((best_pattern, 0))][
                    1] if best_pattern else 0):
                    best_pattern = pattern
                    best_matches = matches

        if best_pattern and best_matches:
            start_pos = 0
            last_end_pos = 0

            for i, match in enumerate(best_matches):
                if i == 0:
                    segment = text[start_pos:match.start()].strip()
                    if segment and len(segment) > 10:
                        segments.append(segment)
                    start_pos = match.start()
                    last_end_pos = match.start()
                    continue

                segment = text[last_end_pos:match.start()].strip()
                if segment and len(segment) > 10:
                    segments.append(segment)
                last_end_pos = match.start()

            last_segment = text[last_end_pos:].strip()
            if last_segment and len(last_segment) > 10:
                segments.append(last_segment)

            if segments and len(segments) >= 2:
                avg_length = sum(len(s) for s in segments) / len(segments)
                if 50 <= avg_length <= self.max_text_length * 2:
                    return segments
                else:
                    segments = []

        if not segments:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if len(paragraphs) >= 2:
                merged: list[str] = []
                buffer = ""

                for para in paragraphs:
                    if len(buffer) + len(para) < self.max_text_length:
                        if buffer:
                            buffer += "\n\n" + para
                        else:
                            buffer = para
                    else:
                        if buffer:
                            merged.append(buffer)
                        buffer = para

                if buffer:
                    merged.append(buffer)

                if len(merged) >= 2:
                    return merged

        if not segments:
            segments = self.split_text_by_punctuation(text)

        return segments

    def split_text_by_punctuation(self, text: str) -> list[str]:
        """
        按标点符号分段

        Args:
            text: 要分段的文本

        Returns:
            分段后的文本列表
        """
        segments: list[str] = []
        current_segment = ""

        punctuation_marks: list[str] = ['。', '！', '？', '；', '.', '!', '?', ';']

        for char in text:
            current_segment += char

            if char in punctuation_marks and len(current_segment) >= 50:
                segments.append(current_segment.strip())
                current_segment = ""

            elif len(current_segment) >= self.max_text_length:
                last_punct = -1
                for punct in punctuation_marks:
                    pos = current_segment.rfind(punct)
                    if pos > last_punct:
                        last_punct = pos

                if last_punct > 0:
                    segments.append(current_segment[:last_punct + 1].strip())
                    current_segment = current_segment[last_punct + 1:]
                else:
                    segments.append(current_segment.strip())
                    current_segment = ""

        if current_segment.strip():
            segments.append(current_segment.strip())

        merged_segments: list[str] = []
        buffer = ""

        for segment in segments:
            if len(buffer) + len(segment) < self.max_text_length * 0.7:
                buffer += " " + segment if buffer else segment
            else:
                if buffer:
                    merged_segments.append(buffer)
                buffer = segment

        if buffer:
            merged_segments.append(buffer)

        return merged_segments
