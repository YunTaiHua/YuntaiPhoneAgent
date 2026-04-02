"""
LangGraph 持续回复工作流模块
============================

本模块实现持续回复工作流，使用 LangGraph 构建状态图管理工作流。

主要功能：
    - 构建工作流状态图
    - 管理节点间的路由
    - 支持终止控制
    - 执行持续回复流程

类说明：
    - ReplyGraph: 持续回复工作流类

使用示例：
    >>> from yuntai.graphs import ReplyGraph
    >>> 
    >>> # 创建工作流
    >>> graph = ReplyGraph(file_manager, tts_manager)
    >>> 
    >>> # 运行工作流
    >>> success, result = graph.run("微信", "张三", device_id="device_123")
    >>> 
    >>> # 停止工作流
    >>> graph.stop()
"""
import logging
import threading
from typing import Literal

from langgraph.graph import StateGraph, END
from phone_agent.events import emit_agent_event

from yuntai.graphs.state import ReplyState, ReplyStateBuilder
from yuntai.graphs.nodes import (
    extract_records,
    parse_messages,
    determine_ownership,
    check_new_message,
    generate_reply,
    send_message,
    update_memory,
    check_continue,
    do_wait,
)
from yuntai.graphs.nodes.memory import set_managers
from yuntai.graphs.nodes.control import set_terminate_event

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class ReplyGraph:
    """
    持续回复工作流
    
    使用 LangGraph 构建状态图，管理持续回复的工作流。
    支持终止控制和状态管理。
    
    Attributes:
        file_manager: 文件管理器实例
        tts_manager: TTS 管理器实例
        terminate_event: 终止事件
        graph: 编译后的状态图
        _running: 是否正在运行
    
    使用示例：
        >>> graph = ReplyGraph()
        >>> success, result = graph.run("微信", "张三")
    """
    
    def __init__(
        self,
        file_manager: object = None,
        tts_manager: object = None
    ) -> None:
        """
        初始化回复工作流
        
        Args:
            file_manager: 文件管理器实例，用于保存对话历史
            tts_manager: TTS 管理器实例，用于语音播报
        """
        # 存储管理器实例
        self.file_manager = file_manager
        self.tts_manager = tts_manager
        
        # 创建终止事件
        self.terminate_event = threading.Event()
        
        # 设置全局管理器（传递给节点）
        set_managers(file_manager, tts_manager)
        set_terminate_event(self.terminate_event)
        
        # 构建工作流图
        self.graph = self._build_graph()
        
        # 运行状态标志
        self._running = False
        
        logger.debug("ReplyGraph 初始化完成")

    def _build_graph(self) -> StateGraph:
        """
        构建工作流图
        
        创建状态图并添加节点和边，定义工作流的执行流程。
        
        Returns:
            StateGraph: 编译后的状态图
        
        工作流结构：
            extract -> parse -> ownership -> check_new -> reply -> send -> memory -> wait -> check_continue
                                                                              ↑                    |
                                                                              +--------------------+
        """
        logger.debug("构建工作流图")
        
        # 创建状态图构建器
        builder = StateGraph(ReplyState)
        
        # ==================== 添加节点 ====================
        # 提取聊天记录节点
        builder.add_node("extract", extract_records)
        # 解析消息节点
        builder.add_node("parse", parse_messages)
        # 判断消息归属节点
        builder.add_node("ownership", determine_ownership)
        # 检查新消息节点
        builder.add_node("check_new", check_new_message)
        # 生成回复节点
        builder.add_node("reply", generate_reply)
        # 发送消息节点
        builder.add_node("send", send_message)
        # 更新记忆节点
        builder.add_node("memory", update_memory)
        # 等待节点
        builder.add_node("wait", do_wait)
        # 检查是否继续节点
        builder.add_node("check_continue", check_continue)
        
        # ==================== 设置入口点 ====================
        builder.set_entry_point("extract")
        
        # ==================== 添加固定边 ====================
        # extract -> parse -> ownership -> check_new
        builder.add_edge("extract", "parse")
        builder.add_edge("parse", "ownership")
        builder.add_edge("ownership", "check_new")
        
        # ==================== 添加条件边 ====================
        # check_new 后的路由：有新消息则回复，否则等待
        builder.add_conditional_edges(
            "check_new",
            self._route_after_check,
            {
                "reply": "reply",
                "wait": "wait",
            }
        )
        
        # reply 后的路由：有回复则发送，否则等待
        builder.add_conditional_edges(
            "reply",
            self._route_after_reply,
            {
                "send": "send",
                "wait": "wait",
            }
        )
        
        # ==================== 添加固定边 ====================
        # send -> memory -> wait
        builder.add_edge("send", "memory")
        builder.add_edge("memory", "wait")
        
        # wait -> check_continue
        builder.add_edge("wait", "check_continue")
        
        # ==================== 添加条件边 ====================
        # check_continue 后的路由：继续则回到 extract，否则结束
        builder.add_conditional_edges(
            "check_continue",
            self._route_continue,
            {
                "continue": "extract",
                "end": END,
            }
        )
        
        # 编译并返回状态图
        logger.debug("工作流图构建完成")
        return builder.compile()

    def _route_after_check(self, state: ReplyState) -> Literal["reply", "wait"]:
        """
        检查新消息后的路由
        
        根据是否有新消息决定下一步操作。
        
        Args:
            state: 当前状态
        
        Returns:
            "reply" 或 "wait"
        """
        # 检查终止标志
        if self.terminate_event.is_set() or state.get("terminate_flag"):
            logger.debug("检测到终止标志，路由到 wait")
            return "wait"
        
        # 有新消息则回复
        if state.get("is_new_message"):
            logger.debug("有新消息，路由到 reply")
            return "reply"
        
        # 无新消息则等待
        return "wait"

    def _route_after_reply(self, state: ReplyState) -> Literal["send", "wait"]:
        """
        生成回复后的路由
        
        根据是否成功生成回复决定下一步操作。
        
        Args:
            state: 当前状态
        
        Returns:
            "send" 或 "wait"
        """
        # 检查终止标志
        if self.terminate_event.is_set() or state.get("terminate_flag"):
            logger.debug("检测到终止标志，路由到 wait")
            return "wait"
        
        # 有生成的回复则发送
        if state.get("generated_reply"):
            logger.debug("有生成的回复，路由到 send")
            return "send"
        
        # 无回复则等待
        return "wait"

    def _route_continue(self, state: ReplyState) -> Literal["continue", "end"]:
        """
        继续检查后的路由
        
        根据是否应该继续决定下一步操作。
        
        Args:
            state: 当前状态
        
        Returns:
            "continue" 或 "end"
        """
        # 检查终止标志
        if self.terminate_event.is_set() or state.get("terminate_flag"):
            logger.debug("检测到终止标志，路由到 end")
            return "end"
        
        # 应该继续则回到 extract
        if state.get("should_continue"):
            logger.debug("继续循环，路由到 extract")
            return "continue"
        
        # 否则结束
        return "end"

    def run(
        self,
        app_name: str,
        chat_object: str,
        device_id: str = "",
        max_cycles: int = 30
    ) -> tuple[bool, str]:
        """
        运行持续回复
        
        启动持续回复工作流，监控聊天记录并自动回复。
        
        Args:
            app_name: APP 名称（如 "微信"、"QQ"）
            chat_object: 聊天对象名称
            device_id: 设备 ID
            max_cycles: 最大循环次数，默认为 30
        
        Returns:
            tuple[bool, str]: (是否成功, 结果消息)
        
        使用示例：
            >>> success, result = graph.run("微信", "张三", max_cycles=20)
        """
        logger.info("启动持续回复: APP=%s, 对象=%s, 最大循环=%d", app_name, chat_object, max_cycles)
        
        # 打印启动信息
        emit_agent_event("status", {"message": "🔄 启动持续回复流程"}, source="yuntai.reply_graph")
        emit_agent_event("status", {"message": f"🎯 目标：{app_name} -> {chat_object}"}, source="yuntai.reply_graph")
        emit_agent_event("status", {"message": "💡 点击终止按钮结束"}, source="yuntai.reply_graph")
        
        # 清除终止事件
        self.terminate_event.clear()
        self._running = True
        
        # 创建初始状态
        initial_state = ReplyStateBuilder.create(
            app_name=app_name,
            chat_object=chat_object,
            device_id=device_id,
            max_cycles=max_cycles,
        )
        
        try:
            # 配置递归限制
            config = {"recursion_limit": max_cycles * 12}
            
            # 执行工作流
            final_state = self.graph.invoke(initial_state, config=config)
            
            # 检查终止原因
            if self.terminate_event.is_set():
                logger.info("持续回复已终止")
                return True, "持续回复已终止"
            else:
                logger.info("持续回复完成，达到最大循环次数: %d", max_cycles)
                return True, f"持续回复完成（达到最大循环次数 {max_cycles}）"
                
        except Exception as e:
            # 记录错误日志
            logger.error("工作流执行异常: %s", str(e), exc_info=True)
            emit_agent_event(
                "error",
                {"message": f"工作流执行异常: {str(e)}"},
                source="yuntai.reply_graph",
                level="error",
            )
            return False, f"执行失败: {str(e)}"
        finally:
            self._running = False

    def stop(self) -> None:
        """
        停止工作流
        
        设置终止事件，工作流会在下一个检查点停止。
        """
        logger.info("停止工作流")
        self.terminate_event.set()

    def is_running(self) -> bool:
        """
        检查是否正在运行
        
        Returns:
            bool: 是否正在运行
        """
        return self._running

    def reset(self) -> None:
        """
        重置状态
        
        清除终止事件和运行状态，准备下一次运行。
        """
        logger.debug("重置工作流状态")
        self.terminate_event.clear()
        self._running = False
