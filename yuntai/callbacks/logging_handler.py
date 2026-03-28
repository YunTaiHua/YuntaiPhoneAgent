"""
日志记录回调处理器模块
======================

本模块实现日志记录回调处理器，用于记录 LLM 调用、Chain 执行、Tool 调用等过程的详细日志。

主要功能：
    - LLM 调用日志：记录 LLM 调用的开始、结束、错误
    - Chain 执行日志：记录 Chain 的执行过程
    - Tool 调用日志：记录 Tool 的调用过程
    - Agent 动作日志：记录 Agent 的执行动作
    - 性能监控：监控各组件的执行时间

类说明：
    - LoggingCallbackHandler: 基础日志记录处理器
    - PerformanceCallbackHandler: 性能监控处理器

使用示例：
    >>> from yuntai.callbacks import LoggingCallbackHandler
    >>> 
    >>> # 创建处理器
    >>> handler = LoggingCallbackHandler(
    ...     log_file="logs/callback.log",
    ...     enable_console=True
    ... )
    >>> 
    >>> # 在模型调用时使用
    >>> response = model.invoke(messages, config={"callbacks": [handler]})
"""
import logging
from pathlib import Path
from datetime import datetime
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.agents import AgentAction, AgentFinish

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


def _get_default_log_file() -> str:
    """
    获取默认日志文件路径
    
    根据当前日期生成日志文件路径，格式为：
    temp/log/langchain_callbacks_YYYY-MM-DD.log
    
    Returns:
        str: 日志文件的完整路径
    """
    # 获取当前文件所在目录
    current_dir = Path(__file__).resolve().parent
    # 计算项目根目录
    project_root = current_dir.parent.parent
    # 日志目录
    log_dir = project_root / "temp" / "log"
    
    # 确保日志目录存在
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 根据日期生成日志文件名
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"langchain_callbacks_{today}.log"
    
    return str(log_file)


