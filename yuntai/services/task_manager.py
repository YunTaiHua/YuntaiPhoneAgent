"""
任务管理模块
============

负责连接管理、TTS 管理和工具初始化，任务分发逻辑已迁移到 TaskChain。

主要组件:
    - TTSManager: TTS 管理器，统一管理所有 TTS 相关功能
    - TaskManager: 任务管理器，负责连接管理和工具初始化

TTSManager 功能:
    - synthesize_text: 合成语音
    - speak_text_intelligently: 智能语音合成
    - play_audio_file: 播放音频文件
    - stop_current_audio_playback: 停止音频播放
    - synthesize_long_text_serial: 分段串行合成长文本

TaskManager 功能:
    - connect_device: 连接设备
    - disconnect_device: 断开设备
    - detect_devices: 检测设备
    - preload_tts_modules: 预加载 TTS 模块

使用示例:
    >>> task_manager = TaskManager(project_root, scrcpy_path)
    >>> success, device_id, message = task_manager.connect_device(config)
    >>> task_manager.tts_manager.speak_text_intelligently("你好")
"""

from __future__ import annotations

import threading
import time
import datetime
import traceback
from typing import Any
from pathlib import Path
import warnings
import logging
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

from zhipuai import ZhipuAI

from yuntai.services.connection_manager import ConnectionManager
from yuntai.services.file_manager import FileManager
from yuntai.core.agent_executor import AgentExecutor
from yuntai.core.utils import Utils

from yuntai.managers import (
    TTSDatabaseManager,
    TTSTextProcessor,
    TTSEngine,
    TTSAudioPlayer,
)

from yuntai.core.config import (
    GPT_SOVITS_ROOT,
    GPT_MODEL_DIR,
    SOVITS_MODEL_DIR,
    REF_AUDIO_ROOT,
    REF_TEXT_ROOT,
    BERT_MODEL_PATH,
    HUBERT_MODEL_PATH,
    TTS_OUTPUT_DIR,
    ZHIPU_API_KEY,
    MAX_HISTORY_LENGTH,
    MAX_CYCLE_TIMES,
    MAX_RETRY_TIMES,
    WAIT_INTERVAL,
    TTS_REF_LANGUAGE,
    TTS_TARGET_LANGUAGE,
    SHORTCUTS,
    TTS_MAX_SEGMENT_LENGTH,
    TTS_MIN_TEXT_LENGTH,
    TTS_TOP_P,
    TTS_TEMPERATURE,
    TTS_SPEED,
    ZHIPU_MODEL,
    ZHIPU_CHAT_MODEL,
    ZHIPU_API_BASE_URL
)

logger: logging.Logger = logging.getLogger(__name__)


