"""
LangGraph 持续回复工作流
"""
import threading
from typing import Optional, Tuple, Literal

from langgraph.graph import StateGraph, END

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


class ReplyGraph:
    """持续回复工作流"""
    
    def __init__(self, file_manager=None, tts_manager=None):
        self.file_manager = file_manager
        self.tts_manager = tts_manager
        self.terminate_event = threading.Event()
        
        set_managers(file_manager, tts_manager)
        set_terminate_event(self.terminate_event)
        
        self.graph = self._build_graph()
        self._running = False
    
    def _build_graph(self) -> StateGraph:
        """构建工作流图"""
        builder = StateGraph(ReplyState)
        
        builder.add_node("extract", extract_records)
        builder.add_node("parse", parse_messages)
        builder.add_node("ownership", determine_ownership)
        builder.add_node("check_new", check_new_message)
        builder.add_node("reply", generate_reply)
        builder.add_node("send", send_message)
        builder.add_node("memory", update_memory)
        builder.add_node("wait", do_wait)
        builder.add_node("check_continue", check_continue)
        
        builder.set_entry_point("extract")
        
        builder.add_edge("extract", "parse")
        builder.add_edge("parse", "ownership")
        builder.add_edge("ownership", "check_new")
        
        builder.add_conditional_edges(
            "check_new",
            self._route_after_check,
            {
                "reply": "reply",
                "wait": "wait",
            }
        )
        
        builder.add_conditional_edges(
            "reply",
            self._route_after_reply,
            {
                "send": "send",
                "wait": "wait",
            }
        )
        
        builder.add_edge("send", "memory")
        builder.add_edge("memory", "wait")
        
        builder.add_edge("wait", "check_continue")
        
        builder.add_conditional_edges(
            "check_continue",
            self._route_continue,
            {
                "continue": "extract",
                "end": END,
            }
        )
        
        return builder.compile()
    
    def _route_after_check(self, state: ReplyState) -> Literal["reply", "wait"]:
        """检查新消息后的路由"""
        if self.terminate_event.is_set() or state.get("terminate_flag"):
            return "wait"
        if state.get("is_new_message"):
            return "reply"
        return "wait"
    
    def _route_after_reply(self, state: ReplyState) -> Literal["send", "wait"]:
        """生成回复后的路由"""
        if self.terminate_event.is_set() or state.get("terminate_flag"):
            return "wait"
        if state.get("generated_reply"):
            return "send"
        return "wait"
    
    def _route_continue(self, state: ReplyState) -> Literal["continue", "end"]:
        """继续检查后的路由"""
        if self.terminate_event.is_set() or state.get("terminate_flag"):
            return "end"
        if state.get("should_continue"):
            return "continue"
        return "end"
    
    def run(
        self, 
        app_name: str, 
        chat_object: str, 
        device_id: str = "",
        max_cycles: int = 30
    ) -> Tuple[bool, str]:
        """
        运行持续回复
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
            device_id: 设备 ID
            max_cycles: 最大循环次数
            
        Returns:
            (是否成功, 结果消息)
        """
        print(f"🔄 启动持续回复流程")
        print(f"🎯 目标：{app_name} -> {chat_object}")
        print(f"💡 点击终止按钮结束")
        
        self.terminate_event.clear()
        self._running = True
        
        initial_state = ReplyStateBuilder.create(
            app_name=app_name,
            chat_object=chat_object,
            device_id=device_id,
            max_cycles=max_cycles,
        )
        
        try:
            config = {"recursion_limit": max_cycles + 10}
            final_state = self.graph.invoke(initial_state, config=config)
            
            if self.terminate_event.is_set():
                return True, "持续回复已终止"
            else:
                return True, f"持续回复完成（达到最大循环次数 {max_cycles}）"
                
        except Exception as e:
            print(f"❌ 工作流执行异常: {e}")
            return False, f"执行失败: {str(e)}"
        finally:
            self._running = False
    
    def stop(self):
        """停止工作流"""
        self.terminate_event.set()
    
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._running
    
    def reset(self):
        """重置状态"""
        self.terminate_event.clear()
        self._running = False
