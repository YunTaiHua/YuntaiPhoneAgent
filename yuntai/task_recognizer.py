#!/usr/bin/env python3
"""
任务识别模块
"""
import re
import json
from typing import Dict, Any, Optional

from yuntai.config import SHORTCUTS, ZHIPU_CLIENT,ZHIPU_JUDGEMENT_MODEL
from yuntai.prompts.task_recognizer_prompt import TASK_RECOGNITION_PROMPT, PHONE_AGENT_EXTRACT_PROMPT, MULTIMODAL_TASK_PROMPT


class TaskRecognizer:
    def __init__(self, zhipu_client):
        self.zhipu_client = zhipu_client

        # 从prompts目录导入提示词
        self.TASK_RECOGNITION_PROMPT = TASK_RECOGNITION_PROMPT
        self.PHONE_AGENT_EXTRACT_PROMPT = PHONE_AGENT_EXTRACT_PROMPT
        self.MULTIMODAL_TASK_PROMPT = MULTIMODAL_TASK_PROMPT

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