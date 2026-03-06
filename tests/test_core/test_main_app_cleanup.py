"""
测试 MainApp 的 cleanup 方法
"""
from yuntai.core.main_app import MainApp


def test_main_app_cleanup():
    """测试 MainApp 的 cleanup 方法"""
    app = MainApp()
    # 调用 cleanup 方法
    app.cleanup()
    # 如果没有抛出异常，测试就通过
    assert True
