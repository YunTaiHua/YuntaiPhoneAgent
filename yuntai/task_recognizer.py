#!/usr/bin/env python3
"""
任务识别模块
"""
import re
import json
from typing import Dict, Any, Optional

from yuntai.config import SHORTCUTS, ZHIPU_CLIENT,ZHIPU_JUDGEMENT_MODEL


class TaskRecognizer:
    def __init__(self, zhipu_client):
        self.zhipu_client = zhipu_client

        # 智能任务识别提示词（更新版）
        self.TASK_RECOGNITION_PROMPT = """你是一个任务识别专家，负责分析用户输入的指令并判断任务类型。

任务类型定义：
1. free_chat：用户只是想和你自由聊天，或者表达感谢、问候等，不涉及手机操作
   - 如"你好"、"今天天气怎么样"、"谢谢你帮我打开抖音"
   - 判断依据：不包含"打开"、"发送"、"发消息"等操作关键词，主要是自然语言交流

2. basic_operation：用户想要打开某个APP
   - 如"打开QQ"、"打开微信"、"打开淘宝"
   - 判断依据：只包含"打开"和APP名称，不包含其他操作如"发消息"、"选购"、"点赞"等

3. single_reply：用户想要在某个APP中给某个联系人发送一次消息，但**没有指定具体消息内容**
   - 如"打开QQ给黄恬发消息"、"在微信里给张三发送消息"
   - 判断依据：包含"打开"、"发消息"/"发送"和联系人，但**不包含具体的消息内容文本**
   - **关键区别**：指令中没有引号或冒号后的具体消息内容（如："你好呀"、"晚上有空吗"等）

4. continuous_reply：用户想要在某个APP中给某个联系人持续回复消息
   - 如"打开QQ给黄恬发消息auto"、"打开微信给张三发消息 auto"
   - 判断依据：包含"打开"、"发消息"/"发送"和联系人，且包含"auto"或"持续"，同样**没有指定具体消息内容**

5. complex_operation：用户想要执行复杂的手机操作，**包括发送具体指定的消息内容**
   - 如"打开QQ给黄恬发送消息：你好呀"、"在微信里给张三发消息：晚上有空吗？"
   - 如"打开淘宝选购一个便宜的文具盒"、"打开抖音点赞"、"在QQ里搜索文件"
   - **发送具体消息的判断依据**：包含"打开"、"发消息"/"发送"、联系人，**并且有具体的消息内容文本（通常用引号或冒号标注）**
   - 其他复杂操作判断依据：包含"打开"和更复杂的操作指令（如"选购"、"点赞"、"搜索"、"查看"等）

识别规则：
1. 首先检查是否包含感谢、问候等自然语言，如果是则归为free_chat
2. 检查是否包含"auto"或"持续"，如果有且包含"发消息"，则是continuous_reply（前提：没有具体消息内容）
3. 检查是否包含"发消息"或"发送"，如果有且不包含"auto"：
   - 如果**有具体的消息内容文本**（如引号内的内容或冒号后的内容），则是complex_operation
   - 如果**没有具体的消息内容文本**，则是single_reply
4. 检查是否只包含"打开"和APP名称，不包含其他操作，则是basic_operation
5. 如果包含"打开"和其他复杂操作词，则是complex_operation
6. 其他情况默认是free_chat

**关键判断点**：
- "发消息"或"发送" + **有具体内容** = complex_operation
- "发消息"或"发送" + **无具体内容** = single_reply（或continuous_reply如果包含auto）

返回格式要求：
请以JSON格式返回，包含以下字段：
{
  "task_type": "任务类型，只能是free_chat/basic_operation/single_reply/continuous_reply/complex_operation",
  "target_app": "目标APP，如QQ、微信等，如果没有则为空字符串",
  "target_object": "聊天对象，如果没有则为空字符串",
  "is_auto": true/false，是否为持续回复模式,
  "specific_content": "具体的消息内容，如果有则返回完整内容，否则为空字符串"
}

注意：只返回JSON格式，不要有其他任何内容。"""

        # 改进的phone_agent提示词（头像位置版本）
        self.PHONE_AGENT_EXTRACT_PROMPT = """你是手机操作执行器，严格按指令执行：

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

        # 在 __init__ 方法末尾添加
        self.MULTIMODAL_TASK_PROMPT = """你是一个多模态任务识别专家，负责判断用户指令是否涉及图像、视频、文件处理。