class TTSManager:
    """
    TTS管理器 - 统一管理所有TTS相关功能
    
    整合TTS引擎、数据库管理器、文本处理器和音频播放器，
    提供统一的TTS功能接口。
    
    Attributes:
        project_root: 项目根目录路径
        default_tts_config: 默认TTS配置字典
        tts_enabled: TTS功能是否启用
        tts_available: TTS模块是否可用
        tts_modules_loaded: TTS模块是否已加载
        database_manager: TTS数据库管理器
        text_processor: TTS文本处理器
        audio_player: TTS音频播放器
        engine: TTS引擎实例
        executor: 线程池执行器
    """

    def __init__(self, project_root: str) -> None:
        """
        初始化TTS管理器
        
        Args:
            project_root: 项目根目录路径
        """
        self.project_root: str = project_root

        self.default_tts_config: dict[str, str] = {
            "gpt_model_dir": GPT_MODEL_DIR,
            "sovits_model_dir": SOVITS_MODEL_DIR,
            "ref_audio_root": REF_AUDIO_ROOT,
            "ref_text_root": REF_TEXT_ROOT,
            "ref_language": TTS_REF_LANGUAGE,
            "target_language": TTS_TARGET_LANGUAGE,
            "output_path": TTS_OUTPUT_DIR,
            "bert_model_path": BERT_MODEL_PATH,
            "hubert_model_path": HUBERT_MODEL_PATH
        }

        self.tts_enabled: bool = False
        self.tts_available: bool = False
        self.tts_modules_loaded: bool = False

        self.database_manager: TTSDatabaseManager = TTSDatabaseManager(self.default_tts_config)
        self.text_processor: TTSTextProcessor = TTSTextProcessor(max_text_length=TTS_MAX_SEGMENT_LENGTH)
        self.audio_player: TTSAudioPlayer = TTSAudioPlayer(self.default_tts_config)
        self.engine: TTSEngine = TTSEngine(self.default_tts_config, self.database_manager, self.text_processor)

        self.executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=3)

        warnings.filterwarnings('ignore')
        logger.debug("TTSManager初始化完成")

    @property
    def tts_files_database(self) -> dict[str, dict[str, str]]:
        """获取TTS文件数据库"""
        return self.database_manager.tts_files_database

    @property
    def tts_synthesized_files(self) -> list[tuple[str, str]]:
        """获取已合成的音频文件列表"""
        return self.database_manager.tts_synthesized_files

    @tts_synthesized_files.setter
    def tts_synthesized_files(self, value: list[tuple[str, str]]) -> None:
        """设置已合成的音频文件列表"""
        self.database_manager.tts_synthesized_files = value

    @property
    def current_gpt_model(self) -> str | None:
        """获取当前GPT模型"""
        return self.database_manager.current_gpt_model

    @property
    def current_sovits_model(self) -> str | None:
        """获取当前SoVITS模型"""
        return self.database_manager.current_sovits_model

    @property
    def current_ref_audio(self) -> str | None:
        """获取当前参考音频"""
        return self.database_manager.current_ref_audio

    @property
    def current_ref_text(self) -> str | None:
        """获取当前参考文本"""
        return self.database_manager.current_ref_text

    @property
    def tts_synthesized_files_lock(self) -> threading.Lock:
        """获取合成文件列表锁"""
        return self.database_manager.tts_synthesized_files_lock

    @property
    def is_playing_audio(self) -> bool:
        """检查是否正在播放音频"""
        return self.audio_player.is_playing_audio

    @property
    def tts_modules(self) -> dict[str, Any] | None:
        return self.engine.tts_modules

    @tts_modules.setter
    def tts_modules(self, value: dict[str, Any] | None) -> None:
        self.engine.tts_modules = value

    @property
    def is_tts_synthesizing(self) -> bool:
        return self.engine.is_tts_synthesizing

    @is_tts_synthesizing.setter
    def is_tts_synthesizing(self, value: bool) -> None:
        self.engine.is_tts_synthesizing = value

    def init_tts_files_database(self) -> bool:
        return self.database_manager.init_tts_files_database()

    def load_tts_modules(self) -> tuple[bool, str]:
        success, message = self.engine.load_tts_modules()
        self.tts_modules_loaded = self.engine.tts_modules_loaded
        self.tts_available = self.engine.tts_available
        return success, message

    def synthesize_text(
        self,
        text: str,
        ref_audio_path: str,
        ref_text_path: str,
        auto_play: bool = True
    ) -> tuple[bool, str]:
        success, output_wav = self.engine.synthesize_text(text, ref_audio_path, ref_text_path, auto_play)

        if success and auto_play:
            def play_thread_func() -> None:
                self.audio_player.play_audio_file(output_wav)
            self.executor.submit(play_thread_func)

        return success, output_wav

    def _clean_text_for_tts(self, text: str) -> str:
        return self.text_processor.clean_text_for_tts(text)

    def should_use_segmented_synthesis(self, text: str) -> bool:
        return self.text_processor.should_use_segmented_synthesis(text)

    def synthesize_long_text_serial(
        self,
        text: str,
        ref_audio_path: str,
        ref_text_path: str
    ) -> tuple[bool, str]:
        try:
            cleaned_text = self.text_processor.clean_text_for_tts(text)
            segments = self.text_processor.split_text_by_numbered_sections(cleaned_text)

            if len(segments) == 1:
                return self.synthesize_text(text, ref_audio_path, ref_text_path, auto_play=False)

            segment_files: list[tuple[int, str]] = []

            for i, segment in enumerate(segments):
                success, result = self.engine.synthesize_text_with_retry(
                    segment, ref_audio_path, ref_text_path, max_retries=1
                )

                if success:
                    segment_files.append((i, result))
                    if i < len(segments) - 1:
                        time.sleep(0.3)
                else:
                    logger.error("第 %d 段合成失败: %s", i + 1, result)

            if not segment_files:
                return False, "所有分段合成失败"

            segment_files.sort(key=lambda x: x[0])
            audio_files_to_merge = [s[1] for s in segment_files]

            final_audio_path = self.audio_player.merge_audio_segments(audio_files_to_merge)

            if not final_audio_path:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                ref_audio_path_obj = Path(ref_audio_path)
                ref_audio_name = ref_audio_path_obj.stem
                output_path = Path(self.default_tts_config["output_path"])
                final_audio_path = output_path / f"{ref_audio_name}_merged_{timestamp}.wav"

                if audio_files_to_merge and Path(audio_files_to_merge[0]).exists():
                    import shutil
                    shutil.copy2(audio_files_to_merge[0], final_audio_path)

            if final_audio_path:
                for _, segment_file in segment_files:
                    try:
                        segment_path = Path(segment_file)
                        if segment_path.exists() and segment_file != final_audio_path:
                            segment_path.unlink()
                    except OSError as e:
                        logger.debug("删除分段文件失败 %s: %s", segment_file, str(e))

                return True, final_audio_path
            else:
                first_audio = segment_files[0][1]
                return True, first_audio

        except Exception as e:
            logger.error("分段合成失败: %s", str(e))
            traceback.print_exc()
            return False, f"分段合成失败: {str(e)}"

    def speak_text_intelligently(self, text: str) -> bool:
        try:
            ref_audio = self.get_current_model("audio")
            ref_text = self.get_current_model("text")

            if not ref_audio or not ref_text:
                logger.warning("无法语音播报：未选择参考音频或文本")
                return False

            if not self.tts_enabled:
                logger.warning("TTS功能未启用")
                return False

            if self.should_use_segmented_synthesis(text):
                logger.info("文本较长(%d字符)，使用分段串行合成", len(text))

                def async_synthesize() -> None:
                    try:
                        success, audio_path = self.synthesize_long_text_serial(
                            text, ref_audio, ref_text
                        )

                        if success and audio_path:
                            self.audio_player.play_audio_file(audio_path)
                        else:
                            logger.error("分段语音合成失败: %s", audio_path)
                            fallback_text = self.text_processor.clean_text_for_tts(text[:500])
                            if len(fallback_text) < 5:
                                fallback_text = "你好，我是小芸，很高兴为您服务"
                            fallback_success, _ = self.synthesize_text(
                                fallback_text, ref_audio, ref_text, auto_play=True
                            )
                    except Exception as e:
                        logger.error("分段语音合成异常: %s", str(e))

                self.executor.submit(async_synthesize)
                return True

            else:
                def async_synthesize() -> None:
                    try:
                        success, _ = self.synthesize_text(
                            text, ref_audio, ref_text, auto_play=True
                        )
                    except Exception as e:
                        logger.error("语音合成异常: %s", str(e))

                threading.Thread(target=async_synthesize, daemon=True).start()
                return True

        except Exception as e:
            logger.error("智能语音合成失败: %s", str(e))
            traceback.print_exc()
            return False

    def play_audio_file(self, audio_path: str) -> None:
        self.audio_player.play_audio_file(audio_path)

    def stop_current_audio_playback(self) -> bool:
        return self.audio_player.stop_current_audio_playback()

    def load_synthesized_files(self) -> list[tuple[str, str]]:
        return self.database_manager.load_synthesized_files()

    def set_current_model(self, model_type: str, filename: str) -> bool:
        return self.database_manager.set_current_model(model_type, filename)

    def get_current_model(self, model_type: str) -> str | None:
        return self.database_manager.get_current_model(model_type)

    def get_model_filename(self, model_type: str) -> str:
        return self.database_manager.get_model_filename(model_type)

    def cleanup(self) -> None:
        """
        清理TTS资源
        
        关闭线程池、停止音频播放并清理相关资源。
        建议在应用退出或TTS功能不再使用时调用。
        """
        logger.info("清理TTS资源")
        
        self.audio_player.cleanup()
        
        if hasattr(self.executor, 'shutdown'):
            self.executor.shutdown(wait=False)
            logger.info("TTS线程池已关闭")


