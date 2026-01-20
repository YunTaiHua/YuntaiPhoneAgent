"""
智能代理核心模块 - 重构版（完整修复）
包含任务处理、消息回复等核心业务逻辑
"""

import datetime
import time
import re
import threading
import logging
from typing import Dict, Any, List, Tuple, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# 常量定义
SIMILARITY_THRESHOLD = 0.6
MAX_MESSAGE_LIST_LENGTH = 50
from yuntai.reply_manager import SmartContinuousReplyManager


class TerminableContinuousReplyManager(SmartContinuousReplyManager):
    """支持终止的持续回复管理器（完整修复版）"""

    def __init__(self, *args, terminate_flag=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.terminate_flag = terminate_flag if terminate_flag else threading.Event()
        self.should_terminate = False

        # 初始化消息列表
        self.other_messages_list = []  # 对方消息列表
        self.my_messages_list = []  # 我方消息列表

        # 第一轮标志
        self.is_first_round = True

    def set_terminate_flag(self) -> None:
        """设置终止标志"""
        self.terminate_flag.set()
        self.should_terminate = True
        logger.info("终止标志已设置")

    def check_termination(self):
        """检查是否应该终止"""
        if hasattr(self, 'terminate_flag') and self.terminate_flag:
            return self.terminate_flag.is_set() or self.should_terminate
        return self.should_terminate

    def is_message_similar(self, msg1: str, msg2: str, threshold: float = 0.6) -> bool:
        """判断两条消息是否相似（使用 difflib.SequenceMatcher 提高效率）"""
        if not msg1 or not msg2:
            return False

        # 清理消息：去除标点、空格、表情符号等
        def clean_text(text):
            if not text:
                return ""
            # 去除标点符号、空格和常见表情符号
            text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
            # 转换为小写（如果是英文）
            return text.lower()

        # 清理消息
        clean_msg1 = clean_text(msg1)
        clean_msg2 = clean_text(msg2)

        # 如果清理后为空，使用原始消息进行简单比较
        if not clean_msg1 or not clean_msg2:
            return msg1 == msg2 or msg1 in msg2 or msg2 in msg1

        # 使用 difflib.SequenceMatcher 计算相似度
        similarity = SequenceMatcher(None, clean_msg1, clean_msg2).ratio()

        return similarity >= threshold

    def determine_message_ownership_fixed(self, messages: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """修复的消息归属判断方法"""
        other_messages = []  # 对方消息
        my_messages = []  # 我方消息

        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content", "").strip()
                position = msg.get("position", "").lower()
                color = msg.get("color", "").lower()
            else:
                content = str(msg).strip()
                position = ""
                color = ""

            if not content or len(content) < 2:
                continue

            # 1. 首先检查是否是我方已发送的消息（使用相似度比较）
            is_my_message = False
            for my_msg in self.my_messages_list:
                if self.is_message_similar(content, my_msg, threshold=SIMILARITY_THRESHOLD):
                    is_my_message = True
                    my_messages.append(content)
                    break

            if is_my_message:
                continue

            # 2. 然后检查是否是对方案已记录的消息
            is_other_message = False
            for other_msg in self.other_messages_list:
                if self.is_message_similar(content, other_msg, threshold=SIMILARITY_THRESHOLD):
                    is_other_message = True
                    other_messages.append(content)
                    break

            if is_other_message:
                continue

            # 3. 新消息：以头像位置为主要判断依据
            # 左侧有头像 -> 对方消息
            if any(keyword in position for keyword in ["左侧", "左边", "左"]) or "left" in position:
                other_messages.append(content)
                self.other_messages_list.append(content)
            # 右侧有头像 -> 我方消息
            elif any(keyword in position for keyword in ["右侧", "右边", "右"]) or "right" in position:
                my_messages.append(content)
                self.my_messages_list.append(content)
            else:
                # 头像位置不明确，使用颜色作为辅助判断
                if "白色" in color or "浅色" in color or "white" in color:
                    other_messages.append(content)
                    self.other_messages_list.append(content)
                elif any(col in color for col in ["红色", "粉色", "蓝色", "绿色", "紫色", "深色", "dark"]):
                    my_messages.append(content)
                    self.my_messages_list.append(content)

        # 限制列表长度，避免无限增长
        if len(self.other_messages_list) > MAX_MESSAGE_LIST_LENGTH:
            self.other_messages_list = self.other_messages_list[-MAX_MESSAGE_LIST_LENGTH:]
        if len(self.my_messages_list) > MAX_MESSAGE_LIST_LENGTH:
            self.my_messages_list = self.my_messages_list[-MAX_MESSAGE_LIST_LENGTH:]

        return other_messages, my_messages

    def send_reply_message_fixed(self, message):
        """发送回复消息并记录到我方消息列表"""
        try:
            if not message or len(message) < 2:
                return False

            message = message.strip()

            # 调用父类发送消息
            success = self.send_reply_message(message)

            if success:
                # 发送成功后，将消息加入我方消息列表
                self.my_messages_list.append(message)

            return success

        except Exception as e:
            print(f"❌ 发送消息失败: {str(e)}")
            return False

    def generate_reply_for_latest_message(self, latest_message, history_messages=None):
        """生成回复消息 - 确保输出思考过程"""
        print("=" * 50)
        print(f"\n💭 思考过程:")
        print("=" * 50)
        print(f"分析对方消息: {latest_message[:100]}...")

        # 构建历史上下文
        context = ""
        if history_messages:
            context = "\n历史对话：\n"
            for i, msg in enumerate(history_messages[-3:]):  # 只取最近3条历史
                context += f"{i + 1}. {msg[:50]}...\n"



        # 调用父类方法生成回复
        reply = super().generate_reply_for_latest_message(latest_message, history_messages)

        print("=" * 50)
        print(f"生成的回复: {reply[:100]}...")

        return reply

    def run_continuous_loop(self):
        """修复的持续回复循环 - 增加终止检查频率"""
        # 从父类获取配置参数
        max_cycle_times = getattr(self, 'max_cycle_times', 30)
        wait_interval = getattr(self, 'wait_interval', 2)

        # 清空消息列表
        self.other_messages_list = []
        self.my_messages_list = []

        cycle = 1
        previous_latest_message = None

        logger.info(f"启动持续回复循环（可终止）")
        logger.info(f"目标：{self.target_app} -> {self.target_object}")
        logger.info(f"最大循环次数：{max_cycle_times}，等待间隔：{wait_interval}秒")

        while cycle <= max_cycle_times:
            # 检查终止标志（在每次循环开始时检查）
            if self.check_termination():
                print(f"\n🛑 检测到终止信号，停止持续回复（第{cycle}轮）")
                return False

            print(f"\n🔄 第{cycle}/{max_cycle_times}轮处理...")

            try:
                # 提取聊天记录
                current_record = self.extract_chat_records()

                # 检查终止标志
                if self.check_termination():
                    print(f"\n🛑 检测到终止信号，停止持续回复")
                    return False

                # 保存记录到文件
                filename = self.file_manager.save_record_to_log(cycle, current_record, self.target_app,
                                                                self.target_object)

                # 解析消息
                messages = self.parse_messages_simple(current_record)
                if not messages:
                    print(f"⏭️  没有解析到消息，等待{wait_interval}秒后继续")
                    # 在等待期间也检查终止
                    for i in range(wait_interval * 2):  # 每0.5秒检查一次
                        if self.check_termination():
                            print(f"\n🛑 检测到终止信号，停止持续回复")
                            return False
                        time.sleep(0.5)
                    cycle += 1
                    continue

                print(f"\n📊 解析到 {len(messages)} 条消息")

                # 判断消息归属
                other_messages, my_messages = self.determine_message_ownership_fixed(messages)

                print(f"\n📋 消息归属：对方消息 {len(other_messages)} 条，我方消息 {len(my_messages)} 条")

                # 只关注最新的对方消息
                if other_messages:
                    latest_other_message = other_messages[-1]

                    # 检查是否是新消息
                    is_new_message = True
                    if previous_latest_message:
                        if self.is_message_similar(previous_latest_message, latest_other_message, threshold=SIMILARITY_THRESHOLD):
                            is_new_message = False
                            print(f"\n🔁 消息相似，不是新消息")

                    # 第一轮总是回复最新的对方消息
                    if cycle == 1:
                        is_new_message = True
                        print(f"\n🚀 第一轮，强制视为新消息")

                    if is_new_message:
                        # 检查终止标志
                        if self.check_termination():
                            print(f"\n🛑 检测到终止信号，停止持续回复")
                            return False

                        print(f"💬 发现新消息: {latest_other_message[:50]}...")

                        # 生成回复
                        reply_message = self.generate_reply_for_latest_message(latest_other_message,
                                                                               other_messages[:-1])

                        if reply_message and len(reply_message) > 2:
                            # 检查终止标志
                            if self.check_termination():
                                print(f"\n🛑 检测到终止信号，停止持续回复")
                                return False

                            print(f"📤 准备发送回复: {reply_message[:50]}...")

                            # 发送回复
                            success = self.send_reply_message_fixed(reply_message)

                            if success:
                                # 保存到对话历史
                                session_data = {
                                    "type": "chat_session",
                                    "session_id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "target_app": self.target_app,
                                    "target_object": self.target_object,
                                    "cycle": cycle,
                                    "record_file": filename,
                                    "reply_generated": reply_message,
                                    "other_messages": [latest_other_message],
                                    "sent_success": True
                                }
                                self.file_manager.save_conversation_history(session_data)

                                print(f"✅ 回复已发送")
                            else:
                                print(f"❌ 回复发送失败")

                        # 更新最新消息记录
                        previous_latest_message = latest_other_message
                    else:
                        print(f"\n⏭️  没有新消息，跳过回复")
                else:
                    print(f"\n⏭️  没有对方消息，跳过回复")

                # 检查终止标志
                if self.check_termination():
                    print(f"\n🛑 检测到终止信号，停止持续回复")
                    return False

                # 等待期间也检查终止
                print(f"⏳ 等待{wait_interval}秒...")
                for i in range(wait_interval * 2):  # 每0.5秒检查一次
                    if self.check_termination():
                        print(f"\n🛑 检测到终止信号，停止持续回复")
                        return False
                    time.sleep(0.5)

                cycle += 1

            except Exception as e:
                print(f"❌ 第{cycle}轮处理出错: {str(e)}")
                import traceback
                traceback.print_exc()
                # 出错后等待一段时间继续
                time.sleep(wait_interval)
                cycle += 1

        print(f"\n✅ 持续回复完成（达到最大循环次数）")
        return True

    # 添加一个兼容方法，以防父类没有这个方法
    def parse_messages_simple(self, record):
        """解析消息的简化方法"""
        try:
            # 首先尝试调用父类方法
            return super().parse_messages_simple(record)
        except AttributeError:
            # 如果父类没有这个方法，使用简化实现
            print("⚠️  父类没有parse_messages_simple方法，使用简化解析")

            messages = []
            if not record:
                return messages

            # 尝试从记录中提取消息
            lines = record.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 简单的消息提取逻辑
                if '内容：' in line and '位置：' in line:
                    # 提取消息内容
                    content_start = line.find('内容：') + 3
                    position_start = line.find('位置：')

                    if content_start < position_start:
                        content = line[content_start:position_start].strip()
                        position_part = line[position_start:].strip()

                        # 提取位置信息
                        position = ""
                        if '左侧' in position_part:
                            position = "左侧"
                        elif '右侧' in position_part:
                            position = "右侧"

                        # 提取颜色信息
                        color = ""
                        if '颜色：' in position_part:
                            color_start = position_part.find('颜色：') + 3
                            color = position_part[color_start:].strip().split('，')[
                                0] if '，' in position_part else position_part[color_start:].strip()

                        messages.append({
                            "content": content,
                            "position": position,
                            "color": color
                        })

            return messages