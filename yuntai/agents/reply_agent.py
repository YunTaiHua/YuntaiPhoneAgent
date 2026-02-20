"""
回复 Agent
协调 ZHIPU_MODEL 和 ZHIPU_CHAT_MODEL 完成回复任务
"""
import time
import threading
import datetime
from typing import Dict, Any, Optional, List, Tuple

from zhipuai import ZhipuAI

from yuntai.models import get_zhipu_client
from yuntai.agents.phone_agent import PhoneAgent, PhoneAgentWrapper
from yuntai.tools.message_tools import (
    parse_messages,
    determine_message_ownership,
    generate_reply,
    check_new_messages,
    is_message_similar,
)
from yuntai.core.config import MAX_CYCLE_TIMES, WAIT_INTERVAL
from yuntai.prompts import REPLY_GENERATION_PROMPT


class ReplyAgent:
    """回复 Agent"""
    
    def __init__(
        self,
        device_id: str = "",
        zhipu_client: Optional[ZhipuAI] = None,
        file_manager=None,
        tts_manager=None
    ):
        self.device_id = device_id
        self.zhipu_client = zhipu_client or get_zhipu_client()
        self.file_manager = file_manager
        self.tts_manager = tts_manager
        
        self.phone_agent = PhoneAgent(device_id)
        
        self.other_messages_list: List[str] = []
        self.my_messages_list: List[str] = []
        
        self.terminate_flag = threading.Event()
        self.is_running = False
    
    def set_device_id(self, device_id: str):
        """设置设备 ID"""
        self.device_id = device_id
        self.phone_agent.set_device_id(device_id)
    
    def set_terminate_flag(self):
        """设置终止标志"""
        self.terminate_flag.set()
        self.is_running = False
    
    def clear_terminate_flag(self):
        """清除终止标志"""
        self.terminate_flag.clear()
    
    def clear_message_lists(self):
        """清空消息列表"""
        self.other_messages_list = []
        self.my_messages_list = []
    
    def single_reply(
        self, 
        app_name: str, 
        chat_object: str
    ) -> Tuple[bool, str]:
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
        print(f"🔄 启动单次回复流程")
        print(f"🎯 目标：{app_name} -> {chat_object}")
        
        success, records = self.phone_agent.extract_chat_records(app_name, chat_object)
        if not success:
            return False, f"提取聊天记录失败: {records}"
        
        if self.file_manager:
            self.file_manager.save_record_to_log(1, records, app_name, chat_object)
        
        messages = parse_messages(records, self.zhipu_client)
        if not messages:
            return False, "未能解析到聊天记录"
        
        other_messages, my_messages = determine_message_ownership(
            messages, self.my_messages_list, self.other_messages_list
        )
        
        if not other_messages:
            return False, "没有发现对方消息"
        
        latest_message = other_messages[-1]
        history_messages = other_messages[:-1] if len(other_messages) > 1 else []
        
        reply = generate_reply(
            latest_message,
            history_messages,
            self.zhipu_client
        )
        
        if not reply or len(reply) < 2:
            return False, "未能生成有效回复"
        
        print(f"\n💬 生成回复: {reply[:50]}...")
        
        send_success, send_result = self.phone_agent.send_message(app_name, chat_object, reply)
        
        if send_success:
            self.my_messages_list.append(reply)
            self.other_messages_list.extend(other_messages)
            
            if self.file_manager:
                import datetime
                session_data = {
                    "type": "chat_session",
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "target_app": app_name,
                    "target_object": chat_object,
                    "reply_generated": reply,
                    "other_messages": [latest_message],
                    "sent_success": True
                }
                self.file_manager.save_conversation_history(session_data)
            
            if self.tts_manager and self.tts_manager.tts_enabled:
                threading.Timer(0.5, lambda: self.tts_manager.speak_text_intelligently(reply)).start()
            
            return True, f"回复已发送: {reply[:50]}..."
        else:
            return False, f"回复发送失败: {send_result}"
    
    def continuous_reply(
        self, 
        app_name: str, 
        chat_object: str,
        max_cycles: int = MAX_CYCLE_TIMES
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
        print(f"🔄 启动持续回复流程")
        print(f"🎯 目标：{app_name} -> {chat_object}")
        print(f"💡 点击终止按钮结束")
        
        self.clear_message_lists()
        self.clear_terminate_flag()
        self.is_running = True
        
        cycle = 0
        previous_latest_message = None
        last_sent_reply = None
        
        while cycle < max_cycles:
            if self.terminate_flag.is_set():
                print("🛑 检测到终止信号，正在退出...")
                break
            
            cycle += 1
            print(f"\n{'='*60}")
            print(f"📊 循环轮次 {cycle}/{max_cycles}")
            print(f"{'='*60}")
            
            if self.terminate_flag.is_set():
                break
                
            success, records = self.phone_agent.extract_chat_records(app_name, chat_object)
            
            if self.terminate_flag.is_set():
                break
            
            if not success:
                print(f"❌ 提取聊天记录失败: {records}")
                for _ in range(int(WAIT_INTERVAL)):
                    if self.terminate_flag.is_set():
                        break
                    time.sleep(1)
                continue
            
            if self.file_manager:
                self.file_manager.save_record_to_log(cycle, records, app_name, chat_object)
            
            messages = parse_messages(records, self.zhipu_client)
            if not messages:
                print("⏭️ 没有解析到消息")
                for _ in range(int(WAIT_INTERVAL)):
                    if self.terminate_flag.is_set():
                        break
                    time.sleep(1)
                continue
            
            other_messages, my_messages = determine_message_ownership(
                messages, self.my_messages_list, self.other_messages_list
            )
            
            print(f"📋 对方消息 {len(other_messages)} 条，我方消息 {len(my_messages)} 条")
            
            if other_messages:
                latest_message = other_messages[-1]
                
                is_new = True
                if previous_latest_message:
                    is_new = not is_message_similar(previous_latest_message, latest_message, 0.6)
                
                if cycle == 1:
                    is_new = True
                
                if last_sent_reply:
                    if is_message_similar(latest_message, last_sent_reply, 0.7):
                        is_new = False
                
                if is_new:
                    print(f"💬 发现新消息: {latest_message[:50]}...")
                    
                    if self.terminate_flag.is_set():
                        break
                    
                    reply = generate_reply(
                        latest_message,
                        other_messages[:-1],
                        self.zhipu_client
                    )
                    
                    if reply and len(reply) > 2:
                        if self.terminate_flag.is_set():
                            break
                        
                        if last_sent_reply and is_message_similar(reply, last_sent_reply, 0.7):
                            print("⏭️ 回复与上次相似，跳过发送")
                        else:
                            print(f"📤 准备发送回复: {reply[:50]}...")
                            
                            if self.terminate_flag.is_set():
                                break
                            
                            send_success, _ = self.phone_agent.send_message(app_name, chat_object, reply)
                            
                            if send_success:
                                self.my_messages_list.append(reply)
                                last_sent_reply = reply
                                self.other_messages_list.extend(other_messages)
                                
                                if self.file_manager:
                                    session_data = {
                                        "type": "chat_session",
                                        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                        "target_app": app_name,
                                        "target_object": chat_object,
                                        "cycle": cycle,
                                        "reply_generated": reply,
                                        "other_messages": [latest_message],
                                        "sent_success": True
                                    }
                                    self.file_manager.save_conversation_history(session_data)
                                
                                print("✅ 回复已发送")
                                
                                if self.tts_manager and self.tts_manager.tts_enabled:
                                    threading.Timer(0.5, lambda: self.tts_manager.speak_text_intelligently(reply)).start()
                            else:
                                print("❌ 回复发送失败")
                    else:
                        print("⏭️ 未能生成有效回复")
                    
                    previous_latest_message = latest_message
                else:
                    print("⏭️ 没有新消息")
            else:
                print("⏭️ 没有对方消息")
            
            for msg in my_messages:
                if not any(is_message_similar(msg, m, 0.6) for m in self.my_messages_list):
                    self.my_messages_list.append(msg)
            
            if len(self.other_messages_list) > 50:
                self.other_messages_list = self.other_messages_list[-50:]
            if len(self.my_messages_list) > 50:
                self.my_messages_list = self.my_messages_list[-50:]
            
            if self.terminate_flag.is_set():
                break
            
            print(f"⏳ 等待 {WAIT_INTERVAL} 秒...")
            for _ in range(int(WAIT_INTERVAL)):
                if self.terminate_flag.is_set():
                    break
                time.sleep(1)
        
        self.is_running = False
        
        if self.terminate_flag.is_set():
            return True, "持续回复已终止"
        else:
            return True, f"持续回复完成（达到最大循环次数 {max_cycles}）"
