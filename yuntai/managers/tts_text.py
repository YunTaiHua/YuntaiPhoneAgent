"""
TTS文本处理器 - 负责TTS文本清洗、分段逻辑
"""

import re


class TTSTextProcessor:
    """TTS文本处理器"""

    def __init__(self, max_text_length: int = 500):
        """
        初始化文本处理器

        Args:
            max_text_length: 单个文本片段最大长度
        """
        self.max_text_length = max_text_length

    def clean_text_for_tts(self, text: str) -> str:
        """清理文本，但不丢失开头部分"""
        if not text:
            return "你好，我是小芸，很高兴为您服务"

        # 保存原始文本以便后续处理
        original_text = text

        # 1. 移除代码块标记
        text = re.sub(r'```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'```', '', text)

        # 2. 移除URL和特殊标记，但保留中文标点
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\[.*?\]', '', text)  # 移除方括号内容

        # 3. 保留中文标点：，。！？；："'
        text = re.sub(r'[^\w\u4e00-\u9fff\s\.,，。!！?？:：;；、\'\"\(\)（）《》【】\-]', '', text)

        # 4. 移除多余空格，但保留一个空格
        text = ' '.join(text.split())

        # 5. 检查清理后的文本长度
        cleaned_text = text.strip()

        # 检查是否主要是英文或特殊字符
        chinese_char_count = len([c for c in cleaned_text if '\u4e00' <= c <= '\u9fff'])
        total_char_count = len(cleaned_text)

        # 如果中文字符占比太低或文本太短，使用兜底文本
        if total_char_count == 0 or (total_char_count > 0 and chinese_char_count / total_char_count < 0.1) or len(cleaned_text) < 2:
            print(f"⚠️  清理后的文本质量不佳（中文字符占比: {chinese_char_count}/{total_char_count}），使用兜底文本")
            # 使用更长的兜底文本，确保GPT-SoVITS能正常处理
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

        # 文本长度超过阈值
        if len(cleaned_text) > self.max_text_length * 1.5:  # 超过750字符
            return True

        # 包含多个序号段落
        numbered_patterns = [r'\d+\.\s', r'\d+、\s', r'\(\d+\)\s']
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
        segments = []

        # 多种序号模式（优先级从高到低）
        patterns = [
            (r'### (\d+\.)', 3),  # Markdown三级标题
            (r'## (\d+\.)', 2),  # Markdown二级标题
            (r'(\d+\.\s)', 1),  # 数字加点（英文）
            (r'(\d+、\s)', 1),  # 数字加顿号（中文）
            (r'\((\d+)\)\s', 1),  # 括号数字
            (r'一、', 1),  # 中文序号
            (r'二、', 1),
            (r'三、', 1),
            (r'四、', 1),
            (r'五、', 1),
            (r'首先', 1),  # 连接词
            (r'其次', 1),
            (r'再次', 1),
            (r'最后', 1),
        ]

        best_pattern = None
        best_matches = []

        # 寻找最佳分段模式
        for pattern, priority in patterns:
            matches = list(re.finditer(pattern, text))
            if len(matches) >= 2:  # 至少有2个匹配
                if not best_matches or (
                len(matches) > len(best_matches) and priority >= patterns[patterns.index((best_pattern, 0))][
                    1] if best_pattern else 0):
                    best_pattern = pattern
                    best_matches = matches

        # 使用最佳模式分段
        if best_pattern and best_matches:
            # 从第一个分段点开始
            start_pos = 0
            last_end_pos = 0

            for i, match in enumerate(best_matches):
                if i == 0:
                    # 第一段：从开头到第一个分段点
                    segment = text[start_pos:match.start()].strip()
                    if segment and len(segment) > 10:  # 确保不是空段
                        segments.append(segment)
                    start_pos = match.start()
                    last_end_pos = match.start()
                    continue

                # 中间段：从前一个分段点到当前分段点
                segment = text[last_end_pos:match.start()].strip()
                if segment and len(segment) > 10:
                    segments.append(segment)
                last_end_pos = match.start()

            # 最后一段：从最后一个分段点到结尾
            last_segment = text[last_end_pos:].strip()
            if last_segment and len(last_segment) > 10:
                segments.append(last_segment)

            # 检查分段质量
            if segments and len(segments) >= 2:
                avg_length = sum(len(s) for s in segments) / len(segments)
                if 50 <= avg_length <= self.max_text_length * 2:
                    return segments
                else:
                    segments = []

        # 如果没有找到合适的序号分段，尝试按段落分段
        if not segments:
            # 按空行分段
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if len(paragraphs) >= 2:
                # 合并过短的段落
                merged = []
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

        # 最后尝试按标点分段
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
        segments = []
        current_segment = ""

        # 标点符号列表
        punctuation_marks = ['。', '！', '？', '；', '.', '!', '?', ';']

        for char in text:
            current_segment += char

            # 如果遇到标点，并且当前段达到一定长度
            if char in punctuation_marks and len(current_segment) >= 50:
                segments.append(current_segment.strip())
                current_segment = ""

            # 如果当前段超过最大长度，强制分段
            elif len(current_segment) >= self.max_text_length:
                # 在最后出现的标点处分段
                last_punct = -1
                for punct in punctuation_marks:
                    pos = current_segment.rfind(punct)
                    if pos > last_punct:
                        last_punct = pos

                if last_punct > 0:
                    segments.append(current_segment[:last_punct + 1].strip())
                    current_segment = current_segment[last_punct + 1:]
                else:
                    # 没有标点，按长度硬切
                    segments.append(current_segment.strip())
                    current_segment = ""

        # 添加最后一段
        if current_segment.strip():
            segments.append(current_segment.strip())

        # 合并过短的段落
        merged_segments = []
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

        #print(f"📝 按标点分段，合并后: {len(merged_segments)} 段")
        return merged_segments