class LoggingCallbackHandler(BaseCallbackHandler):
    """
    日志记录回调处理器
    
    记录所有 LangChain 组件的执行过程，包括：
    - LLM 调用（开始、结束、错误）
    - Chain 执行（开始、结束）
    - Tool 调用（开始、结束）
    - Agent 动作（开始、完成）
    
    Attributes:
        log_file: 日志文件路径
        enable_console: 是否输出到控制台
        enable_detailed: 是否记录详细信息
        _llm_calls: LLM 调用次数
        _chain_calls: Chain 调用次数
        _tool_calls: Tool 调用次数
        _agent_actions: Agent 动作次数
        _total_tokens: 总 token 使用量
    
    使用示例：
        >>> handler = LoggingCallbackHandler(enable_console=True)
        >>> response = model.invoke(messages, config={"callbacks": [handler]})
    """
    
    def __init__(
        self,
        log_file: str | None = None,
        enable_console: bool = False,
        enable_detailed: bool = True
    ):
        """
        初始化日志记录处理器
        
        Args:
            log_file: 日志文件路径，默认为 temp/log/langchain_callbacks_YYYY-MM-DD.log
            enable_console: 是否输出到控制台，默认 False（只写入文件）
            enable_detailed: 是否记录详细信息，默认 True
        """
        super().__init__()
        
        # 如果未指定日志文件，使用默认路径
        if log_file is None:
            self.log_file = _get_default_log_file()
        else:
            self.log_file = log_file
        
        # 是否输出到控制台
        self.enable_console = enable_console
        # 是否记录详细信息
        self.enable_detailed = enable_detailed
        
        # 统计信息初始化
        self._llm_calls = 0      # LLM 调用次数
        self._chain_calls = 0    # Chain 调用次数
        self._tool_calls = 0     # Tool 调用次数
        self._agent_actions = 0  # Agent 动作次数
        self._total_tokens = 0   # 总 token 使用量
        
        logger.debug("LoggingCallbackHandler 初始化完成，日志文件: %s", self.log_file)
        
    def _log(self, message: str, level: str = "INFO"):
        """
        记录日志
        
        将日志写入文件，可选输出到控制台。
        
        Args:
            message: 日志消息内容
            level: 日志级别，默认为 INFO
        """
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 格式化日志行
        log_line = f"[{timestamp}] [{level}] {message}"
        
        # 如果启用控制台输出，打印到控制台
        if self.enable_console:
            print(log_line)
        
        # 写入日志文件
        if self.log_file:
            try:
                log_path = Path(self.log_file)
                # 确保日志目录存在
                log_path.parent.mkdir(parents=True, exist_ok=True)
                # 追加写入日志
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line + '\n')
            except Exception as e:
                logger.warning("写入日志文件失败: %s", str(e))
                print(f"⚠️ 写入日志文件失败: {e}")
    
    # ==================== LLM 回调 ====================
    
    def on_llm_start(
        self,
        serialized: dict[str, object],
        prompts: list[str],
        **kwargs: object
    ) -> None:
        """
        LLM 开始调用
        
        记录 LLM 调用开始事件，包括模型名称和提示词预览。
        
        Args:
            serialized: 序列化的模型信息
            prompts: 提示词列表
            **kwargs: 其他参数
        """
        # 增加调用计数
        self._llm_calls += 1
        
        # 获取模型名称
        model = kwargs.get('invocation_params', {}).get('model', 'unknown')
        
        # 记录日志摘要
        summary = f"🤖 LLM 调用 #{self._llm_calls} - {model}"
        self._log(summary)
        
        # 如果启用详细信息，记录提示词预览
        if self.enable_detailed:
            for i, prompt in enumerate(prompts[:3]):  # 只显示前3个
                self._log(f"   提示词 {i+1}: {prompt[:100]}...")
        
        # 如果启用控制台输出，也输出到控制台
        if self.enable_console:
            if self.enable_detailed:
                print(summary)
                for i, prompt in enumerate(prompts[:3]):
                    print(f"   提示词 {i+1}: {prompt[:100]}...")
    
    def on_llm_end(self, response: LLMResult, **kwargs: object) -> None:
        """
        LLM 调用结束
        
        记录 LLM 调用结束事件，包括 token 使用量和生成内容预览。
        
        Args:
            response: LLM 响应结果
            **kwargs: 其他参数
        """
        # 统计 token 使用
        if response.llm_output and 'token_usage' in response.llm_output:
            usage = response.llm_output['token_usage']
            total_tokens = usage.get('total_tokens', 0)
            self._total_tokens += total_tokens
            
            # 记录日志摘要
            summary = f"✅ LLM 调用结束 - Token: {total_tokens}"
            self._log(summary)
            
            # 如果启用详细信息，记录生成内容预览
            if self.enable_detailed and response.generations:
                content = str(response.generations[0][0].text)[:200]
                self._log(f"   生成内容: {content}...")
            
            # 如果启用控制台输出，也输出到控制台
            if self.enable_console:
                print(summary)
    
    def on_llm_error(self, error: Exception, **kwargs: object) -> None:
        """
        LLM 调用错误
        
        记录 LLM 调用错误事件。
        
        Args:
            error: 异常对象
            **kwargs: 其他参数
        """
        logger.error("LLM 调用错误: %s", str(error))
        self._log(f"❌ LLM 调用错误: {str(error)}", level="ERROR")
    
    # ==================== Chain 回调 ====================
    
    def on_chain_start(
        self,
        serialized: dict[str, object],
        inputs: dict[str, object],
        **kwargs: object
    ) -> None:
        """
        Chain 开始执行
        
        记录 Chain 执行开始事件。
        
        Args:
            serialized: 序列化的 Chain 信息
            inputs: 输入参数
            **kwargs: 其他参数
        """
        # 增加调用计数
        self._chain_calls += 1
        
        # 获取 Chain 名称
        chain_name = serialized.get('name', 'unknown')
        self._log(f"🔗 Chain 开始执行 (#{self._chain_calls}) - 名称: {chain_name}")
        
        # 如果启用详细信息，记录输入参数预览
        if self.enable_detailed:
            for key, value in list(inputs.items())[:3]:
                value_str = str(value)[:100]
                self._log(f"   输入 {key}: {value_str}...")
    
    def on_chain_end(self, outputs: dict[str, object], **kwargs: object) -> None:
        """
        Chain 执行结束
        
        记录 Chain 执行结束事件。
        
        Args:
            outputs: 输出结果
            **kwargs: 其他参数
        """
        self._log(f"✅ Chain 执行结束")
        
        # 如果启用详细信息，记录输出结果预览
        if self.enable_detailed:
            for key, value in list(outputs.items())[:3]:
                value_str = str(value)[:100]
                self._log(f"   输出 {key}: {value_str}...")
    
    def on_chain_error(self, error: Exception, **kwargs: object) -> None:
        """
        Chain 执行错误
        
        记录 Chain 执行错误事件。
        
        Args:
            error: 异常对象
            **kwargs: 其他参数
        """
        logger.error("Chain 执行错误: %s", str(error))
        self._log(f"❌ Chain 执行错误: {str(error)}", level="ERROR")
    
    # ==================== Tool 回调 ====================
    
    def on_tool_start(
        self,
        serialized: dict[str, object],
        input_str: str,
        **kwargs: object
    ) -> None:
        """
        Tool 开始调用
        
        记录 Tool 调用开始事件。
        
        Args:
            serialized: 序列化的 Tool 信息
            input_str: 输入字符串
            **kwargs: 其他参数
        """
        # 增加调用计数
        self._tool_calls += 1
        
        # 获取 Tool 名称
        tool_name = serialized.get('name', 'unknown')
        self._log(f"🔧 Tool 开始调用 (#{self._tool_calls}) - 名称: {tool_name}")
        
        # 如果启用详细信息，记录输入预览
        if self.enable_detailed:
            self._log(f"   输入: {input_str[:100]}...")
    
    def on_tool_end(
        self,
        output: str,
        **kwargs: object
    ) -> None:
        """
        Tool 调用结束
        
        记录 Tool 调用结束事件。
        
        Args:
            output: 输出结果
            **kwargs: 其他参数
        """
        self._log(f"✅ Tool 调用结束")
        
        # 如果启用详细信息，记录输出预览
        if self.enable_detailed:
            self._log(f"   输出: {output[:100]}...")
    
    def on_tool_error(self, error: Exception, **kwargs: object) -> None:
        """
        Tool 调用错误
        
        记录 Tool 调用错误事件。
        
        Args:
            error: 异常对象
            **kwargs: 其他参数
        """
        logger.error("Tool 调用错误: %s", str(error))
        self._log(f"❌ Tool 调用错误: {str(error)}", level="ERROR")
    
    # ==================== Agent 回调 ====================
    
    def on_agent_action(
        self,
        action: AgentAction,
        **kwargs: object
    ) -> None:
        """
        Agent 执行动作
        
        记录 Agent 执行动作事件。
        
        Args:
            action: Agent 动作对象
            **kwargs: 其他参数
        """
        # 增加动作计数
        self._agent_actions += 1
        
        self._log(f"🤖 Agent 动作 (#{self._agent_actions})")
        self._log(f"   工具: {action.tool}")
        self._log(f"   输入: {str(action.tool_input)[:100]}...")
    
    def on_agent_finish(
        self,
        finish: AgentFinish,
        **kwargs: object
    ) -> None:
        """
        Agent 执行完成
        
        记录 Agent 执行完成事件。
        
        Args:
            finish: Agent 完成对象
            **kwargs: 其他参数
        """
        self._log(f"✅ Agent 执行完成")
        
        # 如果启用详细信息，记录结果预览
        if self.enable_detailed:
            output_str = str(finish.return_values)[:100]
            self._log(f"   结果: {output_str}...")
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> dict[str, object]:
        """
        获取统计信息
        
        Returns:
            包含各项统计数据的字典
        """
        return {
            "llm_calls": self._llm_calls,
            "chain_calls": self._chain_calls,
            "tool_calls": self._tool_calls,
            "agent_actions": self._agent_actions,
            "total_tokens": self._total_tokens,
        }
    
    def reset_statistics(self):
        """
        重置统计信息
        
        将所有统计数据归零。
        """
        logger.debug("重置统计信息")
        self._llm_calls = 0
        self._chain_calls = 0
        self._tool_calls = 0
        self._agent_actions = 0
        self._total_tokens = 0
    
    def print_summary(self):
        """
        打印统计摘要
        
        输出所有统计数据的摘要信息。
        """
        stats = self.get_statistics()
        self._log("=" * 50)
        self._log("📊 执行统计摘要")
        self._log("=" * 50)
        self._log(f"LLM 调用次数: {stats['llm_calls']}")
        self._log(f"Chain 执行次数: {stats['chain_calls']}")
        self._log(f"Tool 调用次数: {stats['tool_calls']}")
        self._log(f"Agent 动作次数: {stats['agent_actions']}")
        self._log(f"总 Token 使用: {stats['total_tokens']}")
        self._log("=" * 50)


