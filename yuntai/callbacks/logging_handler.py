"""
日志记录回调处理器
用于记录 LLM 调用、Chain 执行、Tool 调用等过程的详细日志
"""
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.agents import AgentAction, AgentFinish


def _get_default_log_file() -> str:
    """获取默认日志文件路径"""
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    log_dir = os.path.join(project_root, "temp", "log")
    
    # 确保 log 目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 使用日期作为日志文件名
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"langchain_callbacks_{today}.log")
    
    return log_file


class LoggingCallbackHandler(BaseCallbackHandler):
    """
    日志记录回调处理器
    
    记录所有 LangChain 组件的执行过程，包括：
    - LLM 调用（开始、结束、错误）
    - Chain 执行（开始、结束）
    - Tool 调用（开始、结束）
    - Agent 动作（开始、完成）
    """
    
    def __init__(
        self,
        log_file: Optional[str] = None,
        enable_console: bool = False,
        enable_detailed: bool = True
    ):
        """
        初始化日志记录处理器
        
        Args:
            log_file: 日志文件路径（默认为 temp/log/langchain_callbacks_YYYY-MM-DD.log）
            enable_console: 是否输出到控制台（默认 False，只写入文件）
            enable_detailed: 是否记录详细信息
        """
        super().__init__()
        
        # 如果未指定日志文件，使用默认路径
        if log_file is None:
            self.log_file = _get_default_log_file()
        else:
            self.log_file = log_file
        
        self.enable_console = enable_console
        self.enable_detailed = enable_detailed
        
        # 统计信息
        self._llm_calls = 0
        self._chain_calls = 0
        self._tool_calls = 0
        self._agent_actions = 0
        self._total_tokens = 0
        
    def _log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}"
        
        if self.enable_console:
            print(log_line)
        
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_line + '\n')
            except Exception as e:
                print(f"⚠️ 写入日志文件失败: {e}")
    
    # ==================== LLM 回调 ====================
    
    def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """LLM 开始调用"""
        self._llm_calls += 1
        
        model = kwargs.get('invocation_params', {}).get('model', 'unknown')
        
        # 始终写入日志文件
        summary = f"🤖 LLM 调用 #{self._llm_calls} - {model}"
        self._log(summary)
        
        if self.enable_detailed:
            for i, prompt in enumerate(prompts[:3]):  # 只显示前3个
                self._log(f"   提示词 {i+1}: {prompt[:100]}...")
        
        # 如果启用控制台输出，也输出到控制台
        if self.enable_console:
            if self.enable_detailed:
                print(summary)
                for i, prompt in enumerate(prompts[:3]):
                    print(f"   提示词 {i+1}: {prompt[:100]}...")
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 调用结束"""
        # 统计 token 使用
        if response.llm_output and 'token_usage' in response.llm_output:
            usage = response.llm_output['token_usage']
            total_tokens = usage.get('total_tokens', 0)
            self._total_tokens += total_tokens
            
            # 始终写入日志文件
            summary = f"✅ LLM 调用结束 - Token: {total_tokens}"
            self._log(summary)
            
            if self.enable_detailed and response.generations:
                content = str(response.generations[0][0].text)[:200]
                self._log(f"   生成内容: {content}...")
            
            # 如果启用控制台输出，也输出到控制台
            if self.enable_console:
                print(summary)
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """LLM 调用错误"""
        self._log(f"❌ LLM 调用错误: {str(error)}", level="ERROR")
    
    # ==================== Chain 回调 ====================
    
    def on_chain_start(
        self, 
        serialized: Dict[str, Any], 
        inputs: Dict[str, Any], 
        **kwargs: Any
    ) -> None:
        """Chain 开始执行"""
        self._chain_calls += 1
        
        chain_name = serialized.get('name', 'unknown')
        self._log(f"🔗 Chain 开始执行 (#{self._chain_calls}) - 名称: {chain_name}")
        
        if self.enable_detailed:
            for key, value in list(inputs.items())[:3]:
                value_str = str(value)[:100]
                self._log(f"   输入 {key}: {value_str}...")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Chain 执行结束"""
        self._log(f"✅ Chain 执行结束")
        
        if self.enable_detailed:
            for key, value in list(outputs.items())[:3]:
                value_str = str(value)[:100]
                self._log(f"   输出 {key}: {value_str}...")
    
    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Chain 执行错误"""
        self._log(f"❌ Chain 执行错误: {str(error)}", level="ERROR")
    
    # ==================== Tool 回调 ====================
    
    def on_tool_start(
        self, 
        serialized: Dict[str, Any], 
        input_str: str, 
        **kwargs: Any
    ) -> None:
        """Tool 开始调用"""
        self._tool_calls += 1
        
        tool_name = serialized.get('name', 'unknown')
        self._log(f"🔧 Tool 开始调用 (#{self._tool_calls}) - 名称: {tool_name}")
        
        if self.enable_detailed:
            self._log(f"   输入: {input_str[:100]}...")
    
    def on_tool_end(
        self, 
        output: str, 
        **kwargs: Any
    ) -> None:
        """Tool 调用结束"""
        self._log(f"✅ Tool 调用结束")
        
        if self.enable_detailed:
            self._log(f"   输出: {output[:100]}...")
    
    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Tool 调用错误"""
        self._log(f"❌ Tool 调用错误: {str(error)}", level="ERROR")
    
    # ==================== Agent 回调 ====================
    
    def on_agent_action(
        self, 
        action: AgentAction, 
        **kwargs: Any
    ) -> None:
        """Agent 执行动作"""
        self._agent_actions += 1
        
        self._log(f"🤖 Agent 动作 (#{self._agent_actions})")
        self._log(f"   工具: {action.tool}")
        self._log(f"   输入: {str(action.tool_input)[:100]}...")
    
    def on_agent_finish(
        self, 
        finish: AgentFinish, 
        **kwargs: Any
    ) -> None:
        """Agent 执行完成"""
        self._log(f"✅ Agent 执行完成")
        
        if self.enable_detailed:
            output_str = str(finish.return_values)[:100]
            self._log(f"   结果: {output_str}...")
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "llm_calls": self._llm_calls,
            "chain_calls": self._chain_calls,
            "tool_calls": self._tool_calls,
            "agent_actions": self._agent_actions,
            "total_tokens": self._total_tokens,
        }
    
    def reset_statistics(self):
        """重置统计信息"""
        self._llm_calls = 0
        self._chain_calls = 0
        self._tool_calls = 0
        self._agent_actions = 0
        self._total_tokens = 0
    
    def print_summary(self):
        """打印统计摘要"""
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
    
    在日志记录的基础上，增加性能监控功能
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 性能统计
        self._llm_times = []
        self._chain_times = []
        self._tool_times = []
        
        # 时间戳记录
        self._start_times = {}
    
    def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """LLM 开始调用"""
        super().on_llm_start(serialized, prompts, **kwargs)
        
        import time
        self._start_times['llm'] = time.time()
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM 调用结束"""
        import time
        
        if 'llm' in self._start_times:
            elapsed = time.time() - self._start_times['llm']
            self._llm_times.append(elapsed)
            self._log(f"⏱️ LLM 调用耗时: {elapsed:.2f}秒")
        
        super().on_llm_end(response, **kwargs)
    
    def on_chain_start(
        self, 
        serialized: Dict[str, Any], 
        inputs: Dict[str, Any], 
        **kwargs: Any
    ) -> None:
        """Chain 开始执行"""
        super().on_chain_start(serialized, inputs, **kwargs)
        
        import time
        self._start_times['chain'] = time.time()
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Chain 执行结束"""
        import time
        
        if 'chain' in self._start_times:
            elapsed = time.time() - self._start_times['chain']
            self._chain_times.append(elapsed)
            self._log(f"⏱️ Chain 执行耗时: {elapsed:.2f}秒")
        
        super().on_chain_end(outputs, **kwargs)
    
    def on_tool_start(
        self, 
        serialized: Dict[str, Any], 
        input_str: str, 
        **kwargs: Any
    ) -> None:
        """Tool 开始调用"""
        super().on_tool_start(serialized, input_str, **kwargs)
        
        import time
        self._start_times['tool'] = time.time()
    
    def on_tool_end(
        self, 
        output: str, 
        **kwargs: Any
    ) -> None:
        """Tool 调用结束"""
        import time
        
        if 'tool' in self._start_times:
            elapsed = time.time() - self._start_times['tool']
            self._tool_times.append(elapsed)
            self._log(f"⏱️ Tool 调用耗时: {elapsed:.2f}秒")
        
        super().on_tool_end(output, **kwargs)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        import statistics
        
        def calc_stats(times):
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
        """打印性能摘要"""
        stats = self.get_performance_stats()
        
        self._log("=" * 50)
        self._log("📊 性能统计摘要")
        self._log("=" * 50)
        
        for component, data in stats.items():
            if data['count'] > 0:
                self._log(f"\n{component.upper()}:")
                self._log(f"  调用次数: {data['count']}")
                self._log(f"  平均耗时: {data['avg']:.2f}秒")
                self._log(f"  最小耗时: {data['min']:.2f}秒")
                self._log(f"  最大耗时: {data['max']:.2f}秒")
        
        self._log("=" * 50)
