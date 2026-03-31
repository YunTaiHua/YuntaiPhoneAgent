"""
TTS 集成 Mixin
==============

TTSIntegrationMixin 包含 TTS 预加载、欢迎语合成、音频播放等待等 TTS 相关功能。
"""
import sys
import logging
import threading
import queue
import time
import datetime
import traceback
from typing import Any
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QObject

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class TTSIntegrationMixin:
    """
    TTS 集成 Mixin

    包含 TTS 预加载、欢迎语合成、音频播放等待等 TTS 相关功能。
    通过 self 属性访问 ControllerCore 中初始化的实例变量。
    """

    # ============ TTS预加载 ============

    def preload_tts_modules(self):
        """预加载TTS模块"""
        logger.debug("预加载 TTS 模块")

        def load_async():
            self._show_tts_loading_signal.emit("正在加载TTS语音资源中...")
            success = self.task_manager.preload_tts_modules()
            self._update_tts_indicator_signal.emit(success)
            if success:
                self._synthesize_welcome_message()
            else:
                self._hide_tts_loading_signal.emit()

        threading.Thread(target=load_async, daemon=True).start()

    def _synthesize_welcome_message(self):
        """启动时合成欢迎语（自动降级）"""
        logger.debug("合成欢迎语")
        try:
            tts = self.task_manager.tts_manager

            for model_type, db_key in [("gpt", "gpt"), ("sovits", "sovits"), ("audio", "audio")]:
                if not tts.get_current_model(model_type) and tts.tts_files_database[db_key]:
                    tts.set_current_model(model_type, list(tts.tts_files_database[db_key].keys())[0])

            if tts.get_current_model("audio") and not tts.get_current_model("text"):
                audio_path = Path(tts.get_current_model("audio"))
                audio_name = audio_path.stem
                txt_file = f"{audio_name}.txt"
                if txt_file in tts.tts_files_database["text"]:
                    tts.set_current_model("text", txt_file)

            if not tts.get_current_model("text") and tts.tts_files_database["text"]:
                tts.set_current_model("text", list(tts.tts_files_database["text"].keys())[0])

            if not all([tts.get_current_model(t) for t in ["gpt", "sovits", "audio", "text"]]):
                self._hide_tts_loading_signal.emit()
                return

            self._show_tts_loading_signal.emit("正在合成欢迎语...")
            tts.speak_text_intelligently("你好，我是小芸，很高兴为您服务")
            self._wait_audio_then_hide()
        except AttributeError as e:
            logger.debug("TTS组件属性访问失败: %s", e)
            self._hide_tts_loading_signal.emit()
        except RuntimeError as e:
            # UI 组件已被销毁
            logger.debug("TTS UI组件已销毁: %s", e)
            self._hide_tts_loading_signal.emit()
        except Exception as e:
            logger.warning("TTS初始化异常: %s", e)
            self._hide_tts_loading_signal.emit()

    def _wait_audio_then_hide(self):
        """等待音频播放完成后隐藏遮罩"""
        def wait_thread():
            try:
                tts = self.task_manager.tts_manager
                max_wait = 30
                waited = 0
                while tts.is_playing_audio and waited < max_wait:
                    time.sleep(0.5)
                    waited += 0.5
            finally:
                self._hide_tts_loading_signal.emit()

        threading.Thread(target=wait_thread, daemon=True).start()