class PerformanceCallbackHandler(LoggingCallbackHandler):
    """
    性能监控回调处理器
    
    在日志记录的基础上，增加性能监控功能。
    记录各组件的执行时间，提供性能统计。
    
    Attributes:
        _llm_times: LLM 调用耗时列表
        _chain_times: Chain 执行耗时列表
        _tool_times: Tool 调用耗时列表
        _start_times: 各组件开始时间戳字典
    
    使用示例：
        >>> handler = PerformanceCallbackHandler(enable_console=True)
        >>> response = model.invoke(messages, config={"callbacks": [handler]})
        >>> handler.print_performance_summary()
    """
    
    def __init__(self, *args, **kwargs):
        """
        初始化性能监控处理器
        
        Args:
            *args: 传递给父类的位置参数
            **kwargs: 传递给父类的关键字参数
        """
        super().__init__(*args, **kwargs)
        
        # 性能统计列表
        self._llm_times = []    # LLM 调用耗时列表
        self._chain_times = []  # Chain 执行耗时列表
        self._tool_times = []   # Tool 调用耗时列表
        
        # 时间戳记录字典
        self._start_times = {}
        
        logger.debug("PerformanceCallbackHandler 初始化完成")
    
    def on_llm_start(
        self,
        serialized: dict[str, object],
        prompts: list[str],
        **kwargs: object
    ) -> None:
        """
        LLM 开始调用，记录开始时间
        
        Args:
            serialized: 序列化的模型信息
            prompts: 提示词列表
            **kwargs: 其他参数
        """
        # 调用父类方法
        super().on_llm_start(serialized, prompts, **kwargs)
        
        # 记录开始时间
        import time
        self._start_times['llm'] = time.time()
    
    def on_llm_end(self, response: LLMResult, **kwargs: object) -> None:
        """
        LLM 调用结束，计算并记录耗时
        
        Args:
            response: LLM 响应结果
            **kwargs: 其他参数
        """
        import time
        
        # 计算耗时
        if 'llm' in self._start_times:
            elapsed = time.time() - self._start_times['llm']
            self._llm_times.append(elapsed)
            self._log(f"⏱️ LLM 调用耗时: {elapsed:.2f}秒")
        
        # 调用父类方法
        super().on_llm_end(response, **kwargs)
    
    def on_chain_start(
        self,
        serialized: dict[str, object],
        inputs: dict[str, object],
        **kwargs: object
    ) -> None:
        """
        Chain 开始执行，记录开始时间
        
        Args:
            serialized: 序列化的 Chain 信息
            inputs: 输入参数
            **kwargs: 其他参数
        """
        # 调用父类方法
        super().on_chain_start(serialized, inputs, **kwargs)
        
        # 记录开始时间
        import time
        self._start_times['chain'] = time.time()
    
    def on_chain_end(self, outputs: dict[str, object], **kwargs: object) -> None:
        """
        Chain 执行结束，计算并记录耗时
        
        Args:
            outputs: 输出结果
            **kwargs: 其他参数
        """
        import time
        
        # 计算耗时
        if 'chain' in self._start_times:
            elapsed = time.time() - self._start_times['chain']
            self._chain_times.append(elapsed)
            self._log(f"⏱️ Chain 执行耗时: {elapsed:.2f}秒")
        
        # 调用父类方法
        super().on_chain_end(outputs, **kwargs)
    
    def on_tool_start(
        self,
        serialized: dict[str, object],
        input_str: str,
        **kwargs: object
    ) -> None:
        """
        Tool 开始调用，记录开始时间
        
        Args:
            serialized: 序列化的 Tool 信息
            input_str: 输入字符串
            **kwargs: 其他参数
        """
        # 调用父类方法
        super().on_tool_start(serialized, input_str, **kwargs)
        
        # 记录开始时间
        import time
        self._start_times['tool'] = time.time()
    
    def on_tool_end(
        self,
        output: str,
        **kwargs: object
    ) -> None:
        """
        Tool 调用结束，计算并记录耗时
        
        Args:
            output: 输出结果
            **kwargs: 其他参数
        """
        import time
        
        # 计算耗时
        if 'tool' in self._start_times:
            elapsed = time.time() - self._start_times['tool']
            self._tool_times.append(elapsed)
            self._log(f"⏱️ Tool 调用耗时: {elapsed:.2f}秒")
        
        # 调用父类方法
        super().on_tool_end(output, **kwargs)
    
    def get_performance_stats(self) -> dict[str, object]:
        """
        获取性能统计
        
        计算各组件的平均、最小、最大耗时。
        
        Returns:
            包含各组件性能统计的字典
        """
        import statistics
        
        def calc_stats(times: list[float]) -> dict[str, float]:
            """
            计算统计数据
            
            Args:
                times: 时间列表
            
            Returns:
                包含 count, avg, min, max 的字典
            """
            if not times:
                return {"count": 0, "avg": 0, "min": 0, "max": 0}
            return {
                "count": len(times),
                "avg": statistics.mean(times),
                "min": min(times),
                "max": max(times),
            }
        
        return {
            "llm": calc_stats(self._llm_times),
            "chain": calc_stats(self._chain_times),
            "tool": calc_stats(self._tool_times),
        }
    
    def print_performance_summary(self):
        """
        打印性能摘要
        
        输出各组件的性能统计信息。
        """
        stats = self.get_performance_stats()
        
        self._log("=" * 50)
        self._log("📊 性能统计摘要")
        self._log("=" * 50)
        
        # 遍历各组件输出统计信息
        for component, data in stats.items():
            if data['count'] > 0:
                self._log(f"\n{component.upper()}:")
                self._log(f"  调用次数: {data['count']}")
                self._log(f"  平均耗时: {data['avg']:.2f}秒")
                self._log(f"  最小耗时: {data['min']:.2f}秒")
                self._log(f"  最大耗时: {data['max']:.2f}秒")
        
        self._log("=" * 50)
