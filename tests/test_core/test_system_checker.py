"""
测试 utils.py 的 Utils 类
"""
from yuntai.core.utils import Utils


def test_utils_check_system_requirements():
    """测试系统要求检查"""
    utils = Utils()
    # 这个方法会检查 ADB 是否安装
    result = utils.check_system_requirements()
    # 不需要验证结果，只要不抛出异常就行
    assert isinstance(result, bool)
