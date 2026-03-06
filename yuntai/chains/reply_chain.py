"""
回复处理链
使用 LangGraph 工作流处理回复
支持 LangChain Callbacks 追踪链执行
"""
import threading
import datetime
from typing import Tuple, Optional, List

from langchain_core.callbacks import BaseCallbackHandler

from yuntai.graphs import ReplyGraph
from yuntai.tools.message_tools import parse_messages, generate_reply
from yuntai.models import get_zhipu_client
from yuntai.callbacks import get_callback_manager


class ReplyChain:
    """回复处理链 - 使用 LangGraph，支持 Callbacks"""
    
    def __init__(
        self,
        device_id: str = "",
        file_manager=None,
        tts_manager=None
    ):
        self.device_id = device_id
        self.file_manager = file_manager
        self.tts_manager = tts_manager
        
        # 回调管理器
        self.callback_manager = get_callback_manager()
        
        self._reply_graph: Optional[ReplyGraph] = None
        self._continuous_thread: Optional[threading.Thread] = None
    
    def set_device_id(self, device_id: str):
        """设置设备 ID"""
        self.device_id = device_id
        self._reply_graph = None
    
    def _get_graph(self) -> ReplyGraph:
        """获取或创建 ReplyGraph"""
        if self._reply_graph is None:
            self._reply_graph = ReplyGraph(
                file_manager=self.file_manager,
                tts_manager=self.tts_manager
            )
        return self._reply_graph
    
    def single_reply(
        self, 
        app_name: str, 
        chat_object: str,
        callbacks: Optional[List[BaseCallbackHandler]] = None
    ) -> Tuple[bool, str]:
        """
        单次回复（支持 Callbacks）
        
        流程：
        1. PhoneAgent 提取聊天记录
        2. ChatAgent 生成回复
        3. PhoneAgent 发送回复
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
            callbacks: 自定义回调处理器列表
        
        Returns:
            (是否成功, 结果消息)
        """
        print(f"🔄 启动单次回复流程")
        print(f"🎯 目标：{app_name} -> {chat_object}")
        
        # 准备回调处理器
        all_callbacks = self._prepare_callbacks(callbacks)
        
        from yuntai.agents.phone_agent import PhoneAgent
        
        phone_agent = PhoneAgent(self.device_id)
        
        success, records = phone_agent.extract_chat_records(app_name, chat_object)
        if not success:
            return False, f"提取聊天记录失败: {records}"
        
        if self.file_manager:
            self.file_manager.save_record_to_log(1, records, app_name, chat_object)
        
        client = get_zhipu_client()
        messages = parse_messages(records, client)
        if not messages:
            return False, "未能解析到聊天记录"
        
        other_messages = []
        my_messages = []
        for msg in messages:
            content = msg.get("content", "").strip()
            if len(content) < 2:
                continue
            if msg.get("position") == "左侧有头像":
                other_messages.append(content)
            elif msg.get("position") == "右侧有头像":
                my_messages.append(content)
        
        if not other_messages:
            return False, "没有发现对方消息"
        
        latest_message = other_messages[-1]
        history_messages = other_messages[:-1] if len(other_messages) > 1 else []
        
        reply = generate_reply(latest_message, history_messages, client)
        
        if not reply or len(reply) < 2:
            return False, "未能生成有效回复"
        
        print(f"\n💬 生成回复: {reply[:50]}...")
        
        send_success, send_result = phone_agent.send_message(app_name, chat_object, reply)
        
        if send_success:
            # 保存历史记录
            if self.file_manager:
                session_data = {
                    "type": "chat_session",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "target_app": app_name,
                    "target_object": chat_object,
                    "cycle": 1,
                    "reply_generated": reply,
                    "other_messages": [latest_message],
                    "sent_success": True
                }
                self.file_manager.save_conversation_history(session_data)
            
            if self.tts_manager and getattr(self.tts_manager, 'tts_enabled', False):
                threading.Timer(0.5, lambda: self.tts_manager.speak_text_intelligently(reply)).start()
            
            return True, f"回复已发送: {reply[:50]}..."
        else:
            return False, f"回复发送失败: {send_result}"
    
    def continuous_reply(
        self, 
        app_name: str, 
        chat_object: str,
        max_cycles: int = 30
    ) -> Tuple[bool, str]:
        """
        持续回复 - 使用 LangGraph 工作流
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
            max_cycles: 最大循环次数
        
        Returns:
            (是否成功, 结果消息)
        """
        graph = self._get_graph()
        return graph.run(
            app_name=app_name,
            chat_object=chat_object,
            device_id=self.device_id,
            max_cycles=max_cycles
        )
    
    def start_continuous_reply_async(
        self, 
        app_name: str, 
        chat_object: str,
        callback=None,
        max_cycles: int = 30
    ):
        """
        异步启动持续回复
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
            callback: 完成回调
            max_cycles: 最大循环次数
        """
        def run():
            success, result = self.continuous_reply(app_name, chat_object, max_cycles)
            if callback:
                callback(success, result)
        
        self._continuous_thread = threading.Thread(target=run, daemon=True)
        self._continuous_thread.start()
    
    def stop(self):
        """停止持续回复"""
        if self._reply_graph:
            self._reply_graph.stop()
    
    def clear_messages(self):
        """清空消息列表 (LangGraph 版本自动管理)"""
        pass
    
    def is_running(self) -> bool:
        """是否正在运行"""
        if self._reply_graph:
            return self._reply_graph.is_running()
        return False
    
    def _prepare_callbacks(
        self, 
        callbacks: Optional[List[BaseCallbackHandler]] = None
    ) -> List[BaseCallbackHandler]:
        """
        准备回调处理器列表
        
        Args:
            callbacks: 用户提供的回调列表
        
        Returns:
            合并后的回调处理器列表
        """
        all_callbacks = []
        
        # 添加全局回调
        global_callbacks = self.callback_manager.get_callbacks(include_global=True)
        all_callbacks.extend(global_callbacks)
        
        # 添加用户提供的回调
        if callbacks:
            all_callbacks.extend(callbacks)
        
        return all_callbacks
