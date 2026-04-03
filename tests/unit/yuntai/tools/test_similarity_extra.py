from yuntai.tools.similarity import calculate_similarity, clean_text, is_similar


def test_clean_text_removes_symbols_and_lowercases():
    assert clean_text("Hello, 世界!!!") == "hello世界"


def test_is_similar_handles_empty_and_exact_and_contains():
    assert is_similar("", "abc") is False
    assert is_similar("你好！", "你好") is True
    assert is_similar("今天心情很好", "心情很好") is True


def test_is_similar_uses_fuzzy_threshold():
    assert is_similar("abcdef", "abcxyz", threshold=0.4) is True
    assert is_similar("abcdef", "xyzuvw", threshold=0.9) is False


def test_calculate_similarity_branches():
    assert calculate_similarity("", "x") == 0.0
    assert calculate_similarity("!!!", "???") == 0.0
    assert calculate_similarity("你好", "你好！") == 1.0
    value = calculate_similarity("abcdefgh", "abcdwxyz")
    assert 0.0 < value < 1.0
