"""
测试 AgentExecutor 的类方法
"""
from yuntai.core.agent_executor import AgentExecutor


def test_agent_executor_user_confirm():
    """测试用户确认方法"""
    # 这个方法需要先调用 user_input，否则会返回 False
    result = AgentExecutor.user_confirm()
    # 由于没有设置 stdin_write，应该返回 False 或不抛出异常
    assert isinstance(result, bool) or result is None
