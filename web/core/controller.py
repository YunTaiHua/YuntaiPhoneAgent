"""
controller.py - Web控制器
处理所有Web请求和业务逻辑
重构版本 - 分离输出捕获类
"""

import os
import sys
import asyncio
import threading
import datetime
import json
from typing import Optional, Dict, Any, List

from yuntai.core.config import (
    PROJECT_ROOT, SCRCPY_PATH, SHORTCUTS, CONVERSATION_HISTORY_FILE, TEMP_DIR
)
from yuntai.services.task_manager import TaskManager
from yuntai.chains import TaskChain, ReplyChain
from yuntai.agents import JudgementAgent
from yuntai.callbacks import get_callback_manager, LoggingCallbackHandler, PerformanceCallbackHandler

from .ws_manager import ConnectionManager
from .output_capture import WebOutputCapture


class WebController:
    """Web控制器 - 处理所有Web请求和业务逻辑"""

    def __init__(self, ws_manager: ConnectionManager):
        self.ws_manager = ws_manager
        self.project_root = PROJECT_ROOT
        self.scrcpy_path = SCRCPY_PATH

        # 延迟初始化任务管理器（避免阻塞）
        self._task_manager = None
        self._task_chain = None
        self._judgement_agent = None

        # 状态变量
        self.is_executing = False
        self.is_continuous_mode = False
        self.terminate_flag = threading.Event()
        self._current_reply_chain = None

        # 设备类型
        self.device_type = "android"

        # 附件文件
        self.attached_files: List[str] = []

        # 主题状态
        self.is_dark_theme = False

        # TTS状态
        self.tts_enabled = False
        self._tts_loaded = False

        # 历史记录缓存
        self._history_cache = None
        self._history_file = os.path.join(TEMP_DIR, "web_history.json")

        # 输出捕获器
        self.output_capture = WebOutputCapture(self)

        # 初始化回调管理器
        self._setup_callbacks()

    def _setup_callbacks(self):
        """设置 LangChain Callbacks"""
        # 获取全局回调管理器
        self.callback_manager = get_callback_manager()

        # 创建日志处理器（记录到文件）
        self.logging_handler = LoggingCallbackHandler(
            enable_console=False,
            enable_detailed=True
        )

        # 注册日志处理器
        self.callback_manager.register_handler(
            name="web_logging",
            handler=self.logging_handler,
            is_global=True
        )

        # 创建性能监控处理器
        self.performance_handler = PerformanceCallbackHandler(
            enable_console=False,
            enable_detailed=False
        )

        # 注册性能处理器
        self.callback_manager.register_handler(
            name="web_performance",
            handler=self.performance_handler,
            is_global=True
        )

    def get_callbacks(self) -> List:
        """获取回调处理器列表"""
        return self.callback_manager.get_callbacks(include_global=True)

    @property
    def task_manager(self) -> TaskManager:
        """延迟初始化任务管理器"""
        if self._task_manager is None:
            self._task_manager = TaskManager(self.project_root, self.scrcpy_path)
        return self._task_manager

    @property
    def task_chain(self) -> TaskChain:
        """延迟初始化TaskChain"""
        if self._task_chain is None:
            self._task_chain = TaskChain(
                device_id="",
                file_manager=self.task_manager.file_manager,
                tts_manager=self.task_manager.tts_manager
            )
        return self._task_chain

    @property
    def judgement_agent(self) -> JudgementAgent:
        """延迟初始化判断Agent"""
        if self._judgement_agent is None:
            self._judgement_agent = JudgementAgent()
        return self._judgement_agent

    # ==================== 消息发送方法 ====================

    async def send_output(self, text: str, msg_type: str = "output"):
        """发送输出到前端"""
        await self.ws_manager.broadcast({
            "type": msg_type,
            "data": text,
            "timestamp": datetime.datetime.now().isoformat()
        })

    async def send_toast(self, message: str, msg_type: str = "info"):
        """发送Toast消息"""
        await self.ws_manager.broadcast({
            "type": "toast",
            "message": message,
            "msg_type": msg_type,
            "timestamp": datetime.datetime.now().isoformat()
        })

    async def send_state_update(self, state: dict):
        """发送状态更新"""
        await self.ws_manager.broadcast({
            "type": "state_update",
            "data": state,
            "timestamp": datetime.datetime.now().isoformat()
        })

    async def send_tts_loading(self, message: str, show: bool = True):
        """发送TTS加载状态"""
        await self.ws_manager.broadcast({
            "type": "tts_loading",
            "message": message,
            "show": show,
            "timestamp": datetime.datetime.now().isoformat()
        })

    async def send_personal_message(self, message: dict, websocket):
        """发送个人消息"""
        await self.ws_manager.send_personal_message(message, websocket)

    # ==================== 状态获取 ====================

    def get_state(self) -> dict:
        """获取当前状态"""
        is_connected = False
        device_id = ""
        try:
            is_connected = self.task_manager.is_connected
            device_id = self.task_manager.device_id
        except:
            pass

        return {
            "is_executing": self.is_executing,
            "is_continuous_mode": self.is_continuous_mode,
            "is_connected": is_connected,
            "device_id": device_id,
            "device_type": self.device_type,
            "tts_enabled": self.tts_enabled,
            "is_dark_theme": self.is_dark_theme,
            "attached_files": [os.path.basename(f) for f in self.attached_files],
            "current_page": 0
        }

    def get_tts_models(self) -> dict:
        """获取TTS模型列表"""
        try:
            tts = self.task_manager.tts_manager
            return {
                "gpt_models": list(tts.tts_files_database.get("gpt", {}).keys()),
                "sovits_models": list(tts.tts_files_database.get("sovits", {}).keys()),
                "audio_files": list(tts.tts_files_database.get("audio", {}).keys()),
                "text_files": list(tts.tts_files_database.get("text", {}).keys()),
                "current_gpt": tts.get_current_model("gpt"),
                "current_sovits": tts.get_current_model("sovits"),
                "current_audio": tts.get_current_model("audio"),
                "current_text": tts.get_current_model("text")
            }
        except Exception as e:
            print(f"获取TTS模型失败: {e}")
            return {
                "gpt_models": [],
                "sovits_models": [],
                "audio_files": [],
                "text_files": [],
                "current_gpt": None,
                "current_sovits": None,
                "current_audio": None,
                "current_text": None
            }

    def get_audio_history(self) -> list:
        """获取历史音频列表"""
        from yuntai.core.config import TTS_OUTPUT_DIR
        audio_dir = TTS_OUTPUT_DIR
        if not os.path.exists(audio_dir):
            return []

        audio_files = []
        for f in os.listdir(audio_dir):
            if f.endswith('.wav'):
                filepath = os.path.join(audio_dir, f)
                stat = os.stat(filepath)
                audio_files.append({
                    "name": f,
                    "path": f"/api/tts/audio/{f}",
                    "size": stat.st_size,
                    "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        audio_files.sort(key=lambda x: x["mtime"], reverse=True)
        return audio_files

    # ==================== TTS预加载 ====================

    def preload_tts_async(self, play_welcome_after_load=False):
        """异步预加载TTS模块"""
        if self._tts_loaded:
            return

        def load():
            try:
                success = self.task_manager.preload_tts_modules()
                self.tts_enabled = success
                self._tts_loaded = True
                print(f"{'✅' if success else '❌'} TTS模块预加载{'成功' if success else '失败'}")

                # 如果TTS加载成功且需要播放欢迎语音
                if success and play_welcome_after_load:
                    self._play_welcome_voice()
                elif play_welcome_after_load:
                    # TTS加载失败，直接发送完成消息关闭遮罩
                    self._send_welcome_complete(tts_success=False)

            except Exception as e:
                print(f"❌ TTS预加载失败: {e}")
                if play_welcome_after_load:
                    self._send_welcome_complete(tts_success=False)

        threading.Thread(target=load, daemon=True).start()

    def _send_welcome_complete(self, tts_success=False):
        """发送欢迎完成消息"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.ws_manager.broadcast({
                "type": "welcome_complete",
                "tts_success": tts_success
            }))
        finally:
            loop.close()

    def _play_welcome_voice(self):
        """播放欢迎语音（TTS测试）"""
        import time
        # 等待一小段时间确保TTS完全就绪
        time.sleep(0.5)

        welcome_text = "您好，很高兴为您服务"
        try:
            tts = self.task_manager.tts_manager

            if tts and tts.tts_available:
                # 获取当前参考音频和文本
                ref_audio = tts.get_current_model("audio")
                ref_text = tts.get_current_model("text")

                # 如果未配置，自动选择第一个
                if not ref_audio:
                    audio_files = list(tts.tts_files_database.get("audio", {}).keys())
                    if audio_files:
                        ref_audio = tts.tts_files_database.get("audio", {}).get(audio_files[0])
                        print(f"🎵 自动选择参考音频: {audio_files[0]}")

                if not ref_text:
                    text_files = list(tts.tts_files_database.get("text", {}).keys())
                    if text_files:
                        ref_text = tts.tts_files_database.get("text", {}).get(text_files[0])
                        print(f"📄 自动选择参考文本: {text_files[0]}")

                if ref_audio and ref_text:
                    success, _ = tts.synthesize_text(
                        text=welcome_text,
                        ref_audio_path=ref_audio,
                        ref_text_path=ref_text,
                        auto_play=True
                    )
                    if success:
                        print("✅ TTS测试成功：欢迎语音播放成功")
                        self.tts_enabled = True
                        # TTS测试成功，发送成功标记
                        self._send_welcome_complete(tts_success=True)
                        return
                    else:
                        print("⚠️ TTS测试失败：欢迎语音合成失败")
                        self.tts_enabled = False
                else:
                    print("⚠️ TTS测试跳过：没有可用的参考音频或文本")
                    self.tts_enabled = False
            else:
                print("⚠️ TTS测试跳过：TTS模块不可用")
                self.tts_enabled = False

        except Exception as e:
            print(f"⚠️ TTS测试异常: {e}")
            self.tts_enabled = False

        # TTS测试失败或不可用，发送失败标记
        self._send_welcome_complete(tts_success=False)

    # ==================== 设备管理 ====================

    def get_available_devices(self) -> list:
        """获取可用设备列表"""
        try:
            devices = self.task_manager.detect_devices()
            return devices if devices else []
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            return []

    # ==================== 历史记录 ====================

    def get_history(self) -> list:
        """获取历史记录"""
        try:
            if os.path.exists(self._history_file):
                with open(self._history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"读取历史记录失败: {e}")
        return []

    def save_history(self, command: str, result: str):
        """保存历史记录"""
        try:
            history = self.get_history()
            history.insert(0, {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "command": command,
                "result": result[:500] if result else ""  # 限制结果长度
            })
            # 只保留最近100条
            history = history[:100]

            os.makedirs(os.path.dirname(self._history_file), exist_ok=True)
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def clear_history(self) -> dict:
        """清空历史记录"""
        try:
            if os.path.exists(self._history_file):
                os.remove(self._history_file)
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    # ==================== 动态功能 ====================

    def get_dynamic_features(self) -> dict:
        """获取动态功能列表"""
        return {
            "features": [
                {
                    "id": "image_gen",
                    "name": "图片生成",
                    "icon": "🖼️",
                    "description": "使用AI生成图片",
                    "enabled": True
                },
                {
                    "id": "video_gen",
                    "name": "视频生成",
                    "icon": "🎬",
                    "description": "使用AI生成视频",
                    "enabled": True
                },
                {
                    "id": "audio_process",
                    "name": "音频处理",
                    "icon": "🎵",
                    "description": "音频格式转换和处理",
                    "enabled": True
                },
                {
                    "id": "batch_operation",
                    "name": "批量操作",
                    "icon": "📦",
                    "description": "批量执行手机操作",
                    "enabled": True
                },
                {
                    "id": "screen_record",
                    "name": "屏幕录制",
                    "icon": "📹",
                    "description": "录制手机屏幕",
                    "enabled": True
                },
                {
                    "id": "auto_task",
                    "name": "自动化任务",
                    "icon": "🤖",
                    "description": "创建自动化任务脚本",
                    "enabled": True
                }
            ]
        }

    # ==================== 设置相关 ====================

    def get_settings_info(self, setting_type: str) -> dict:
        """获取设置信息"""
        if setting_type == "connection":
            return {
                "title": "连接配置",
                "items": [
                    {"label": "设备类型", "value": self.device_type},
                    {"label": "连接状态", "value": "已连接" if self.task_manager.is_connected else "未连接"},
                    {"label": "设备ID", "value": self.task_manager.device_id or "无"}
                ]
            }
        elif setting_type == "system":
            return {
                "title": "系统检查",
                "items": [
                    {"label": "API状态", "value": "正常"},
                    {"label": "版本", "value": "v1.3.3"},
                    {"label": "Python版本", "value": sys.version.split()[0]}
                ]
            }
        elif setting_type == "tts":
            return {
                "title": "TTS语音配置",
                "items": [
                    {"label": "TTS状态", "value": "已启用" if self.tts_enabled else "未启用"},
                    {"label": "GPT模型", "value": self.get_tts_models().get("current_gpt") or "未选择"},
                    {"label": "SoVITS模型", "value": self.get_tts_models().get("current_sovits") or "未选择"}
                ]
            }
        elif setting_type == "files":
            return {
                "title": "文件管理",
                "items": [
                    {"label": "上传目录", "value": "temp/uploads/"},
                    {"label": "TTS输出目录", "value": "temp/tts_output/"},
                    {"label": "生成文件目录", "value": "temp/generated/"}
                ]
            }
        return {"title": "设置", "items": []}