判断规则：
1. 如果用户明确提到了"图片"、"照片"、"图像"、"截图"、"拍照"、"查看图片"、"分析图片"等关键词 -> 需要多模态处理
2. 如果用户明确提到了"视频"、"录像"、"影片"、"看电影"、"看视频"、"分析视频"等关键词 -> 需要多模态处理
3. 如果用户明确提到了"文件"、"文档"、"PDF"、"Word"、"Excel"、"PPT"、"查看文件"、"分析文件"等关键词 -> 需要多模态处理
4. 如果用户提到了"上传"、"发送"、"分享"等动词 + 文件类型 -> 需要多模态处理
5. 如果用户只是普通文本聊天，没有文件相关意图 -> 不需要多模态处理

返回格式：
{
  "needs_multimodal": true/false,
  "file_type": "image/video/document/none",
  "description": "对文件处理需求的简短描述"
}
"""

    def recognize_multimodal_intent(self, user_input: str, has_attached_files: bool = False) -> Dict[str, Any]:
        """识别是否需要多模态处理"""
        if has_attached_files:
            return {
                "needs_multimodal": True,
                "file_type": "mixed",  # 有附件时认为是混合类型
                "description": "用户上传了附件"
            }

        try:
            messages = [
                {"role": "system", "content": self.MULTIMODAL_TASK_PROMPT},
                {"role": "user", "content": f"判断以下指令是否需要多模态处理：\n\n{user_input}"}
            ]

            response = self.zhipu_client.chat.completions.create(
                model=ZHIPU_JUDGEMENT_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=100,
                thinking={"type": "disabled"}
            )

            result = response.choices[0].message.content.strip()

            try:
                json_start = result.find('{')
                json_end = result.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    task_info = json.loads(result[json_start:json_end])
                    return task_info
            except:
                pass

            # 后备规则：关键词匹配
            user_input_lower = user_input.lower()
            multimodal_keywords = {
                "image": ["图片", "照片", "图像", "截图", "拍照", "相册", "jpg", "jpeg", "png", "gif"],
                "video": ["视频", "录像", "影片", "电影", "mp4", "avi", "mov", "观看视频"],
                "document": ["文件", "文档", "pdf", "word", "excel", "ppt", "txt", "查看文件"]
            }

            for file_type, keywords in multimodal_keywords.items():
                if any(keyword in user_input_lower for keyword in keywords):
                    return {
                        "needs_multimodal": True,
                        "file_type": file_type,
                        "description": f"检测到{file_type}相关指令"
                    }

            return {
                "needs_multimodal": False,
                "file_type": "none",
                "description": "普通文本聊天"
            }

        except Exception as e:
            print(f"多模态意图识别失败: {e}")
            return {
                "needs_multimodal": False,
                "file_type": "none",
                "description": "识别失败"
            }

    def recognize_task_intent(self, user_input: str) -> Dict[str, Any]:
        """
        使用ZHIPU_JUDGEMENT_MODEL智能识别任务意图
        返回任务类型、目标APP、目标对象等信息
        """
        try:
            # 如果输入是空的，返回默认值
            if not user_input or user_input.strip() == "":
                return {
                    "task_type": "free_chat",
                    "target_app": "",
                    "target_object": "",
                    "is_auto": False,
                    "specific_content": ""
                }

            # 使用ZHIPU_JUDGEMENT_MODEL进行任务识别
            messages = [
                {"role": "system", "content": self.TASK_RECOGNITION_PROMPT},
                {"role": "user", "content": f"请分析以下用户指令并返回JSON格式的任务识别结果：\n\n用户指令：{user_input}"}
            ]

            response = self.zhipu_client.chat.completions.create(
                model=ZHIPU_JUDGEMENT_MODEL,
                messages=messages,
                temperature=0.1,
                max_tokens=300,
                thinking={"type": "disabled"}
            )

            result = response.choices[0].message.content.strip()

            # 提取JSON部分
            try:
                # 找到JSON开始和结束的位置
                json_start = result.find('{')
                json_end = result.rfind('}') + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = result[json_start:json_end]
                    task_info = json.loads(json_str)

                    # 确保返回格式正确
                    return {
                        "task_type": task_info.get("task_type", "free_chat"),
                        "target_app": task_info.get("target_app", ""),
                        "target_object": task_info.get("target_object", ""),
                        "is_auto": task_info.get("is_auto", False),
                        "specific_content": task_info.get("specific_content", "")
                    }
            except json.JSONDecodeError:
                # 如果JSON解析失败，使用简单规则作为后备
                pass

            # 后备规则：简单关键词匹配
            user_input_lower = user_input.lower()

            # 检查是否包含感谢、问候等自然语言
            thank_keywords = ["谢谢", "感谢", "辛苦了", "麻烦你", "请帮", "帮我", "帮忙"]
            chat_keywords = ["你好", "请问", "问一下", "怎么样", "如何", "为什么", "什么", "哪里"]

            has_thank = any(keyword in user_input_lower for keyword in thank_keywords)
            has_chat = any(keyword in user_input_lower for keyword in chat_keywords)

            # 如果有感谢或聊天内容，优先认为是自由聊天
            if has_thank or has_chat:
                # 除非明确包含操作指令
                if "打开" in user_input_lower or "发消息" in user_input_lower or "发送" in user_input_lower:
                    # 继续后续判断
                    pass
                else:
                    return {
                        "task_type": "free_chat",
                        "target_app": "",
                        "target_object": "",
                        "is_auto": False,
                        "specific_content": ""
                    }

            # 检查是否包含具体的消息内容（引号或冒号后的内容）
            has_specific_content = False
            specific_content = ""

            # 查找引号内的内容
            quote_patterns = [r'["\']([^"\']+)["\']', r'["\']([^"\']+)["\']']
            for pattern in quote_patterns:
                match = re.search(pattern, user_input)
                if match:
                    has_specific_content = True
                    specific_content = match.group(1)
                    break

            # 查找冒号后的内容（排除时间格式）
            if not has_specific_content and "：" in user_input:
                parts = user_input.split("：")
                if len(parts) > 1:
                    last_part = parts[-1].strip()
                    # 排除时间格式（如 20:30）
                    if not re.match(r'\d{1,2}:\d{2}', last_part) and len(last_part) > 0:
                        has_specific_content = True
                        specific_content = last_part

            if not has_specific_content and ":" in user_input:
                parts = user_input.split(":")
                if len(parts) > 1:
                    last_part = parts[-1].strip()
                    # 排除时间格式（如 20:30）
                    if not re.match(r'\d{1,2}:\d{2}', last_part) and len(last_part) > 0:
                        has_specific_content = True
                        specific_content = last_part

            # 检查复杂操作关键词
            complex_keywords = ["选购", "购买", "买", "搜索", "查找", "查看", "点赞", "关注", "收藏", "分享",
                                "转发", "评论", "发布", "上传", "下载"]

            if "打开" in user_input_lower:
                # 如果有具体消息内容，就是complex_operation
                if has_specific_content and ("发消息" in user_input_lower or "发送" in user_input_lower):
                    return {
                        "task_type": "complex_operation",
                        "target_app": "",
                        "target_object": "",
                        "is_auto": False,
                        "specific_content": specific_content
                    }

                # 如果有其他复杂操作关键词
                if any(keyword in user_input_lower for keyword in complex_keywords):
                    return {
                        "task_type": "complex_operation",
                        "target_app": "",
                        "target_object": "",
                        "is_auto": False,
                        "specific_content": ""
                    }

            if "auto" in user_input_lower or "持续" in user_input_lower:
                if "打开" in user_input and "发消息" in user_input:
                    # 持续回复模式不应该有具体内容
                    if not has_specific_content:
                        return {
                            "task_type": "continuous_reply",
                            "target_app": "",
                            "target_object": "",
                            "is_auto": True,
                            "specific_content": ""
                        }
                    else:
                        # 有具体内容的持续回复也归为complex_operation
                        return {
                            "task_type": "complex_operation",
                            "target_app": "",
                            "target_object": "",
                            "is_auto": True,
                            "specific_content": specific_content
                        }

            if "打开" in user_input and "发消息" in user_input:
                # 区分是否有具体内容
                if has_specific_content:
                    return {
                        "task_type": "complex_operation",
                        "target_app": "",
                        "target_object": "",
                        "is_auto": False,
                        "specific_content": specific_content
                    }
                else:
                    return {
                        "task_type": "single_reply",
                        "target_app": "",
                        "target_object": "",
                        "is_auto": False,
                        "specific_content": ""
                    }

            if "打开" in user_input:
                return {
                    "task_type": "basic_operation",
                    "target_app": "",
                    "target_object": "",
                    "is_auto": False,
                    "specific_content": ""
                }

            # 默认是自由聊天
            return {
                "task_type": "free_chat",
                "target_app": "",
                "target_object": "",
                "is_auto": False,
                "specific_content": ""
            }

        except Exception as e:
            print(f"\n⚠️  任务识别失败: {e}")
            return {
                "task_type": "free_chat",
                "target_app": "",
                "target_object": "",
                "is_auto": False,
                "specific_content": ""
            }

    def extract_target_app_simple(self, task: str) -> Optional[str]:
        """简单提取目标APP"""
        task_lower = task.lower()
        supported_apps = ["qq", "微信", "抖音", "淘宝", "快手", "qq音乐", "支付宝", "微博", "小红书", "bilibili",
                          "百度", "京东", "拼多多"]

        for app in supported_apps:
            if app in task_lower:
                return app
        return None

    def extract_chat_object_simple(self, task: str) -> Optional[str]:
        """简单提取聊天对象"""
        # 简单正则匹配
        patterns = [
            r"给([^\s]+?)发消息",
            r"和([^\s]+?)聊天",
            r"向([^\s]+?)发送",
            r"回复([^\s]+?)"
        ]

        for pattern in patterns:
            match = re.search(pattern, task)
            if match and match.group(1):
                chat_obj = match.group(1).strip()
                if chat_obj not in ["消息", "聊天", "对话", "联系人", "他", "她", "我"]:
                    return chat_obj
        return None

    def extract_specific_content_simple(self, task: str) -> Optional[str]:
        """简单提取具体的消息内容"""
        # 查找引号内的内容
        quote_patterns = [r'["\']([^"\']+)["\']']
        for pattern in quote_patterns:
            match = re.search(pattern, task)
            if match:
                return match.group(1).strip()

        # 查找冒号后的内容（排除时间格式）
        if "：" in task:
            parts = task.split("：")
            if len(parts) > 1:
                last_part = parts[-1].strip()
                # 排除时间格式
                if not re.match(r'\d{1,2}:\d{2}', last_part):
                    return last_part

        if ":" in task:
            parts = task.split(":")
            if len(parts) > 1:
                last_part = parts[-1].strip()
                # 排除时间格式
                if not re.match(r'\d{1,2}:\d{2}', last_part):
                    return last_part

        return None