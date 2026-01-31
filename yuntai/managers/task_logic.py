"""
任务逻辑处理器 - 负责具体的任务处理逻辑（自由聊天、基础操作、单次回复等）
"""

import datetime
import threading
import traceback
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TaskLogicHandler:
    """任务逻辑处理器"""

    def __init__(self, zhipu_client, file_manager, tts_manager=None):
        """
        初始化任务逻辑处理器

        Args:
            zhipu_client: 智谱AI客户端
            file_manager: 文件管理器
            tts_manager: TTS管理器（可选）
        """
        self.zhipu_client = zhipu_client
        self.file_manager = file_manager
        self.tts_manager = tts_manager

    def handle_free_chat(self, task: str, zhipu_chat_model: str) -> str:
        """处理自由聊天"""
        try:
            # 获取当前时间信息
            from yuntai.tools.time_tool import TimeTool
            time_info = TimeTool.get_time_info()

            # 获取历史自由聊天记录
            free_chat_history = self.file_manager.get_recent_free_chats(limit=5)

            # 获取永久记忆
            forever_memory_content = self.file_manager.read_forever_memory()

            # 构建上下文
            context_prompt = ""
            if free_chat_history:
                context_prompt = "\n\n=== 历史对话（最近5条） ===\n"
                for i, chat in enumerate(free_chat_history):
                    context_prompt += f"\n{i + 1}. 用户: {chat.get('user_input', '')}\n"
                    context_prompt += f"   你: {chat.get('assistant_reply', '')}\n"

            # 构建系统提示词，添加时间信息
            system_prompt = f"""你是一个友好的助手，名字叫'小芸'（不用刻意用"小芸："放在对话开头做标注），性别为女，请用自然又俏皮可爱的方式回应用户。

你有记忆功能，可以记住之前的对话内容。以下是你们之前的对话记录（最近5条）：
{context_prompt}
{forever_memory_content}

{time_info}

**重要**：
- 如果用户询问时间，请使用上述当前时间信息回答
- 不要编造时间，要准确使用提供的时间信息
- 回答时可以自然地提及时间，如"现在的时间是14:30"或"今天是2026年1月31日"
- 如果用户询问具体时间，请直接返回准确时间，不要添加不必要的对话内容
- 如果用户未提及时间相关问题不要强行将时间添加到对话中

请基于以上历史对话、时间信息和用户当前的问题，生成一个连贯、友好的回复。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ]

            response = self.zhipu_client.chat.completions.create(
                model=zhipu_chat_model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            reply = response.choices[0].message.content.strip()

            # 语音播报回复内容（使用智能合成）
            if self.tts_manager and self.tts_manager.tts_enabled and len(reply) > 5:
                def speak_reply():
                    try:
                        # 使用智能语音合成
                        self.tts_manager.speak_text_intelligently(reply)
                    except Exception as e:
                        print(f"❌ 语音播报失败: {e}")

                # 异步播报，延迟0.5秒避免阻塞
                threading.Timer(0.5, speak_reply).start()

            # 保存到对话历史
            session_data = {
                "type": "free_chat",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_input": task,
                "assistant_reply": reply,
                "model_used": zhipu_chat_model,
                "used_forever_memory": forever_memory_content != ""
            }
            self.file_manager.save_conversation_history(session_data)

            return reply

        except Exception as e:
            error_msg = f"❌ 聊天失败：{str(e)}"
            print(error_msg)
            traceback.print_exc()
            return error_msg

    def handle_basic_operation(self, task: str, args, device_id: str, agent_executor) -> str:
        """处理基础操作"""
        print(f"📱 执行：{task}\n")

        try:
            # 获取执行结果
            result = agent_executor.phone_agent_exec(task, args, "basic", device_id)

            # 提取详细信息
            detailed_info = ""

            # 处理不同类型的返回值
            if isinstance(result, str):
                detailed_info = result
            elif isinstance(result, (list, tuple)):
                # 从列表/元组中提取字符串
                for item in result:
                    if isinstance(item, str) and item.strip():
                        detailed_info = item
                        break

            # 简化详细信息的长度
            if detailed_info:
                # 取第一句话或前100个字符
                if len(detailed_info) > 100:
                    short_info = detailed_info[:100] + "..."
                else:
                    short_info = detailed_info
            else:
                short_info = task

            # 检查执行结果
            if ("失败" in str(result) or "错误" in str(result) or
                    "失败" in short_info or "错误" in short_info):
                return_msg = f"❌ 操作失败"
            else:
                return_msg = f"✅ 操作完成"

                # TTS语音播报
                if self.tts_manager and self.tts_manager.tts_enabled and short_info and len(short_info) > 2:
                    def speak_result():
                        try:
                            # 清理消息用于TTS
                            cleaned_msg = self.tts_manager.text_processor.clean_text_for_tts(short_info)
                            # 使用智能语音合成
                            self.tts_manager.speak_text_intelligently(cleaned_msg)
                        except Exception as e:
                            print(f"❌ 语音播报失败: {e}")

                    # 异步播报
                    threading.Thread(target=speak_result, daemon=True).start()

            return return_msg

        except Exception as e:
            error_msg = f"❌ 操作失败：{str(e)}"
            print(error_msg)
            traceback.print_exc()
            return error_msg

    def handle_single_reply(self, task: str, args, target_app: str, target_object: str,
                            device_id: str, zhipu_chat_model: str) -> str:
        """处理单次回复"""
        print(f"\n🔄 启动单次回复流程")
        print(f"\n🎯 目标：{target_app} -> {target_object}\n")
        print()

        try:
            # 使用TerminableContinuousReplyManager
            from ..agent_core import TerminableContinuousReplyManager
            manager = TerminableContinuousReplyManager(args, target_app, target_object, device_id,
                                                       self.zhipu_client, self.file_manager)

            # 1. 获取聊天记录
            current_record = manager.extract_chat_records()

            # 2. 保存原始记录到文件
            filename = self.file_manager.save_record_to_log(1, current_record, target_app, target_object)

            # 3. 解析消息
            messages = manager.parse_messages_simple(current_record)
            if messages:
                # 4. 判断消息归属
                other_messages, my_messages = manager.determine_message_ownership_fixed(messages)

                # 5. 检查是否有对方消息
                if other_messages:
                    # 只取最新的对方消息
                    latest_message = other_messages[-1]

                    # 6. 生成回复
                    # 历史消息：除了最新消息之外的其他消息
                    history_messages = other_messages[:-1] if len(other_messages) > 1 else []

                    reply_message = manager.generate_reply_for_latest_message(latest_message, history_messages)

                    if reply_message and len(reply_message) > 2:
                        # 7. 发送回复
                        success = manager.send_reply_message_fixed(reply_message)

                        if success:
                            # 保存到对话历史
                            session_data = {
                                "type": "chat_session",
                                "session_id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "target_app": target_app,
                                "target_object": target_object,
                                "cycle": 1,
                                "record_file": filename,
                                "reply_generated": reply_message,
                                "other_messages": [latest_message],
                                "sent_success": True
                            }
                            self.file_manager.save_conversation_history(session_data)

                            # 语音播报回复内容
                            if self.tts_manager and self.tts_manager.tts_enabled and len(reply_message) > 5:
                                def speak_reply():
                                    try:
                                        # 使用智能语音合成
                                        self.tts_manager.speak_text_intelligently(reply_message)
                                    except Exception as e:
                                        print(f"❌ 语音播报失败: {e}")

                                threading.Timer(0.5, speak_reply).start()

                            print(f"\n✅ 回复已发送：{reply_message[:50]}...\n")
                            return f"\n✅ 回复已发送：{reply_message[:50]}..."
                        else:
                            print(f"\n❌ 回复发送失败\n")
                            return f"\n❌ 回复发送失败"
                    else:
                        return f"⚠️  未能生成有效回复"
                else:
                    return f"⚠️  没有发现对方消息"
            else:
                return f"⚠️  未能解析到聊天记录"

        except Exception as e:
            print(f"❌ 单次回复失败: {e}\n")
            traceback.print_exc()
            return f"❌ 单次回复失败: {str(e)}"

    def handle_continuous_reply(self, args, target_app: str, target_object: str,
                               device_id: str, terminate_flag=None) -> str:
        """处理持续回复"""
        # 检查设备连接
        if not device_id:
            print(f"❌ 设备未连接\n")
            return "❌ 设备未连接"

        # 使用TerminableContinuousReplyManager
        try:
            from ..agent_core import TerminableContinuousReplyManager
            manager = TerminableContinuousReplyManager(
                args, target_app, target_object, device_id,
                self.zhipu_client, self.file_manager,
                terminate_flag=terminate_flag
            )

            # 确保manager有所有必要的方法
            self._ensure_manager_methods(manager)

            success = manager.run_continuous_loop()

            if success:
                return f"✅ 持续回复完成"
            else:
                return f"⏹️  持续回复已终止"
        except Exception as e:
            print(f"❌ 创建持续回复管理器失败: {e}\n")
            import traceback
            traceback.print_exc()
            return f"❌ 持续回复失败: {str(e)}"

    def handle_complex_operation(self, task: str, args, device_id: str, agent_executor) -> str:
        """处理复杂操作"""
        print(f"⚙️  执行复杂操作：{task}\n")

        try:
            result, _ = agent_executor.phone_agent_exec(task, args, "complex", device_id)

            # 确保结果有换行符
            if result:
                result = result.strip()
                if not result.startswith('\n'):
                    result = '\n' + result
                if not result.endswith('\n'):
                    result = result + '\n'

            # 检查执行结果
            if "失败" in result or "错误" in result:
                return_msg = f"❌ 操作失败：{result}..."
            else:
                # 提取成功消息部分
                success_msg = result.strip()
                # 移除开头的 ✅ 操作完成： 前缀
                if success_msg.startswith("✅ 操作完成："):
                    success_msg = success_msg.replace("✅ 操作完成：", "")

                return_msg = f"✅ 操作完成：{result}..."

                # TTS语音播报回复内容（与自由聊天和单次回复保持一致）
                if self.tts_manager and self.tts_manager.tts_enabled and len(success_msg) > 5:
                    def speak_result():
                        # 检查是否有参考音频和文本
                        ref_audio = self.tts_manager.database_manager.get_current_model("audio")
                        ref_text = self.tts_manager.database_manager.get_current_model("text")

                        if ref_audio and ref_text:
                            # 清理消息用于TTS（使用与自由聊天相同的清理方法）
                            cleaned_msg = self.tts_manager.text_processor.clean_text_for_tts(success_msg)
                            self.tts_manager.engine.synthesize_text(
                                cleaned_msg,
                                ref_audio,
                                ref_text,
                                auto_play=True
                            )
                        else:
                            print("⚠️  无法语音播报：未选择参考音频或文本")

                    # 异步播报（与自由聊天和单次回复保持一致）
                    threading.Thread(target=speak_result, daemon=True).start()

            return return_msg

        except Exception as e:
            error_msg = f"❌ 操作失败：{str(e)}"
            print(error_msg)
            return error_msg

    def _ensure_manager_methods(self, manager):
        """确保管理器有所有必要的方法"""
        # 检查并添加缺失的方法
        if not hasattr(manager, 'parse_messages_simple'):
            print("⚠️  添加缺失的parse_messages_simple方法到管理器")

            def parse_messages_simple(record):
                """解析消息的简化方法"""
                messages = []
                if not record:
                    return messages

                # 这里是简化的解析逻辑
                # 实际应该根据你的聊天记录格式来解析
                lines = record.split('\n')
                for line in lines:
                    line = line.strip()
                    if '内容：' in line:
                        messages.append(line)

                return messages

            manager.parse_messages_simple = parse_messages_simple

        if not hasattr(manager, 'determine_message_ownership_fixed'):
            print("⚠️  警告：管理器缺少determine_message_ownership_fixed方法")
