"""
测试 config.py 的 print_config_summary 函数
"""
from yuntai.core.config import print_config_summary


def test_print_config_summary():
    """测试打印配置摘要"""
    # 这个函数只是打印配置信息，不需要验证输出
    print_config_summary()
    # 如果没有抛出异常，测试就通过
    assert True
