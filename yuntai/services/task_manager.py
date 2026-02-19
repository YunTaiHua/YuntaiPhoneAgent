"""
TaskManager - 任务调度和执行模块（重构版）
负责连接管理、TTS管理和工具初始化
任务分发逻辑已迁移到 TaskChain
"""

import os
import threading
import time
import datetime
import traceback
from typing import Optional, Dict, Any, Tuple, List
import warnings
import logging
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

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


class TTSManager:
    """TTS管理器：统一管理所有TTS相关功能"""

    def __init__(self, project_root: str):
        self.project_root = project_root

        self.default_tts_config = {
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

        self.tts_enabled = False
        self.tts_available = False
        self.tts_modules_loaded = False

        self.database_manager = TTSDatabaseManager(self.default_tts_config)
        self.text_processor = TTSTextProcessor(max_text_length=TTS_MAX_SEGMENT_LENGTH)
        self.audio_player = TTSAudioPlayer(self.default_tts_config)
        self.engine = TTSEngine(self.default_tts_config, self.database_manager, self.text_processor)

        self.executor = ThreadPoolExecutor(max_workers=3)

        warnings.filterwarnings('ignore')

    @property
    def tts_files_database(self):
        return self.database_manager.tts_files_database

    @property
    def tts_synthesized_files(self):
        return self.database_manager.tts_synthesized_files

    @tts_synthesized_files.setter
    def tts_synthesized_files(self, value):
        self.database_manager.tts_synthesized_files = value

    @property
    def current_gpt_model(self):
        return self.database_manager.current_gpt_model

    @property
    def current_sovits_model(self):
        return self.database_manager.current_sovits_model

    @property
    def current_ref_audio(self):
        return self.database_manager.current_ref_audio

    @property
    def current_ref_text(self):
        return self.database_manager.current_ref_text

    @property
    def tts_synthesized_files_lock(self):
        return self.database_manager.tts_synthesized_files_lock

    @property
    def is_playing_audio(self):
        return self.audio_player.is_playing_audio

    @property
    def tts_modules(self):
        return self.engine.tts_modules

    @tts_modules.setter
    def tts_modules(self, value):
        self.engine.tts_modules = value

    @property
    def is_tts_synthesizing(self):
        return self.engine.is_tts_synthesizing

    @is_tts_synthesizing.setter
    def is_tts_synthesizing(self, value):
        self.engine.is_tts_synthesizing = value

    def init_tts_files_database(self) -> bool:
        return self.database_manager.init_tts_files_database()

    def load_tts_modules(self) -> Tuple[bool, str]:
        success, message = self.engine.load_tts_modules()
        self.tts_modules_loaded = self.engine.tts_modules_loaded
        self.tts_available = self.engine.tts_available
        return success, message

    def synthesize_text(self, text: str, ref_audio_path: str, ref_text_path: str,
                        auto_play: bool = True) -> Tuple[bool, str]:
        success, output_wav = self.engine.synthesize_text(text, ref_audio_path, ref_text_path, auto_play)

        if success and auto_play:
            def play_thread_func():
                self.audio_player.play_audio_file(output_wav)
            self.executor.submit(play_thread_func)

        return success, output_wav

    def _clean_text_for_tts(self, text: str) -> str:
        return self.text_processor.clean_text_for_tts(text)

    def should_use_segmented_synthesis(self, text: str) -> bool:
        return self.text_processor.should_use_segmented_synthesis(text)

    def synthesize_long_text_serial(self, text: str, ref_audio_path: str, ref_text_path: str) -> tuple[bool, str]:
        try:
            cleaned_text = self.text_processor.clean_text_for_tts(text)
            segments = self.text_processor.split_text_by_numbered_sections(cleaned_text)

            if len(segments) == 1:
                return self.synthesize_text(text, ref_audio_path, ref_text_path, auto_play=False)

            segment_files = []

            for i, segment in enumerate(segments):
                success, result = self.engine.synthesize_text_with_retry(
                    segment, ref_audio_path, ref_text_path, max_retries=1
                )

                if success:
                    segment_files.append((i, result))
                    if i < len(segments) - 1:
                        time.sleep(0.3)
                else:
                    print(f"❌ 第 {i + 1} 段合成失败: {result}")

            if not segment_files:
                return False, "所有分段合成失败"

            segment_files.sort(key=lambda x: x[0])
            audio_files_to_merge = [s[1] for s in segment_files]

            final_audio_path = self.audio_player.merge_audio_segments(audio_files_to_merge)

            if not final_audio_path:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                ref_audio_name = os.path.splitext(os.path.basename(ref_audio_path))[0]
                final_audio_path = os.path.join(
                    self.default_tts_config["output_path"],
                    f"{ref_audio_name}_merged_{timestamp}.wav"
                )

                if audio_files_to_merge and os.path.exists(audio_files_to_merge[0]):
                    import shutil
                    shutil.copy2(audio_files_to_merge[0], final_audio_path)

            if final_audio_path:
                for _, segment_file in segment_files:
                    try:
                        if os.path.exists(segment_file) and segment_file != final_audio_path:
                            os.remove(segment_file)
                    except:
                        pass

                return True, final_audio_path
            else:
                first_audio = segment_files[0][1]
                return True, first_audio

        except Exception as e:
            print(f"❌ 分段合成失败: {e}")
            traceback.print_exc()
            return False, f"分段合成失败: {str(e)}"

    def speak_text_intelligently(self, text: str) -> bool:
        try:
            ref_audio = self.get_current_model("audio")
            ref_text = self.get_current_model("text")

            if not ref_audio or not ref_text:
                print("\n⚠️  无法语音播报：未选择参考音频或文本")
                return False

            if not self.tts_enabled:
                print("⚠️  TTS功能未启用")
                return False

            if self.should_use_segmented_synthesis(text):
                print(f"📝 文本较长({len(text)}字符)，使用分段串行合成...")

                def async_synthesize():
                    try:
                        success, audio_path = self.synthesize_long_text_serial(
                            text, ref_audio, ref_text
                        )

                        if success and audio_path:
                            self.audio_player.play_audio_file(audio_path)
                        else:
                            logger.error(f"分段语音合成失败: {audio_path}")
                            fallback_text = self.text_processor.clean_text_for_tts(text[:500])
                            if len(fallback_text) < 5:
                                fallback_text = "你好，我是小芸，很高兴为您服务"
                            fallback_success, _ = self.synthesize_text(
                                fallback_text, ref_audio, ref_text, auto_play=True
                            )
                    except Exception as e:
                        print(f"❌ 分段语音合成异常: {e}")

                self.executor.submit(async_synthesize)
                return True

            else:
                def async_synthesize():
                    try:
                        success, _ = self.synthesize_text(
                            text, ref_audio, ref_text, auto_play=True
                        )
                    except Exception as e:
                        print(f"❌ 语音合成异常: {e}")

                threading.Thread(target=async_synthesize, daemon=True).start()
                return True

        except Exception as e:
            print(f"❌ 智能语音合成失败: {e}")
            traceback.print_exc()
            return False

    def play_audio_file(self, audio_path: str):
        self.audio_player.play_audio_file(audio_path)

    def stop_current_audio_playback(self) -> bool:
        return self.audio_player.stop_current_audio_playback()

    def load_synthesized_files(self) -> List[Tuple[str, str]]:
        return self.database_manager.load_synthesized_files()

    def set_current_model(self, model_type: str, filename: str) -> bool:
        return self.database_manager.set_current_model(model_type, filename)

    def get_current_model(self, model_type: str) -> Optional[str]:
        return self.database_manager.get_current_model(model_type)

    def get_model_filename(self, model_type: str) -> str:
        return self.database_manager.get_model_filename(model_type)

    def cleanup(self):
        print("🧹 清理TTS资源...")
        self.audio_player.cleanup()


class TaskManager:
    """任务管理器 - 负责连接管理、TTS管理和工具初始化"""

    def __init__(self, project_root: str, scrcpy_path: str):
        self.project_root = project_root
        self.scrcpy_path = scrcpy_path

        self.utils = Utils()
        self.utils.enable_windows_color()

        self.connection_manager = ConnectionManager()
        self.file_manager = FileManager()

        try:
            self.zhipu_client = ZhipuAI(api_key=ZHIPU_API_KEY)
            self.agent_executor = AgentExecutor()
            print("✅ 已初始化真实模块")
        except Exception as e:
            print(f"❌ 初始化客户端失败: {e}")
            raise

        self.tts_manager = TTSManager(project_root)

        try:
            self.tts_manager.init_tts_files_database()
        except Exception as e:
            print(f"⚠️  TTS文件数据库初始化失败: {e}")

        self.tts_manager.tts_enabled = False

        self.device_id = None
        self.config = {}
        self.is_connected = False
        self.task_args = None

        self.file_manager.init_file_system()

        self._init_args()

        warnings.filterwarnings('ignore')

    def _init_args(self):
        class Args:
            def __init__(self):
                self.base_url = ZHIPU_API_BASE_URL
                self.model = ZHIPU_MODEL
                self.apikey = ZHIPU_API_KEY
                self.max_steps = 100
                self.device_id = None
                self.usb = False
                self.wireless = False
                self.ip = None
                self.port = "5555"
                self.setup = False
                self.quiet = False
                self.lang = "cn"
                self.task = None

        self.task_args = Args()

    def set_device_type(self, device_type: str):
        self.connection_manager.set_device_type(device_type)

    def check_initial_connection(self):
        self.config = self.connection_manager.load_connection_config()

        if self.config.get("connection_type") == "usb" and self.config.get("usb_device_id"):
            self.try_connect()
        elif self.config.get("connection_type") == "wireless" and self.config.get("wireless_ip"):
            self.try_connect()

    def try_connect(self):
        success, device_id, message = self.connection_manager.connect_to_device(self.config)

        if success:
            self.is_connected = True
            self.device_id = device_id
            self.task_args.device_id = device_id
            print(f"✅ {message}")
        else:
            print(f"❌ 连接失败: {message}")

    def connect_device(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str], str]:
        self.config = config
        self.connection_manager.save_connection_config(config)

        success, device_id, message = self.connection_manager.connect_to_device(config)

        if success:
            self.is_connected = True
            self.device_id = device_id
            self.task_args.device_id = device_id

        return success, device_id, message

    def setup_connection(self):
        print("请在连接管理页面设置连接")


    def detect_devices(self, device_type: str = "android") -> List[str]:
        self.connection_manager.set_device_type(device_type)
        return self.connection_manager.get_available_devices()

    def disconnect_device(self):
        self.is_connected = False
        self.device_id = None
        self.task_args.device_id = None

    def preload_tts_modules(self) -> bool:
        print("📦 预加载TTS模块...")

        try:
            success, message = self.tts_manager.load_tts_modules()
            if success:
                print("✅ TTS模块预加载成功")
                self.tts_manager.tts_enabled = True
                return True
            else:
                print(f"⚠️ TTS模块预加载失败: {message}")
                self.tts_manager.tts_enabled = False
                return False
        except Exception as e:
            print(f"❌ TTS预加载异常: {e}")
            self.tts_manager.tts_enabled = False
            return False

    def tts_synthesize_text(self, text: str, ref_audio_path: str, ref_text_path: str,
                            auto_play: bool = True) -> Tuple[bool, str]:
        return self.tts_manager.synthesize_text(text, ref_audio_path, ref_text_path, auto_play)

    def play_audio_file(self, audio_path: str):
        self.tts_manager.play_audio_file(audio_path)

    def stop_audio_playback(self) -> bool:
        return self.tts_manager.stop_current_audio_playback()

    def cleanup(self):
        print("🧹 正在清理任务管理器资源...")

        self.stop_audio_playback()

        if hasattr(self.tts_manager, 'cleanup'):
            self.tts_manager.cleanup()
