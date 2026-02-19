"""
回复处理链
处理单次和持续回复流程
"""
import threading
from typing import Dict, Any, Optional, Tuple

from yuntai.agents import ReplyAgent


class ReplyChain:
    """回复处理链"""
    
    def __init__(
        self,
        device_id: str = "",
        file_manager=None,
        tts_manager=None
    ):
        self.reply_agent = ReplyAgent(
            device_id=device_id,
            file_manager=file_manager,
            tts_manager=tts_manager
        )
    
    def set_device_id(self, device_id: str):
        """设置设备 ID"""
        self.reply_agent.set_device_id(device_id)
    
    def single_reply(self, app_name: str, chat_object: str) -> Tuple[bool, str]:
        """
        单次回复
        
        流程：
        1. PhoneAgent 提取聊天记录
        2. ChatAgent 生成回复
        3. PhoneAgent 发送回复
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
        
        Returns:
            (是否成功, 结果消息)
        """
        return self.reply_agent.single_reply(app_name, chat_object)
    
    def continuous_reply(
        self, 
        app_name: str, 
        chat_object: str,
        max_cycles: int = 30
    ) -> Tuple[bool, str]:
        """
        持续回复
        
        流程：
        循环：
        1. PhoneAgent 提取聊天记录
        2. ChatAgent 生成回复
        3. PhoneAgent 发送回复
        4. PhoneAgent 提取聊天记录
        5. ChatAgent 判断是否有新消息
        6. 有新消息：生成回复并发送
        7. 无新消息：继续提取
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
            max_cycles: 最大循环次数
        
        Returns:
            (是否成功, 结果消息)
        """
        return self.reply_agent.continuous_reply(app_name, chat_object, max_cycles)
    
    def start_continuous_reply_async(
        self, 
        app_name: str, 
        chat_object: str,
        callback=None
    ):
        """
        异步启动持续回复
        
        Args:
            app_name: APP 名称
            chat_object: 聊天对象
            callback: 完成回调
        """
        def run():
            success, result = self.reply_agent.continuous_reply(app_name, chat_object)
            if callback:
                callback(success, result)
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def stop(self):
        """停止持续回复"""
        self.reply_agent.set_terminate_flag()
    
    def clear_messages(self):
        """清空消息列表"""
        self.reply_agent.clear_message_lists()
    
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.reply_agent.is_running
