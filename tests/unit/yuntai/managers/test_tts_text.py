from yuntai.managers.tts_text import TTSTextProcessor


def test_clean_text_for_tts_returns_fallback_for_empty_or_low_quality_text():
    processor = TTSTextProcessor()

    assert processor.clean_text_for_tts("") == "你好，我是小芸，很高兴为您服务"
    assert processor.clean_text_for_tts("hello world 123") == "你好，我是小芸，很高兴为您服务"


def test_clean_text_for_tts_removes_markdown_and_urls_but_keeps_chinese():
    processor = TTSTextProcessor()
    raw = """```python
print('x')
```
请访问 https://example.com [link]，这是测试文本。"""

    cleaned = processor.clean_text_for_tts(raw)

    assert "```" not in cleaned
    assert "http" not in cleaned
    assert "请访问" in cleaned
    assert "这是测试文本" in cleaned


def test_should_use_segmented_synthesis_for_long_and_numbered_text():
    processor = TTSTextProcessor(max_text_length=40)

    long_text = "这是一段中文文本。" * 20
    assert processor.should_use_segmented_synthesis(long_text) is True

    numbered = "1. 第一部分内容。\n2. 第二部分内容。\n3. 第三部分内容。"
    assert processor.should_use_segmented_synthesis(numbered) is True


def test_split_text_by_numbered_sections_falls_back_to_paragraph_or_punctuation():
    processor = TTSTextProcessor(max_text_length=80)

    paragraphs = (
        "第一段内容足够长，用于触发段落分割，包含较多字符以超过分段阈值。"
        "这里继续补充第一段文本，让其长度明显增加。\n\n"
        "第二段内容也足够长，用于验证逻辑，保持段落级分割可用。"
        "这里继续补充第二段文本，确保两段分别成段。"
    )
    paragraph_segments = processor.split_text_by_numbered_sections(paragraphs)
    assert len(paragraph_segments) >= 2

    punctuation_text = "这是第一句。" * 20 + "这是第二句。" * 20
    punct_segments = processor.split_text_by_punctuation(punctuation_text)
    assert len(punct_segments) >= 2


def test_tts_text_numbered_sections_and_should_use_false_case():
    p = TTSTextProcessor(max_text_length=60)

    short = "你好，这是简短文本。"
    assert p.should_use_segmented_synthesis(short) is False

    text = (
        "### 1. 第一部分内容足够长，包含较多字符用于分段检测和语音合成验证。\n"
        "这里继续补充第一部分内容，确保段落长度超过阈值。\n"
        "### 2. 第二部分也足够长，继续用于验证分段策略。\n"
        "继续补充第二部分，确保结构稳定。"
    )
    parts = p.split_text_by_numbered_sections(text)
    assert len(parts) >= 2


def test_tts_text_punctuation_split_hard_limit_and_merge():
    p = TTSTextProcessor(max_text_length=30)

    no_punct = "这是一段没有标点的超长文本用于触发硬切分逻辑" * 4
    parts = p.split_text_by_punctuation(no_punct)
    assert parts
    assert all(len(x) > 0 for x in parts)

    with_punct = "第一句非常长非常长非常长。第二句非常长非常长非常长。第三句。"
    parts2 = p.split_text_by_punctuation(with_punct)
    assert len(parts2) >= 1
