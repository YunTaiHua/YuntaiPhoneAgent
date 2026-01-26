#!/usr/bin/env python3
"""
回复管理模块 - 最终修复版
"""
import re
import time
import threading
import datetime
import json
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher
from zhipuai import ZhipuAI
from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig
from phone_agent.agent import AgentConfig
from pydantic import BaseModel, Field, ValidationError

# 导入配置
from yuntai.config import (
    MAX_CYCLE_TIMES, WAIT_INTERVAL, ZHIPU_CLIENT,ZHIPU_CHAT_MODEL
)
from yuntai.file_manager import FileManager


class ChatMessage(BaseModel):
    content: str = Field(description="消息的具体内容，完整无遗漏")
    position: str = Field(description="头像位置：左侧有头像、右侧有头像、未知")
    color: str = Field(description="气泡颜色：白色、红色、蓝色、绿色、粉色、紫色、黑色、灰色、橙色、黄色、未知")


class ChatMessages(BaseModel):
    messages: List[ChatMessage] = Field(description="从聊天记录中提取的所有有效消息列表")


class SmartContinuousReplyManager:
    def __init__(self, args, target_app: str, target_object: str, device_id: str, zhipu_client: ZhipuAI,
                 file_manager: FileManager):
        self.args = args
        self.target_app = target_app
        self.target_object = target_object
        self.device_id = device_id
        self.zhipu_client = zhipu_client
        self.file_manager = file_manager
        self.previous_record = None
        self.auto_reply = True
        self.terminate_requested = False
        self.cycle_count = 0
        self.session_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.other_messages_list = []
        self.my_messages_list = []

        # 修复Prompt格式（转义大括号）
        self.extract_prompt = """
        你是专业的聊天记录解析助手，必须严格按以下规则提取信息：
        ### 核心规则（优先级最高）：
        1. 头像位置判断：
           - 右侧有头像 = 消息气泡在屏幕右侧（我方发送的消息）
           - 左侧有头像 = 消息气泡在屏幕左侧（对方发送的消息）
           - 从描述中找关键词："右侧有头像"、"红色气泡"、"粉色气泡" → 一律标为「右侧有头像」
        2. 气泡颜色判断：
           - 红色/粉色/绿色气泡 = 我方的消息，颜色填「红色」或「粉色」
           - 白色/灰色气泡 = 对方的消息，颜色填「白色」
           - 从描述中找关键词："红色气泡"→颜色填「红色」，"粉色气泡"→填「粉色」，"绿色气泡"→填「绿色」，无描述才填「未知」
        3. 消息内容：完整保留原文，包括标点、emoji、语气词（如~、💪）

        ### 输入文本（聊天记录描述）：
        {text}

        ### 强制输出格式（必须是纯JSON，不要加任何额外文字、代码块标记）：
        {{
          "messages": [
            {{"content": "消息内容1", "position": "右侧有头像", "color": "红色"}},
            {{"content": "消息内容2", "position": "左侧有头像", "color": "白色"}}
          ]
        }}

        ### 错误示例（禁止出现）：
        - 不要输出"```json"或"```"
        - 不要加解释性文字（如"以下是提取结果："）
        - 不要遗漏position/color字段
        - 不要把"右侧有头像"写成"右"或"右侧"，必须严格按指定值输出
        """

    def parse_messages_simple(self, record: str) -> List[Dict[str, str]]:
        """
        纯ZHIPU_CHAT_MODEL智能提取：适配任意格式的自然语言聊天记录描述
        核心：让ZHIPU_CHAT_MODEL直接理解文本，提取消息+位置+颜色，无需正则
        """
        if not record or len(record.strip()) < 10:
            print(f"\n⚠️  聊天记录为空/过短")
            return []

        # ========== 核心：给ZHIPU_CHAT_MODEL的超精准指令 ==========
        prompt_text = f"""
    你的唯一任务是：从以下文本中提取聊天消息，并按要求输出JSON。
    严格遵守以下规则（违反任何一条都会导致解析失败）：
    1. 消息提取规则：
       - 只提取实际的聊天内容（如"早上就有两节"），忽略时间戳、思考过程、性能指标等无关内容
       - 不遗漏任何一条可见的聊天消息，不重复提取
       - 消息内容完整保留（包括标点、emoji、语气词）
    2. 位置/颜色判断规则：
       - 右侧有头像 = 我方发送的消息（通常是红色/粉色/绿色气泡）
       - 左侧有头像 = 对方发送的消息（通常是白色气泡）
       - 必须从文本中找依据（如"红色气泡，右侧有头像"→右侧+红色；"白色气泡，左侧有头像"→左侧+白色）
       - 无明确依据时，位置/颜色填"未知"
       - 位置和颜色判断矛盾时，以位置为主
    3. 输出格式（必须是纯JSON，无任何额外内容、代码块、解释文字）：
    {{
      "messages": [
        {{"content": "消息内容1", "position": "左侧有头像", "color": "白色"}},
        {{"content": "消息内容2", "position": "右侧有头像", "color": "红色"}}
      ]
    }}

    需要处理的文本：
    {record[:2000]}  # 限制长度，避免ZHIPU_CHAT_MODEL上下文超限
    """

        try:
            # ========== 调用ZHIPU_CHAT_MODEL（强制精准输出） ==========
            response = self.zhipu_client.chat.completions.create(
                model=ZHIPU_CHAT_MODEL,     
                messages=[
                    {"role": "system", "content": "你必须只输出符合要求的JSON，不要加任何额外文字！"},
                    {"role": "user", "content": prompt_text}
                ],
                temperature=0.0,  # 0温度=绝对精准，无随机性
                max_tokens=2000,
                response_format={"type": "json_object"}  # 强制JSON格式（ZHIPU_CHAT_MODEL支持）
            )

            # ========== 解析ZHIPU_CHAT_MODEL返回结果（容错处理） ==========
            resp_content = response.choices[0].message.content.strip()
            # 容错：去掉可能的代码块标记（防止ZHIPU_CHAT_MODEL违规输出）
            if resp_content.startswith("```"):
                resp_content = resp_content.replace("```json", "").replace("```", "").strip()

            # 解析JSON
            structured_data = json.loads(resp_content)
            messages = structured_data.get("messages", [])

            # ========== 格式化结果（去重+过滤） ==========
            final_messages = []
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                content = msg.get("content", "").strip()
                position = msg.get("position", "未知")
                color = msg.get("color", "未知")

                # 过滤无效消息+去重
                if len(content) >= 2 and not any(existing["content"] == content for existing in final_messages):
                    final_messages.append({
                        "content": content,
                        "position": self.standardize_position(position),
                        "color": self.standardize_color(color)
                    })

            # ========== 输出结果 ==========
            print(f"\n✅ 智能提取到 {len(final_messages)} 条消息")
            for i, msg in enumerate(final_messages):
                print(f"\n   {i + 1}. 内容：{msg['content'][:50]}")
                print(f"      位置：{msg['position']}，颜色：{msg['color']}")

            return final_messages

        except json.JSONDecodeError as e:
            print(f"\n⚠️  JSON解析失败：{str(e)}")
            print(f"⚠️  GLM-4返回内容：{resp_content[:200]}...")
            return self._emergency_extract(record)  # 终极兜底
        except Exception as e:
            print(f"\n❌ 提取失败：{str(e)}")
            return self._emergency_extract(record)  # 终极兜底

    # ========== 终极兜底：纯文本拆分（最后防线） ==========
    def _emergency_extract(self, record: str) -> List[Dict[str, str]]:
        """
        终极兜底：当ZHIPU_CHAT_MODEL也失败时，纯文本拆分（不依赖格式）
        逻辑：提取所有像聊天消息的短句，默认位置/颜色
        """
        print(f"\n🔧 启动终极兜底提取")
        # 清理文本
        record_clean = re.sub(r"思考过程:|性能指标:|总推理时间:|首 Token 延迟|思考完成延迟", "", record)
        record_clean = re.sub(r"[^\u4e00-\u9fff\w\s\.,，。！？；：""''💪~]", "", record_clean)

        # 按标点拆分短句（适配任意格式）
        sentences = re.split(r"[。！？；：\n]", record_clean)
        final_messages = []

        # 过滤+去重
        for sent in sentences:
            sent = sent.strip().strip('"').strip("'")
            # 过滤条件：长度≥2 + 不是数字/时间戳 + 不是无关描述
            if (len(sent) >= 2 and
                    not sent.isdigit() and
                    not sent.startswith("20:") and
                    not "气泡" in sent and
                    not "头像" in sent and
                    not "消息" in sent):
                if not any(existing["content"] == sent for existing in final_messages):
                    # 兜底位置/颜色：根据关键词判断
                    position = "右侧有头像" if "芸苔" in sent or "💪" in sent or "~" in sent else "左侧有头像"
                    color = "红色" if position == "右侧有头像" else "白色"
                    final_messages.append({
                        "content": sent,
                        "position": position,
                        "color": color
                    })

        print(f"\n✅ 兜底提取到 {len(final_messages)} 条消息")
        return final_messages

    def standardize_color(self, color: str) -> str:
        """标准化气泡颜色"""
        if not color or color == "未知":
            return "未知"
        color_lower = color.lower()
        color_map = {
            "粉红": "粉色", "红": "红色", "蓝": "蓝色", "绿": "绿色",
            "紫": "紫色", "黑": "黑色", "灰": "灰色", "橙": "橙色", "黄": "黄色", "白": "白色"
        }
        for key, val in color_map.items():
            if key in color_lower:
                return val
        return "未知"

    def standardize_position(self, position: str) -> str:
        """标准化头像位置"""
        if not position or position == "未知":
            return "未知"
        position_lower = position.lower()
        if "左" in position_lower:
            return "左侧有头像"
        elif "右" in position_lower:
            return "右侧有头像"
        return "未知"

    # 其他原有方法（run_continuous_loop、extract_chat_records等）保留不变

    # ==================== 其他原有方法保持不变 ====================
    def start_terminate_listener(self):
        """启动终止监听线程"""
        def listen_for_terminate():
            while self.auto_reply and not self.terminate_requested:
                try:
                    user_input = input()
                    if user_input.lower() == 's':
                        self.terminate_requested = True
                        print(f"\n⚠️  收到终止指令，将结束当前循环...")
                        break
                except:
                    pass

        thread = threading.Thread(target=listen_for_terminate, daemon=True)
        thread.start()

    def extract_chat_records(self) -> str:
        """提取聊天记录 - 头像位置版本"""
        try:
            task = f"""在{self.target_app}中进入{self.target_object}的聊天窗口，向下滑动1次，提取当前屏幕可见的聊天记录

重要说明：
1. 键盘已经关闭，不需要点击聊天区空白处关闭键盘
2. 直接向下滑动1次即可
3. 准确描述每条消息的气泡颜色（如白色、红色、蓝色、绿色等）
4. 准确描述每条消息的头像位置（左侧有头像/右侧有头像）
5. 不要判断发送方，只需描述客观信息
6. 不要简化描述，必须明确说明头像位置
7. 不要向上滑动
"""

            model_config = ModelConfig(
                base_url=self.args.base_url,
                model_name=self.args.model,
                api_key=self.args.apikey,
                lang=self.args.lang,
            )
            agent_config = AgentConfig(
                max_steps=self.args.max_steps,
                device_id=self.device_id,
                verbose=False,
                lang=self.args.lang,
            )
            phone_agent = PhoneAgent(model_config=model_config, agent_config=agent_config)

            task_with_prompt = task + "\n\n" + """你是手机操作执行器，严格按指令执行：

重要：准确识别头像位置和气泡颜色是判断消息发送方的关键！

消息提取要求：
1. 准确描述每条消息气泡的颜色（如：白色、红色、蓝色、绿色、粉色等）
2. **非常重要**：准确描述每条消息的头像位置（左侧有头像、右侧有头像）
3. **绝对不要简化描述**，必须明确说明"左侧有头像"或"右侧有头像"
4. 注意：我方发送的消息通常在右侧有头像，气泡颜色可能是粉色、绿色等深色
5. 对方发送的消息通常在左侧有头像，气泡颜色通常是白色或浅色
6. 不要判断发送方，只需客观描述颜色和头像位置

执行要求：
1. 如果指令中指定了聊天对象，必须进入该对象的聊天窗口
2. 提取聊天记录时：键盘已经关闭，不需要点击空白处关闭键盘，直接向下滑动1次
3. 提取聊天记录时：不要向上滚动，只向下滑动1次
4. 发送消息时：准确输入并点击发送按钮
5. 发送消息必须完整，不要截断
6. 输出聊天记录时，包括：
   - 每条消息的内容
   - 每条消息的气泡颜色
   - 每条消息的头像位置（左侧有头像/右侧有头像）
7. 不要判断消息发送方，只需描述客观信息（颜色和头像位置）
8. 不要查看完整聊天历史或更早的聊天记录，只需当前屏幕可见消息
9. 发送消息后必须使用Back按钮关闭键盘
"""

            raw_result = phone_agent.run(task_with_prompt)
            phone_agent.reset()

            return raw_result

        except Exception as e:
            print(f"\n提取聊天记录失败：{str(e)}")
            return f"提取聊天记录失败：{str(e)}"

    def send_reply_message(self, message: str) -> bool:
        """发送回复消息"""
        try:
            if not message or len(message) < 2:
                return False

            message = message.strip()

            # 根据不同APP使用不同的发送指令，发送后按Back键关闭键盘
            if self.target_app == "QQ":
                task = f"在{self.target_app}中给{self.target_object}发送消息：{message}，点击右下角的发送按钮，然后使用Back按钮关闭键盘"
            elif self.target_app == "微信":
                task = f"在{self.target_app}中给{self.target_object}发送消息：{message}，点击右侧的发送按钮，然后使用Back按钮关闭键盘"
            else:
                task = f"在{self.target_app}中给{self.target_object}发送消息：{message}，然后点击发送按钮，然后使用Back按钮关闭键盘"

            model_config = ModelConfig(
                base_url=self.args.base_url,
                model_name=self.args.model,
                api_key=self.args.apikey,
                lang=self.args.lang,
            )
            agent_config = AgentConfig(
                max_steps=self.args.max_steps,
                device_id=self.device_id,
                verbose=False,
                lang=self.args.lang,
            )
            phone_agent = PhoneAgent(model_config=model_config, agent_config=agent_config)

            raw_result = phone_agent.run(task)
            phone_agent.reset()

            # 检查是否发送成功
            success_keywords = ["已成功发送消息", "消息已成功发送", "发送了消息", "发送成功", "发送了", "已发送",
                                "点击了发送", "发送按钮", "点击发送按钮"]
            success = False
            for keyword in success_keywords:
                if keyword in raw_result:
                    success = True
                    break

            # 同时检查是否关闭了键盘
            if success and ("Back" in raw_result or "返回" in raw_result or "键盘已关闭" in raw_result):
                success = True
            elif success:
                # 发送成功但没有明确提到关闭键盘，也认为是成功
                success = True

            # 发送成功后，将消息加入我方消息列表
            if success:
                self.my_messages_list.append(message)
                print(f"\n✅ 已发送并存储到我方消息列表：{message[:30]}...")

            return success

        except Exception as e:
            print(f"\n发送消息失败：{str(e)}")
            return False

    def determine_message_ownership(self, messages: List[Dict[str, str]]) -> Tuple[List[str], List[str]]:
        """判断消息归属：以头像位置为主，颜色为辅，增加强保护逻辑"""
        other_messages = []  # 对方消息
        my_messages = []  # 我方消息

        for msg in messages:
            content = msg.get("content", "").strip()
            position = msg.get("position", "")
            color = msg.get("color", "")

            if not content or len(content) < 2:
                continue

            # 1. 首先检查是否是我方发送的消息（在我方消息列表中）- 使用更宽松的相似度
            is_my_message = False
            for my_msg in self.my_messages_list:
                # 降低相似度阈值以提高匹配率
                if self.is_message_similar(content, my_msg, threshold=0.5):
                    is_my_message = True
                    my_messages.append(content)
                    print(f"📨 识别为我方消息（从列表匹配）: {content[:30]}...")
                    break

            if is_my_message:
                continue

            # 2. 然后检查是否是对发送的消息（在对方消息列表中）
            is_other_message = False
            for other_msg in self.other_messages_list:
                if self.is_message_similar(content, other_msg, threshold=0.5):
                    is_other_message = True
                    other_messages.append(content)
                    print(f"📨 识别为对方消息（从列表匹配）: {content[:30]}...")
                    break

            if is_other_message:
                continue

            # 3. 以头像位置为主要判断依据
            # 左侧有头像 -> 对方消息
            # 右侧有头像 -> 我方消息
            if position == "左侧有头像":
                other_messages.append(content)
                print(f"\n📨 识别为对方消息（左侧有头像）: {content[:30]}...")
            elif position == "右侧有头像":
                my_messages.append(content)
                print(f"\n📨 识别为我方消息（右侧有头像）: {content[:30]}...")
            else:
                # 头像位置不明确，使用颜色作为辅助判断
                if color == "白色":
                    other_messages.append(content)
                    print(f"\n📨 识别为对方消息（白色）: {content[:30]}...")
                elif color in ["红色", "粉色", "粉红色", "蓝色", "绿色", "紫色", "黑色", "灰色", "橙色", "黄色"]:
                    my_messages.append(content)
                    print(f"\n📨 识别为我方消息（深色）: {content[:30]}...")
                else:
                    # 无法判断，暂时跳过
                    print(
                        f"⚠️  无法判断归属: {content[:30]}... (头像位置:{position}, 颜色:{color})")

        return other_messages, my_messages

    def generate_reply_for_latest_message(self, latest_message: str, history_messages: List[str]) -> str:
        """为最新的一条消息生成回复，其他消息作为历史上下文"""
        try:
            if not latest_message:
                return ""

            # 准备历史上下文
            history_prompt = ""
            if history_messages and len(history_messages) > 0:
                history_prompt = "\n\n=== 历史对话（按时间顺序，从旧到新）===\n"
                for i, msg in enumerate(history_messages[-5:], 1):  # 只取最近5条作为历史
                    history_prompt += f"{i}. {msg[:50]}...\n"

            # 构建提示词 - 优化以支持头像位置判断
            prompt = f"""你是一个聊天助手，名字叫"小芸"，性别为女，请用可爱俏皮的方式回复对方消息。
不要使用真实人名，用"你"、"对方"、"朋友"等代替。
保持对话的自然和友好。

重要提示：在聊天界面中，左侧有头像的消息是对方发送的，右侧有头像的消息是我方发送的。
请根据这个规则理解对话上下文。

对方最新消息：
"{latest_message}"
{history_prompt}

请基于以上对方最新消息生成回复，保持对话的连贯性。
注意：只需要回复最新的一条消息，历史消息仅作为上下文参考。"""

            messages = [
                {"role": "system",
                 "content": "你是一个友好的聊天助手，名字叫'小芸'，请用可爱俏皮的方式回复。记住：左侧有头像的消息是对方发送的，右侧有头像的消息是我方发送的。"},
                {"role": "user", "content": prompt}
            ]

            response = self.zhipu_client.chat.completions.create(
                model=ZHIPU_CHAT_MODEL,     
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            reply = response.choices[0].message.content.strip()

            # 清理回复，确保只包含一条消息
            if "。" in reply:
                # 取第一个句号前的部分作为回复
                reply = reply.split("。")[0] + "。"

            print(f"\n💬 为最新消息生成回复: {reply[:50]}...")
            return reply

        except Exception as e:
            print(f"\n⚠️  GLM-4生成回复失败: {e}")
            return ""

    def cleanup_message_lists(self):
        """清空消息列表，为下一次会话做准备"""
        self.other_messages_list = []
        self.my_messages_list = []
        print(f"\n🧹 已清空消息列表，为下一次会话做准备")

    def run_continuous_loop(self):
        """运行持续回复循环（头像位置版本）"""
        print(f"\n🔄 启动持续回复循环")
        print(f"\n🎯 目标：{self.target_app} -> {self.target_object}")
        print(f"\n💡 输入 's' 终止持续回复模式")

        # 打印判断规则
        print(f"\n📊 判断规则：")
        print(f"\n  • 头像位置为主：左侧有头像 → 对方消息，右侧有头像 → 我方消息")
        print(f"\n  • 颜色为辅：白色 → 对方消息，深色 → 我方消息")

        # 启动终止监听
        self.start_terminate_listener()

        # 获取历史上下文
        history_context = self.file_manager.get_recent_conversation_history(self.target_app, self.target_object,
                                                                            limit=5)
        if history_context:
            print(f"\n📚 加载了 {len(history_context)} 条历史对话记录")

        while (self.auto_reply and
               not self.terminate_requested and
               self.cycle_count < MAX_CYCLE_TIMES):

            self.cycle_count += 1
            print(f"\n{'=' * 60}")
            print(f"\n📊 循环轮次 {self.cycle_count}/{MAX_CYCLE_TIMES}")
            print(f"\n{'=' * 60}")

            # 1. 获取最新聊天记录
            print(f"\n📥 正在提取聊天记录...")
            current_record = self.extract_chat_records()

            # 显示原始记录（用于调试）
            if current_record:
                print(f"\n📋 原始记录片段: {current_record[:200]}...")

            # 2. 保存原始记录到文件
            filename = self.file_manager.save_record_to_log(self.cycle_count, current_record, self.target_app,
                                                            self.target_object)
            if filename:
                print(f"\n💾 记录已保存: record_logs/{filename}")

            # 3. 解析消息（使用新的ZHIPU_CHAT_MODEL结构化解析）
            messages = self.parse_messages_simple(current_record)
            if messages:
                print(f"\n📊 解析到 {len(messages)} 条消息")

                # 显示解析到的消息（只显示前3条）
                for i, msg in enumerate(messages[:3]):
                    print(f"\n  {i + 1}. 内容: {msg.get('content', '')[:40]}...")
                    print(
                        f"     头像位置: {msg.get('position', '未知')}, 颜色: {msg.get('color', '未知')}")

                # 4. 判断消息归属
                other_messages, my_messages = self.determine_message_ownership(messages)

                # 显示解析结果
                if other_messages:
                    print(f"\n📨 对方消息 ({len(other_messages)}条):")
                    for i, msg in enumerate(other_messages[:3]):  # 只显示前3条
                        print(f"\n   {i + 1}. {msg[:50]}...")
                if my_messages:
                    print(f"\n📨 我方消息 ({len(my_messages)}条):")
                    for i, msg in enumerate(my_messages[:3]):  # 只显示前3条
                        print(f"\n   {i + 1}. {msg[:50]}...")

                # 5. 检查是否有新的对方消息（不在对方消息列表中的）
                new_other_messages = []
                for msg in other_messages:
                    is_new = True
                    # 与对方消息列表对比
                    for existing_msg in self.other_messages_list:
                        if self.is_message_similar(msg, existing_msg, threshold=0.5):
                            is_new = False
                            break

                    # 与我方消息列表对比（避免将我方消息误判为对方消息）- 加强检查
                    if is_new:
                        for my_msg in self.my_messages_list:
                            if self.is_message_similar(msg, my_msg, threshold=0.5):
                                is_new = False
                                print(f"\n⚠️  消息'{msg[:30]}...'识别为我方已发送消息，跳过")
                                break

                    if is_new:
                        new_other_messages.append(msg)

                # 6. 如果有新消息，只回复最新的一条
                if new_other_messages:
                    # 只取最新的一条消息（列表中的最后一条）
                    latest_message = new_other_messages[-1]
                    print(f"\n🆕 发现新对方消息，只回复最新一条: {latest_message[:50]}...")

                    # 历史消息：除了最新消息之外的其他消息
                    history_messages = self.other_messages_list.copy()

                    # 使用GLM-4生成回复（只针对最新消息）
                    print(f"\n🤖 正在为最新消息生成回复...")
                    reply_message = self.generate_reply_for_latest_message(latest_message, history_messages)

                    if reply_message and len(reply_message) > 2:
                        print(f"\n💬 生成回复: {reply_message[:50]}...")
                        print(f"\n📤 正在发送回复...")

                        # 发送回复
                        success = self.send_reply_message(reply_message)

                        if success:
                            print(f"\n✅ 回复发送成功")

                            # 更新消息列表
                            for msg in new_other_messages:
                                if msg not in self.other_messages_list:
                                    self.other_messages_list.append(msg)

                            # 保存到对话历史
                            session_data = {
                                "type": "chat_session",
                                "session_id": self.session_id,
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "target_app": self.target_app,
                                "target_object": self.target_object,
                                "cycle": self.cycle_count,
                                "record_file": filename,
                                "reply_generated": reply_message,
                                "other_messages": [latest_message],  # 只保存最新消息
                                "sent_success": True,
                                "other_messages_list": self.other_messages_list[-10:],  # 保存最近10条
                                "my_messages_list": self.my_messages_list[-10:]  # 保存最近10条
                            }
                            self.file_manager.save_conversation_history(session_data)
                        else:
                            print(f"\n❌ 回复发送失败")
                    else:
                        print(f"\n⚠️  未能生成有效回复")
                else:
                    print(f"\n⏳ 没有发现新的对方消息")

                # 7. 更新我方消息列表（将识别为我方的消息加入列表）
                for msg in my_messages:
                    # 再次检查是否已在我方消息列表中，避免重复添加
                    already_exists = False
                    for existing_msg in self.my_messages_list:
                        if self.is_message_similar(msg, existing_msg, threshold=0.5):
                            already_exists = True
                            break

                    if not already_exists:
                        self.my_messages_list.append(msg)
                        print(f"\n📝 将消息加入我方消息列表: {msg[:30]}...")

                # 限制列表长度，避免无限增长
                if len(self.other_messages_list) > 50:
                    self.other_messages_list = self.other_messages_list[-50:]
                if len(self.my_messages_list) > 50:
                    self.my_messages_list = self.my_messages_list[-50:]

                # 显示当前统计
                print(
                    f"\n📊 统计: 对方消息({len(self.other_messages_list)}条), 我方消息({len(self.my_messages_list)}条)")
            else:
                print(f"\n⚠️  未能解析到消息")
                # 显示更多原始记录用于调试
                if current_record:
                    print(f"\n📋 原始记录（前500字符）:")
                    print(f"\n{current_record[:500]}")

            # 8. 检查终止
            if self.terminate_requested:
                break

            # 9. 等待下一轮
            print(f"\n⏰ 等待 {WAIT_INTERVAL} 秒后继续...")
            time.sleep(WAIT_INTERVAL)

        # 10. 循环结束后清空消息列表，为下一次会话做准备
        self.cleanup_message_lists()

        if self.terminate_requested:
            print(f"\n🛑 用户主动终止持续回复")
        elif self.cycle_count >= MAX_CYCLE_TIMES:
            print(f"\n⏹️  达到最大循环次数 {MAX_CYCLE_TIMES}")

        return True

    def is_message_similar(self, msg1: str, msg2: str, threshold: float = 0.5) -> bool:
        """
        判断两条消息是否相似（使用 difflib.SequenceMatcher 提高效率和准确性）
        threshold: 相似度阈值，0-1之间

        修复：使用 Python 标准库 difflib.SequenceMatcher 替换自定义 LCS 算法
        """
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

        # 完全相同
        if clean_msg1 == clean_msg2:
            return True

        # 包含关系
        if clean_msg1 in clean_msg2 or clean_msg2 in clean_msg1:
            return True

        # 使用 difflib.SequenceMatcher 计算相似度
        similarity = SequenceMatcher(None, clean_msg1, clean_msg2).ratio()

        # 调试输出
        if similarity > 0.3:  # 只在有一定相似度时输出调试信息
            print(f"\n🔍 相似度比较: {similarity:.2f}")
            print(f"\n  消息1 (清理后): {clean_msg1[:30]}")
            print(f"\n  消息2 (清理后): {clean_msg2[:30]}")
            print(f"\n  消息1 (原始): {msg1[:30]}")
            print(f"\n  消息2 (原始): {msg2[:30]}")

        return similarity >= threshold