class TaskManager:
    """
    任务管理器 - 负责连接管理、TTS管理和工具初始化
    
    作为应用程序的核心管理器，协调连接管理器、文件管理器、
    TTS管理器和工具类的工作。
    
    Attributes:
        project_root: 项目根目录路径
        scrcpy_path: scrcpy工具路径
        utils: 工具类实例
        connection_manager: 连接管理器实例
        file_manager: 文件管理器实例
        zhipu_client: 智谱AI客户端实例
        agent_executor: Agent执行器实例
        tts_manager: TTS管理器实例
        device_id: 当前连接的设备ID
        config: 当前连接配置
        is_connected: 是否已连接设备
        task_args: 任务参数对象
    """

    def __init__(self, project_root: str, scrcpy_path: str) -> None:
        """
        初始化任务管理器
        
        Args:
            project_root: 项目根目录路径
            scrcpy_path: scrcpy工具路径
        """
        self.project_root: str = project_root
        self.scrcpy_path: str = scrcpy_path

        self.utils: Utils = Utils()
        self.utils.enable_windows_color()

        self.connection_manager: ConnectionManager = ConnectionManager()
        self.file_manager: FileManager = FileManager()

        try:
            self.zhipu_client: ZhipuAI = ZhipuAI(api_key=ZHIPU_API_KEY)
            self.agent_executor: AgentExecutor = AgentExecutor()
            logger.debug("已初始化真实模块")
        except Exception as e:
            logger.error("初始化客户端失败: %s", str(e))
            raise

        self.tts_manager: TTSManager = TTSManager(project_root)

        try:
            self.tts_manager.init_tts_files_database()
        except Exception as e:
            logger.warning("TTS文件数据库初始化失败: %s", str(e))

        self.tts_manager.tts_enabled = False

        self.device_id: str | None = None
        self.config: dict[str, Any] = {}
        self.is_connected: bool = False
        self.task_args: Any = None

        self.file_manager.init_file_system()

        self._init_args()

        warnings.filterwarnings('ignore')

    def _init_args(self) -> None:
        class Args:
            def __init__(self) -> None:
                self.base_url: str = ZHIPU_API_BASE_URL
                self.model: str = ZHIPU_MODEL
                self.apikey: str = ZHIPU_API_KEY
                self.max_steps: int = 100
                self.device_id: str | None = None
                self.usb: bool = False
                self.wireless: bool = False
                self.ip: str | None = None
                self.port: str = "5555"
                self.setup: bool = False
                self.quiet: bool = False
                self.lang: str = "cn"
                self.task: str | None = None

        self.task_args = Args()

    def set_device_type(self, device_type: str) -> None:
        self.connection_manager.set_device_type(device_type)

    def check_initial_connection(self) -> None:
        self.config = self.connection_manager.load_connection_config()

        if self.config.get("connection_type") == "usb" and self.config.get("usb_device_id"):
            self.try_connect()
        elif self.config.get("connection_type") == "wireless" and self.config.get("wireless_ip"):
            self.try_connect()

    def try_connect(self) -> None:
        success, device_id, message = self.connection_manager.connect_to_device(self.config)

        if success:
            self.is_connected = True
            self.device_id = device_id
            self.task_args.device_id = device_id
            logger.info("%s", message)
        else:
            logger.error("连接失败: %s", message)

    def connect_device(self, config: dict[str, Any]) -> tuple[bool, str | None, str]:
        self.config = config
        self.connection_manager.save_connection_config(config)

        success, device_id, message = self.connection_manager.connect_to_device(config)

        if success:
            self.is_connected = True
            self.device_id = device_id
            self.task_args.device_id = device_id

        return success, device_id, message

    def setup_connection(self) -> None:
        logger.info("请在连接管理页面设置连接")

    def detect_devices(self, device_type: str = "android") -> list[str]:
        self.connection_manager.set_device_type(device_type)
        return self.connection_manager.get_available_devices()

    def disconnect_device(self) -> None:
        self.is_connected = False
        self.device_id = None
        self.task_args.device_id = None

    def preload_tts_modules(self) -> bool:
        logger.debug("预加载TTS模块")

        try:
            success, message = self.tts_manager.load_tts_modules()
            if success:
                logger.debug("TTS模块预加载成功")
                self.tts_manager.tts_enabled = True
                return True
            else:
                logger.warning("TTS模块预加载失败: %s", message)
                self.tts_manager.tts_enabled = False
                return False
        except Exception as e:
            logger.error("TTS预加载异常: %s", str(e))
            self.tts_manager.tts_enabled = False
            return False

    def tts_synthesize_text(
        self,
        text: str,
        ref_audio_path: str,
        ref_text_path: str,
        auto_play: bool = True
    ) -> tuple[bool, str]:
        return self.tts_manager.synthesize_text(text, ref_audio_path, ref_text_path, auto_play)

    def play_audio_file(self, audio_path: str) -> None:
        self.tts_manager.play_audio_file(audio_path)

    def stop_audio_playback(self) -> bool:
        return self.tts_manager.stop_current_audio_playback()

    def cleanup(self) -> None:
        logger.info("正在清理任务管理器资源")

        self.stop_audio_playback()

        if hasattr(self.tts_manager, 'cleanup'):
            self.tts_manager.cleanup()
