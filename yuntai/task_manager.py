"""
TaskManager - 任务调度和执行模块
负责所有后台任务的调度、执行和管理
"""

import os
import sys
import threading
import time
import datetime
import traceback
from typing import Optional, Dict, Any, Tuple, List, Callable
import warnings
import logging
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_TTS_CONFIG_KEY = "default_tts_config"
SIMILARITY_THRESHOLD = 0.6
MIN_CHINESE_RATIO = 0.3
MAX_LIST_LENGTH = 50
AUDIO_CHUNK_SIZE = 1024
AUDIO_FORMAT_WIDTH = 2
AUDIO_CHANNELS = 1
DEFAULT_SAMPLE_RATE = 22050

# 第三方库
from zhipuai import ZhipuAI

# 项目模块
from yuntai.connection_manager import ConnectionManager
from yuntai.file_manager import FileManager
from yuntai.task_recognizer import TaskRecognizer
from yuntai.agent_executor import AgentExecutor
from yuntai.utils import Utils
from yuntai.reply_manager import SmartContinuousReplyManager

# 导入新的管理器模块
from yuntai.managers import (
    TTSDatabaseManager,
    TTSTextProcessor,
    TTSEngine,
    TTSAudioPlayer,
    TaskLogicHandler
)

# 使用新的统一配置
from .config import (
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
        """
        初始化TTS管理器

        Args:
            project_root: 项目根目录路径
        """
        self.project_root = project_root

        # 默认TTS配置
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

        # 状态变量
        self.tts_enabled = False
        self.tts_available = False
        self.tts_modules_loaded = False

        # 初始化各个子模块
        self.database_manager = TTSDatabaseManager(self.default_tts_config)
        self.text_processor = TTSTextProcessor(max_text_length=TTS_MAX_SEGMENT_LENGTH)
        self.audio_player = TTSAudioPlayer(self.default_tts_config)
        self.engine = TTSEngine(self.default_tts_config, self.database_manager, self.text_processor)

        # 线程池执行器
        self.executor = ThreadPoolExecutor(max_workers=3)

        # 过滤冗余警告
        warnings.filterwarnings('ignore')

    # 向后兼容性：提供属性代理
    @property
    def tts_files_database(self):
        """访问TTS文件数据库"""
        return self.database_manager.tts_files_database

    @property
    def tts_synthesized_files(self):
        """访问已合成文件列表"""
        return self.database_manager.tts_synthesized_files

    @tts_synthesized_files.setter
    def tts_synthesized_files(self, value):
        """设置已合成文件列表"""
        self.database_manager.tts_synthesized_files = value

    @property
    def current_gpt_model(self):
        """访问当前GPT模型"""
        return self.database_manager.current_gpt_model

    @property
    def current_sovits_model(self):
        """访问当前SoVITS模型"""
        return self.database_manager.current_sovits_model

    @property
    def current_ref_audio(self):
        """访问当前参考音频"""
        return self.database_manager.current_ref_audio

    @property
    def current_ref_text(self):
        """访问当前参考文本"""
        return self.database_manager.current_ref_text

    @property
    def tts_synthesized_files_lock(self):
        """访问已合成文件列表锁"""
        return self.database_manager.tts_synthesized_files_lock

    @property
    def is_playing_audio(self):
        """访问音频播放状态"""
        return self.audio_player.is_playing_audio

    @property
    def tts_modules(self):
        """访问TTS模块"""
        return self.engine.tts_modules

    @tts_modules.setter
    def tts_modules(self, value):
        """设置TTS模块"""
        self.engine.tts_modules = value

    @property
    def is_tts_synthesizing(self):
        """访问TTS合成状态"""
        return self.engine.is_tts_synthesizing

    @is_tts_synthesizing.setter
    def is_tts_synthesizing(self, value):
        """设置TTS合成状态"""
        self.engine.is_tts_synthesizing = value

    def init_tts_files_database(self) -> bool:
        """初始化TTS文件数据库"""
        return self.database_manager.init_tts_files_database()

    def load_tts_modules(self) -> Tuple[bool, str]:
        """加载TTS模块"""
        success, message = self.engine.load_tts_modules()

        # 同步状态
        self.tts_modules_loaded = self.engine.tts_modules_loaded
        self.tts_available = self.engine.tts_available

        return success, message

    def synthesize_text(self, text: str, ref_audio_path: str, ref_text_path: str,
                        auto_play: bool = True) -> Tuple[bool, str]:
        """合成文本为语音"""
        success, output_wav = self.engine.synthesize_text(text, ref_audio_path, ref_text_path, auto_play)

        # 自动播放
        if success and auto_play:
            def play_thread_func():
                self.audio_player.play_audio_file(output_wav)
            self.executor.submit(play_thread_func)

        return success, output_wav

    def _clean_text_for_tts(self, text: str) -> str:
        """清理文本"""
        return self.text_processor.clean_text_for_tts(text)

    def should_use_segmented_synthesis(self, text: str) -> bool:
        """判断是否应该使用分段合成"""
        return self.text_processor.should_use_segmented_synthesis(text)

    def synthesize_long_text_serial(self, text: str, ref_audio_path: str, ref_text_path: str) -> tuple[bool, str]:
        """分段串行合成长文本语音"""
        try:
            # 清理文本
            cleaned_text = self.text_processor.clean_text_for_tts(text)

            # 分段文本
            segments = self.text_processor.split_text_by_numbered_sections(cleaned_text)

            if len(segments) == 1:
                # 直接合成
                return self.synthesize_text(text, ref_audio_path, ref_text_path, auto_play=False)

            # 串行合成每个分段
            segment_files = []

            for i, segment in enumerate(segments):
                # 使用带重试的合成
                success, result = self.engine.synthesize_text_with_retry(
                    segment, ref_audio_path, ref_text_path, max_retries=1
                )

                if success:
                    segment_files.append((i, result))

                    # 添加延迟避免冲突
                    if i < len(segments) - 1:
                        time.sleep(0.3)  # 300ms延迟
                else:
                    print(f"❌ 第 {i + 1} 段合成失败: {result}")
                    # 尝试用更短的文本重试
                    if len(segment) > 100:
                        short_segment = segment[:100] + "..."
                        retry_success, retry_result = self.engine.synthesize_text_with_retry(
                            short_segment, ref_audio_path, ref_text_path
                        )
                        if retry_success:
                            segment_files.append((i, retry_result))
                            print(f"🔄 第 {i + 1} 段重试成功（截断版）")

            if not segment_files:
                return False, "所有分段合成失败"

            # 按索引排序
            segment_files.sort(key=lambda x: x[0])

            # 修复：只传递音频文件列表，不传递ref_audio_path
            audio_files_to_merge = [s[1] for s in segment_files]

            # 合并音频文件
            final_audio_path = self.audio_player.merge_audio_segments(audio_files_to_merge)

            # 如果合并失败，尝试使用更简单的合并方式
            if not final_audio_path:
                # 创建新的合并文件名（与普通合成格式一致）
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                ref_audio_name = os.path.splitext(os.path.basename(ref_audio_path))[0]
                final_audio_path = os.path.join(
                    self.default_tts_config["output_path"],
                    f"{ref_audio_name}_merged_{timestamp}.wav"
                )

                # 简单的音频合并（只复制第一个文件）
                if audio_files_to_merge and os.path.exists(audio_files_to_merge[0]):
                    import shutil
                    shutil.copy2(audio_files_to_merge[0], final_audio_path)
                    print(f"⚠️  使用简单合并方式，只保留第一段音频")

            if final_audio_path:
                # 清理临时文件
                for _, segment_file in segment_files:
                    try:
                        if os.path.exists(segment_file) and segment_file != final_audio_path:
                            os.remove(segment_file)
                    except:
                        pass

                return True, final_audio_path
            else:
                # 如果合并失败，至少播放第一段
                first_audio = segment_files[0][1]
                print(f"⚠️  音频合并失败，将播放第一段音频")
                return True, first_audio

        except Exception as e:
            print(f"❌ 分段合成失败: {e}")
            import traceback
            traceback.print_exc()
            return False, f"分段合成失败: {str(e)}"

    def speak_text_intelligently(self, text: str) -> bool:
        """智能语音合成（自动判断是否分段）"""
        try:
            # 检查是否有参考音频和文本
            ref_audio = self.get_current_model("audio")
            ref_text = self.get_current_model("text")

            if not ref_audio or not ref_text:
                print("\n⚠️  无法语音播报：未选择参考音频或文本")
                return False

            # 检查TTS是否启用
            if not self.tts_enabled:
                print("⚠️  TTS功能未启用")
                return False

            # 判断是否使用分段合成
            if self.should_use_segmented_synthesis(text):
                print(f"📝 文本较长({len(text)}字符)，使用分段串行合成...")

                def async_synthesize():
                    try:
                        # 使用串行合成
                        success, audio_path = self.synthesize_long_text_serial(
                            text, ref_audio, ref_text
                        )

                        if success and audio_path:
                            # 播放合并后的音频
                            self.audio_player.play_audio_file(audio_path)
                        else:
                            logger.error(f"分段语音合成失败: {audio_path}")

                            # 分段合成失败，尝试普通合成
                            print("🔄 分段失败，尝试普通合成...")
                            # 使用清理后的文本，确保质量
                            fallback_text = self.text_processor.clean_text_for_tts(text[:500])
                            if len(fallback_text) < 5 or len([c for c in fallback_text if '\u4e00' <= c <= '\u9fff']) < 2:
                                fallback_text = "你好，我是小芸，很高兴为您服务"
                            fallback_success, _ = self.synthesize_text(
                                fallback_text, ref_audio, ref_text, auto_play=True
                            )
                            if fallback_success:
                                print("\n")
                    except Exception as e:
                        print(f"❌ 分段语音合成异常: {e}")

                # 异步执行分段合成
                self.executor.submit(async_synthesize)
                return True

            else:
                def async_synthesize():
                    try:
                        success, _ = self.synthesize_text(
                            text, ref_audio, ref_text, auto_play=True
                        )
                        if success:
                            print("\n")
                    except Exception as e:
                        print(f"❌ 语音合成异常: {e}\n")

                # 异步执行普通合成
                threading.Thread(target=async_synthesize, daemon=True).start()
                return True

        except Exception as e:
            print(f"❌ 智能语音合成失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def play_audio_file(self, audio_path: str):
        """播放音频文件"""
        self.audio_player.play_audio_file(audio_path)

    def stop_current_audio_playback(self) -> bool:
        """停止当前正在播放的音频"""
        return self.audio_player.stop_current_audio_playback()

    def load_synthesized_files(self) -> List[Tuple[str, str]]:
        """加载已合成音频文件"""
        return self.database_manager.load_synthesized_files()

    def set_current_model(self, model_type: str, filename: str) -> bool:
        """设置当前选中的模型"""
        return self.database_manager.set_current_model(model_type, filename)

    def get_current_model(self, model_type: str) -> Optional[str]:
        """获取当前选中的模型"""
        return self.database_manager.get_current_model(model_type)

    def get_model_filename(self, model_type: str) -> str:
        """获取当前选中模型的文件名"""
        return self.database_manager.get_model_filename(model_type)

    def cleanup(self):
        """清理TTS资源"""
        print("🧹 清理TTS资源...")
        self.audio_player.cleanup()


class TaskManager:
    """任务管理器 - 负责所有后台任务的调度和执行"""

    def __init__(self, project_root: str, scrcpy_path: str):
        self.project_root = project_root
        self.scrcpy_path = scrcpy_path

        # 初始化工具和模块
        self.utils = Utils()
        self.utils.enable_windows_color()

        # 创建模块实例
        self.connection_manager = ConnectionManager()
        self.file_manager = FileManager()

        # 初始化智谱AI客户端
        try:
            self.zhipu_client = ZhipuAI(api_key=ZHIPU_API_KEY)
            self.task_recognizer = TaskRecognizer(self.zhipu_client)
            self.agent_executor = AgentExecutor()
            print("✅ 已初始化真实模块")
        except Exception as e:
            print(f"❌ 初始化客户端失败: {e}")
            raise

        # 初始化TTS管理器
        self.tts_manager = TTSManager(project_root)

        # 初始化TTS文件数据库
        try:
            self.tts_manager.init_tts_files_database()
        except Exception as e:
            print(f"⚠️  TTS文件数据库初始化失败: {e}")

        # 默认TTS关闭
        self.tts_manager.tts_enabled = False

        # 初始化任务逻辑处理器
        self.task_logic_handler = TaskLogicHandler(
            self.zhipu_client,
            self.file_manager,
            self.tts_manager
        )

        # 状态变量
        self.device_id = None
        self.config = {}
        self.is_connected = False
        self.task_args = None

        # 初始化文件系统
        self.file_manager.init_file_system()

        # 初始化命令行参数
        self._init_args()

        # 过滤冗余警告
        warnings.filterwarnings('ignore')

    def _init_args(self):
        """初始化命令行参数"""

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
        """设置设备类型"""
        self.connection_manager.set_device_type(device_type)
        print(f"📱 TaskManager设备类型已切换为: {device_type}")

    # ========== 连接管理方法 ==========

    def check_initial_connection(self):
        """检查初始连接"""
        self.config = self.connection_manager.load_connection_config()

        if self.config.get("connection_type") == "usb" and self.config.get("usb_device_id"):
            self.try_connect()
        elif self.config.get("connection_type") == "wireless" and self.config.get("wireless_ip"):
            self.try_connect()

    def try_connect(self):
        """尝试连接设备"""
        success, device_id, message = self.connection_manager.connect_to_device(self.config)

        if success:
            self.is_connected = True
            self.device_id = device_id
            self.task_args.device_id = device_id
            print(f"✅ {message}")
        else:
            print(f"❌ 连接失败: {message}")

    def connect_device(self, config: Dict[str, Any]) -> Tuple[bool, Optional[str], str]:
        """连接设备"""
        self.config = config
        self.connection_manager.save_connection_config(config)

        success, device_id, message = self.connection_manager.connect_to_device(config)

        if success:
            self.is_connected = True
            self.device_id = device_id
            self.task_args.device_id = device_id

        return success, device_id, message

    def setup_connection(self):
        """设置连接"""
        config = self.connection_manager.interactive_setup_connection()
        success, device_id, message = self.connection_manager.connect_to_device(config)

        if success:
            self.is_connected = True
            self.device_id = device_id
            self.task_args.device_id = device_id
            print(f"✅ 重新连接成功: {message}")
        else:
            print(f"❌ 重新连接失败: {message}")

    def detect_devices(self, device_type: str = "android") -> List[str]:
        """检测可用设备"""
        self.connection_manager.set_device_type(device_type)
        return self.connection_manager.get_available_devices()

    def disconnect_device(self):
        """断开设备连接"""
        self.is_connected = False
        self.device_id = None
        self.task_args.device_id = None

    # ========== TTS管理方法 ==========

    def preload_tts_modules(self) -> bool:
        """预加载TTS模块"""
        print("📦 预加载TTS模块...")

        try:
            success, message = self.tts_manager.load_tts_modules()
            if success:
                print("✅ TTS模块预加载成功")
                # 设置默认TTS为开启状态
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
        """TTS合成文本"""
        return self.tts_manager.synthesize_text(text, ref_audio_path, ref_text_path, auto_play)

    def play_audio_file(self, audio_path: str):
        """播放音频文件"""
        self.tts_manager.play_audio_file(audio_path)

    def stop_audio_playback(self) -> bool:
        """停止音频播放"""
        return self.tts_manager.stop_current_audio_playback()

    # ========== 任务调度方法 ==========

    def dispatch_task(self, user_input: str, args, device_id: Optional[str]) -> Optional[str]:
        """
        任务分发核心：识别任务类型并调用对应处理函数
        """
        print(f"\n🤖 正在分析任务意图...\n")

        # 检查是否是空输入但有附件的情况（通过GUI处理，这里不应该进入）
        if not user_input or user_input.strip() == "":
            # 可能是纯附件的情况，让GUI处理
            return None

        # 0. 特别处理：单个字母的快捷键
        if len(user_input.strip()) == 1:
            letter = user_input.strip().lower()
            if letter in SHORTCUTS:
                print(f"📋 识别为快捷键: {letter} -> {SHORTCUTS[letter]}\n")
                return self._handle_basic_operation(SHORTCUTS[letter], args, device_id)

        # 1. 使用ZHIPU_JUDGEMENT_MODEL进行任务识别
        task_info = self.task_recognizer.recognize_task_intent(user_input)
        task_type = task_info["task_type"]
        target_app = task_info["target_app"]
        target_object = task_info["target_object"]
        is_auto = task_info["is_auto"]

        print(f"📋 识别结果：任务类型={task_type}, APP={target_app}, 对象={target_object}, 持续={is_auto}\n")

        # 2. 如果ZHIPU_CHAT_MODEL没有提取到APP和对象，尝试简单提取
        if task_type in ["single_reply", "continuous_reply", "basic_operation", "complex_operation"] and not target_app:
            target_app = self.task_recognizer.extract_target_app_simple(user_input)

        if task_type in ["single_reply", "continuous_reply"] and not target_object:
            target_object = self.task_recognizer.extract_chat_object_simple(user_input)

        # 3. 根据任务类型分发
        result = None

        if task_type == "free_chat":
            result = self._handle_free_chat(user_input)
            return result

        elif task_type == "basic_operation":
            if not target_app:
                # 如果还是没识别到APP，使用用户原始输入
                result = self._handle_basic_operation(user_input, args, device_id)
            else:
                # 构造打开APP的指令
                task = f"打开{target_app}"
                result = self._handle_basic_operation(task, args, device_id)

        elif task_type == "single_reply":
            if not target_app or not target_object:
                result = f"❌ 无法识别APP或聊天对象，请确保指令格式正确"
            else:
                result = self._handle_single_reply(user_input, args, target_app, target_object, device_id)

        elif task_type == "continuous_reply":
            if not target_app or not target_object:
                result = f"❌ 无法识别APP或聊天对象，请确保指令格式正确"

            # 检查设备连接
            if not device_id:
                result = f"❌ 设备未连接，请先连接设备"

            # 重要：这里返回一个特殊标记，让控制器知道这是持续回复模式
            # 控制器会启动持续回复线程
            result = f"🔄CONTINUOUS_REPLY:{target_app}:{target_object}"

        elif task_type == "complex_operation":
            # 复杂操作直接使用用户原始输入
            result = self._handle_complex_operation(user_input, args, device_id)

        else:
            # 默认当作复杂操作处理
            print(f"⚠️  无法识别的任务类型，当作复杂操作处理")
            result = self._handle_complex_operation(user_input, args, device_id)

        return result

    # ========== 具体任务处理方法 ==========

    def _handle_free_chat(self, task: str) -> str:
        """处理自由聊天"""
        return self.task_logic_handler.handle_free_chat(task, ZHIPU_CHAT_MODEL)

    def _handle_basic_operation(self, task: str, args, device_id: str) -> str:
        """处理基础操作"""
        return self.task_logic_handler.handle_basic_operation(task, args, device_id, self.agent_executor)

    def _handle_single_reply(self, task: str, args, target_app: str, target_object: str,
                             device_id: str) -> str:
        """处理单次回复"""
        return self.task_logic_handler.handle_single_reply(task, args, target_app, target_object, device_id, ZHIPU_CHAT_MODEL)

    def _handle_continuous_reply(self, args, target_app: str, target_object: str,
                                 device_id: str) -> str:
        """处理持续回复"""
        return self.task_logic_handler.handle_continuous_reply(args, target_app, target_object, device_id)

    def _handle_complex_operation(self, task: str, args, device_id: str) -> str:
        """处理复杂操作"""
        return self.task_logic_handler.handle_complex_operation(task, args, device_id, self.agent_executor)

    def _start_continuous_reply_thread(self, args, target_app: str, target_object: str,
                                       device_id: str):
        """启动持续回复线程"""

        def continuous_thread():
            try:
                # 先打开应用
                print(f"📱 正在打开 {target_app}...\n")
                open_result = self.dispatch_task(
                    f"打开{target_app}", args, device_id
                )
                print(f"📱 打开应用结果: {open_result}\n")

                # 等待应用打开
                time.sleep(3)

                # 使用handle_continuous_reply处理持续回复
                result = self._handle_continuous_reply(args, target_app, target_object, device_id)

                print(f"\n🎉 持续回复模式结束: {result}\n")

            except Exception as e:
                print(f"\n❌ 持续回复错误：{str(e)}\n")
                traceback.print_exc()

        thread = threading.Thread(target=continuous_thread)
        thread.daemon = True
        thread.start()

    # ========== 资源管理方法 ==========

    def cleanup(self):
        """清理资源"""
        print("🧹 正在清理任务管理器资源...")

        # 停止所有音频播放
        self.stop_audio_playback()

        # 清理TTS资源
        if hasattr(self.tts_manager, 'cleanup'):
            self.tts_manager.cleanup()
