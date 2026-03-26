"""
controller.py - Web控制器
处理所有Web请求和业务逻辑
重构版本 - 分离输出捕获类
"""

from __future__ import annotations

import os
import sys
import asyncio
import threading
import datetime
import json
import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

from yuntai.core.config import (
    PROJECT_ROOT, SCRCPY_PATH, SHORTCUTS, CONVERSATION_HISTORY_FILE, TEMP_DIR
)
from yuntai.services.task_manager import TaskManager, TTSManager
from yuntai.chains import TaskChain, ReplyChain
from yuntai.agents import JudgementAgent
from yuntai.callbacks import get_callback_manager, LoggingCallbackHandler, PerformanceCallbackHandler

from .ws_manager import ConnectionManager
from .output_capture import WebOutputCapture

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from fastapi import WebSocket
    from langchain_core.callbacks import BaseCallbackHandler


class WebController:
    """Web控制器 - 处理所有Web请求和业务逻辑"""

    def __init__(self, ws_manager: ConnectionManager) -> None:
        self.ws_manager: ConnectionManager = ws_manager
        self.project_root: str = PROJECT_ROOT
        self.scrcpy_path: str = SCRCPY_PATH

        self._task_manager: TaskManager | None = None
        self._task_chain: TaskChain | None = None
        self._judgement_agent: JudgementAgent | None = None

        self.is_executing: bool = False
        self.is_continuous_mode: bool = False
        self.terminate_flag: threading.Event = threading.Event()
        self._current_reply_chain: ReplyChain | None = None

        self.device_type: str = "android"

        self.attached_files: list[str] = []

        self.is_dark_theme: bool = False

        self.tts_enabled: bool = False
        self._tts_loaded: bool = False

        self._history_cache: list[dict[str, Any]] | None = None
        self._history_file: Path = Path(TEMP_DIR) / "web_history.json"

        self.output_capture: WebOutputCapture = WebOutputCapture(self)

        self.callback_manager = get_callback_manager()
        self.logging_handler: LoggingCallbackHandler
        self.performance_handler: PerformanceCallbackHandler

        self._setup_callbacks()

    def _setup_callbacks(self) -> None:
        """设置 LangChain Callbacks"""
        self.logging_handler = LoggingCallbackHandler(
            enable_console=False,
            enable_detailed=True
        )

        self.callback_manager.register_handler(
            name="web_logging",
            handler=self.logging_handler,
            is_global=True
        )

        self.performance_handler = PerformanceCallbackHandler(
            enable_console=False,
            enable_detailed=False
        )

        self.callback_manager.register_handler(
            name="web_performance",
            handler=self.performance_handler,
            is_global=True
        )

    def get_callbacks(self) -> list[BaseCallbackHandler]:
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

    async def send_output(self, text: str, msg_type: str = "output") -> None:
        """发送输出到前端"""
        await self.ws_manager.broadcast({
            "type": msg_type,
            "data": text,
            "timestamp": datetime.datetime.now().isoformat()
        })

    async def send_toast(self, message: str, msg_type: str = "info") -> None:
        """发送Toast消息"""
        await self.ws_manager.broadcast({
            "type": "toast",
            "message": message,
            "msg_type": msg_type,
            "timestamp": datetime.datetime.now().isoformat()
        })

    async def send_state_update(self, state: dict[str, Any]) -> None:
        """发送状态更新"""
        await self.ws_manager.broadcast({
            "type": "state_update",
            "data": state,
            "timestamp": datetime.datetime.now().isoformat()
        })

    async def send_tts_loading(self, message: str, show: bool = True) -> None:
        """发送TTS加载状态"""
        await self.ws_manager.broadcast({
            "type": "tts_loading",
            "message": message,
            "show": show,
            "timestamp": datetime.datetime.now().isoformat()
        })

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """发送个人消息"""
        await self.ws_manager.send_personal_message(message, websocket)

    def get_state(self) -> dict[str, Any]:
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
            "attached_files": [Path(f).name for f in self.attached_files],
            "current_page": 0
        }

    def get_tts_models(self) -> dict[str, Any]:
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

    def get_audio_history(self) -> list[dict[str, Any]]:
        """获取历史音频列表"""
        from yuntai.core.config import TTS_OUTPUT_DIR
        audio_dir = Path(TTS_OUTPUT_DIR)
        if not audio_dir.exists():
            return []

        audio_files: list[dict[str, Any]] = []
        for f in audio_dir.iterdir():
            if f.suffix == '.wav':
                stat = f.stat()
                audio_files.append({
                    "name": f.name,
                    "path": f"/api/tts/audio/{f.name}",
                    "size": stat.st_size,
                    "mtime": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        audio_files.sort(key=lambda x: x["mtime"], reverse=True)
        return audio_files

    def preload_tts_async(self, play_welcome_after_load: bool = False) -> None:
        """异步预加载TTS模块"""
        if self._tts_loaded:
            return

        def load() -> None:
            try:
                success = self.task_manager.preload_tts_modules()
                self.tts_enabled = success
                self._tts_loaded = True
                print(f"{'✅' if success else '❌'} TTS模块预加载{'成功' if success else '失败'}")

                if success and play_welcome_after_load:
                    self._play_welcome_voice()
                elif play_welcome_after_load:
                    self._send_welcome_complete(tts_success=False)

            except Exception as e:
                print(f"❌ TTS预加载失败: {e}")
                if play_welcome_after_load:
                    self._send_welcome_complete(tts_success=False)

        threading.Thread(target=load, daemon=True).start()

    def _send_welcome_complete(self, tts_success: bool = False) -> None:
        """发送欢迎完成消息"""
        self.ws_manager.mark_first_connection_done()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.ws_manager.broadcast({
                "type": "welcome_complete",
                "tts_success": tts_success
            }))
        finally:
            loop.close()

    def _play_welcome_voice(self) -> None:
        """播放欢迎语音（TTS测试）"""
        import time
        time.sleep(0.5)

        welcome_text = "您好，很高兴为您服务"
        try:
            tts = self.task_manager.tts_manager

            if tts and tts.tts_available:
                ref_audio = tts.get_current_model("audio")
                ref_text = tts.get_current_model("text")

                if not ref_audio:
                    audio_files = list(tts.tts_files_database.get("audio", {}).keys())
                    if audio_files:
                        ref_audio = tts.tts_files_database.get("audio", {}).get(audio_files[0])
                        logger.info(f"自动选择参考音频: {audio_files[0]}")

                if not ref_text:
                    text_files = list(tts.tts_files_database.get("text", {}).keys())
                    if text_files:
                        ref_text = tts.tts_files_database.get("text", {}).get(text_files[0])
                        logger.info(f"自动选择参考文本: {text_files[0]}")

                if ref_audio and ref_text:
                    success, _ = tts.synthesize_text(
                        text=welcome_text,
                        ref_audio_path=ref_audio,
                        ref_text_path=ref_text,
                        auto_play=True
                    )
                    if success:
                        logger.info("TTS测试成功：欢迎语音播放成功")
                        self.tts_enabled = True
                        self._send_welcome_complete(tts_success=True)
                        return
                    else:
                        logger.warning("TTS测试失败：欢迎语音合成失败")
                        self.tts_enabled = False
                else:
                    logger.warning("TTS测试跳过：没有可用的参考音频或文本")
                    self.tts_enabled = False
            else:
                logger.warning("TTS测试跳过：TTS模块不可用")
                self.tts_enabled = False

        except Exception as e:
            logger.error(f"TTS测试异常: {e}")
            self.tts_enabled = False

        self._send_welcome_complete(tts_success=False)

    def get_available_devices(self) -> list[str]:
        """获取可用设备列表"""
        try:
            devices = self.task_manager.detect_devices()
            return devices if devices else []
        except Exception as e:
            print(f"获取设备列表失败: {e}")
            return []

    def get_history(self) -> list[dict[str, Any]]:
        """获取历史记录"""
        try:
            if self._history_file.exists():
                data = json.loads(self._history_file.read_text(encoding="utf-8"))
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"读取历史记录失败: {e}")
        return []

    def save_history(self, command: str, result: str) -> None:
        """保存历史记录"""
        try:
            history = self.get_history()
            history.insert(0, {
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "command": command,
                "result": result[:500] if result else ""
            })
            history = history[:100]

            self._history_file.parent.mkdir(parents=True, exist_ok=True)
            self._history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"保存历史记录失败: {e}")

    def clear_history(self) -> dict[str, Any]:
        """清空历史记录"""
        try:
            if self._history_file.exists():
                self._history_file.unlink()
            return {"success": True}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_dynamic_features(self) -> dict[str, Any]:
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

    def get_settings_info(self, setting_type: str) -> dict[str, Any]:
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
