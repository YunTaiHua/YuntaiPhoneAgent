"""
LangChain Callbacks 功能测试
验证所有回调处理器是否正常工作
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from yuntai.callbacks import (
    StreamingCallbackHandler,
    LoggingCallbackHandler,
    PerformanceCallbackHandler,
    MemoryCallbackHandler,
    get_callback_manager,
    reset_callback_manager
)


def test_streaming_handler():
    """测试流式输出处理器"""
    print("\n=== 测试 StreamingCallbackHandler ===")
    
    tokens = []
    complete_response = ""
    
    def on_token(token):
        tokens.append(token)
        print(token, end='', flush=True)
    
    def on_complete(response):
        nonlocal complete_response
        complete_response = response
    
    handler = StreamingCallbackHandler(
        output_callback=on_token,
        complete_callback=on_complete
    )
    
    # 模拟 LLM 调用
    from langchain_core.outputs import LLMResult, ChatGeneration
    from langchain_core.messages import AIMessage
    
    handler.on_llm_start({}, ["测试提示"])
    
    # 模拟 token 生成
    test_tokens = ["你", "好", "，", "我", "是", "AI"]
    for token in test_tokens:
        handler.on_llm_new_token(token)
    
    # 模拟 LLM 结束
    generation = ChatGeneration(message=AIMessage(content="你好，我是AI"))
    result = LLMResult(generations=[[generation]])
    handler.on_llm_end(result)
    
    # 验证
    assert len(tokens) == len(test_tokens), "Token 数量不匹配"
    assert complete_response == "你好，我是AI", "完整响应不匹配"
    print("\n✅ StreamingCallbackHandler 测试通过")


def test_logging_handler():
    """测试日志记录处理器"""
    print("\n=== 测试 LoggingCallbackHandler ===")
    
    handler = LoggingCallbackHandler(
        enable_console=True,
        enable_detailed=False
    )
    
    # 模拟 LLM 调用
    handler.on_llm_start({}, ["测试提示"])
    
    from langchain_core.outputs import LLMResult, ChatGeneration
    from langchain_core.messages import AIMessage
    
    generation = ChatGeneration(message=AIMessage(content="测试响应"))
    result = LLMResult(
        generations=[[generation]],
        llm_output={"token_usage": {"total_tokens": 100}}
    )
    handler.on_llm_end(result)
    
    # 模拟 Chain 调用
    handler.on_chain_start({"name": "test_chain"}, {"input": "test"})
    handler.on_chain_end({"output": "result"})
    
    # 模拟 Tool 调用
    handler.on_tool_start({"name": "test_tool"}, "test input")
    handler.on_tool_end("test output")
    
    # 获取统计
    stats = handler.get_statistics()
    assert stats['llm_calls'] == 1, "LLM 调用次数不匹配"
    assert stats['chain_calls'] == 1, "Chain 调用次数不匹配"
    assert stats['tool_calls'] == 1, "Tool 调用次数不匹配"
    assert stats['total_tokens'] == 100, "Token 使用量不匹配"
    
    print("✅ LoggingCallbackHandler 测试通过")


def test_performance_handler():
    """测试性能监控处理器"""
    print("\n=== 测试 PerformanceCallbackHandler ===")
    
    handler = PerformanceCallbackHandler(enable_console=False)
    
    # 模拟 LLM 调用
    import time
    handler.on_llm_start({}, ["测试提示"])
    time.sleep(0.1)  # 模拟耗时
    
    from langchain_core.outputs import LLMResult, ChatGeneration
    from langchain_core.messages import AIMessage
    
    generation = ChatGeneration(message=AIMessage(content="测试"))
    result = LLMResult(generations=[[generation]])
    handler.on_llm_end(result)
    
    # 获取性能统计
    stats = handler.get_performance_stats()
    assert stats['llm']['count'] == 1, "LLM 调用次数不匹配"
    assert stats['llm']['avg'] >= 0.1, "耗时统计不准确"
    
    print(f"LLM 平均耗时: {stats['llm']['avg']:.3f}秒")
    print("✅ PerformanceCallbackHandler 测试通过")


def test_memory_handler():
    """测试记忆管理处理器"""
    print("\n=== 测试 MemoryCallbackHandler ===")
    
    # 创建简单的记忆管理器
    class SimpleMemoryManager:
        def __init__(self):
            self.messages = []
        
        def add_message(self, role, content):
            self.messages.append({"role": role, "content": content})
    
    memory_manager = SimpleMemoryManager()
    handler = MemoryCallbackHandler(
        memory_manager=memory_manager,
        auto_save=True
    )
    
    # 模拟 LLM 调用
    handler.on_llm_start({}, ["用户输入"])
    
    from langchain_core.outputs import LLMResult, ChatGeneration
    from langchain_core.messages import AIMessage
    
    generation = ChatGeneration(message=AIMessage(content="AI 响应"))
    result = LLMResult(generations=[[generation]])
    handler.on_llm_end(result)
    
    # 验证记忆
    assert len(memory_manager.messages) == 2, "消息数量不匹配"
    assert memory_manager.messages[0]['role'] == "user", "用户消息不匹配"
    assert memory_manager.messages[1]['role'] == "assistant", "AI 消息不匹配"
    
    # 获取历史
    history = handler.get_conversation_history()
    assert len(history) == 1, "历史记录数量不匹配"
    
    print("✅ MemoryCallbackHandler 测试通过")


def test_callback_manager():
    """测试回调管理器"""
    print("\n=== 测试 CallbackManager ===")
    
    # 重置管理器
    reset_callback_manager()
    manager = get_callback_manager()
    
    # 创建并注册处理器
    streaming = StreamingCallbackHandler()
    logging = LoggingCallbackHandler(enable_console=False)
    
    manager.register_handler("streaming", streaming, is_global=True)
    manager.register_handler("logging", logging, is_global=False)
    
    # 获取处理器
    assert manager.get_handler("streaming") == streaming, "获取处理器失败"
    assert manager.get_handler("logging") == logging, "获取处理器失败"
    
    # 获取回调列表
    callbacks = manager.get_callbacks(include_global=True)
    assert len(callbacks) == 1, "全局回调数量不匹配"
    
    callbacks = manager.get_callbacks(include_global=False, handler_names=["logging"])
    assert len(callbacks) == 1, "指定回调数量不匹配"
    
    # 注销处理器
    manager.unregister_handler("logging")
    assert manager.get_handler("logging") is None, "注销失败"
    
    print("✅ CallbackManager 测试通过")


def test_integration():
    """集成测试：模拟真实使用场景"""
    print("\n=== 集成测试 ===")
    
    # 重置并设置回调
    reset_callback_manager()
    manager = get_callback_manager()
    
    # 注册处理器
    tokens = []
    streaming = StreamingCallbackHandler(
        output_callback=lambda t: tokens.append(t)
    )
    logging = LoggingCallbackHandler(enable_console=False)
    
    manager.register_handler("streaming", streaming, is_global=True)
    manager.register_handler("logging", logging, is_global=True)
    
    # 模拟 Agent 调用
    print("模拟 ChatAgent 调用...")
    
    # 获取回调
    callbacks = manager.get_callbacks(include_global=True)
    print(f"获取到 {len(callbacks)} 个回调处理器")
    
    # 模拟 LLM 调用
    from langchain_core.messages import SystemMessage, HumanMessage
    from langchain_core.outputs import LLMResult, ChatGeneration
    from langchain_core.messages import AIMessage
    
    for handler in callbacks:
        handler.on_llm_start({}, ["测试"])
    
    # 模拟 token 生成
    test_response = "这是一个测试响应"
    from uuid import uuid4
    
    for char in test_response:
        for handler in callbacks:
            if hasattr(handler, 'on_llm_new_token'):
                # 创建模拟的 chunk 对象
                class MockChunk:
                    def __init__(self, content):
                        self.choices = [type('obj', (object,), {
                            'delta': type('obj', (object,), {'content': content})
                        })]
                
                # on_llm_new_token 需要 run_id 参数
                handler.on_llm_new_token(
                    char, 
                    chunk=MockChunk(char),
                    run_id=uuid4()
                )
    
    # 模拟结束
    generation = ChatGeneration(message=AIMessage(content=test_response))
    result = LLMResult(generations=[[generation]])
    for handler in callbacks:
        handler.on_llm_end(result)
    
    # 验证
    assert len(tokens) == len(test_response), "流式输出 token 数量不匹配"
    stats = logging.get_statistics()
    assert stats['llm_calls'] == 1, "日志记录不匹配"
    
    print(f"流式输出捕获了 {len(tokens)} 个 token")
    print(f"日志记录了 {stats['llm_calls']} 次 LLM 调用")
    print("集成测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始测试 LangChain Callbacks 功能")
    print("=" * 60)
    
    try:
        test_streaming_handler()
        test_logging_handler()
        test_performance_handler()
        test_memory_handler()
        test_callback_manager()
        test_integration()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
