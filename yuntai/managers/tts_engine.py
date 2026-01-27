"""
TTS引擎 - 负责GPT-SoVITS模型加载、环境设置和核心合成调用
"""

import os
import sys
import time
import threading
import datetime
import logging
from typing import Tuple, Dict, Any
import torch
import soundfile as sf
import warnings

logger = logging.getLogger(__name__)


class TTSEngine:
    """TTS引擎 - 核心合成功能"""

    def __init__(self, default_tts_config: dict, database_manager, text_processor):
        """
        初始化TTS引擎

        Args:
            default_tts_config: 默认TTS配置
            database_manager: 数据库管理器实例
            text_processor: 文本处理器实例
        """
        self.default_tts_config = default_tts_config
        self.database_manager = database_manager
        self.text_processor = text_processor

        # 使用统一配置
        self.bert_model_path = default_tts_config.get("bert_model_path")
        self.hubert_model_path = default_tts_config.get("hubert_model_path")

        # 状态变量
        self.tts_enabled = False
        self.tts_available = False
        self.tts_modules_loaded = False

        # 线程安全的状态变量
        self.is_tts_synthesizing = False
        self.is_tts_synthesizing_lock = threading.Lock()

        # TTS模块
        self.tts_modules: Dict[str, Any] = {}

        # 过滤冗余警告
        warnings.filterwarnings('ignore')

    def load_tts_modules(self) -> Tuple[bool, str]:
        """加载TTS模块"""
        if self.tts_modules_loaded:
            return True, "模块已加载"

        try:
            print("📦 正在加载TTS模块...")

            # 设置环境变量，减少冗余输出
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TQDM_DISABLE"] = "1"  # 禁用tqdm进度条
            os.environ["TOKENIZERS_PARALLELISM"] = "false"

            # 抑制transformers的日志
            import logging
            logging.getLogger("transformers").setLevel(logging.ERROR)
            logging.getLogger("torch").setLevel(logging.WARNING)

            # 设置模型路径
            if os.path.exists(self.bert_model_path):
                os.environ["bert_path"] = self.bert_model_path
                print(f"✅ BERT模型路径已设置")

            if os.path.exists(self.hubert_model_path):
                os.environ["cnhubert_base_path"] = self.hubert_model_path
                print(f"✅ HuBERT模型路径已设置")

            # 关键修复：设置默认的GPT和SoVITS模型路径
            if self.database_manager.tts_files_database["gpt"]:
                first_gpt = list(self.database_manager.tts_files_database["gpt"].values())[0]
                os.environ["gpt_path"] = first_gpt
                print(f"📌 默认GPT模型: {os.path.basename(first_gpt)}")

            if self.database_manager.tts_files_database["sovits"]:
                first_sovits = list(self.database_manager.tts_files_database["sovits"].values())[0]
                os.environ["sovits_path"] = first_sovits
                print(f"📌 默认SoVITS模型: {os.path.basename(first_sovits)}")

            # 设置其他必要环境变量
            os.environ["version"] = "v2"
            os.environ["is_half"] = "True" if torch.cuda.is_available() else "False"
            os.environ["language"] = "Auto"
            os.environ["infer_ttswebui"] = "9872"
            os.environ["is_share"] = "False"

            # 临时重定向输出，避免模块导入时的冗余信息
            import io
            import contextlib

            # 创建空设备
            class NullIO(io.StringIO):
                def write(self, text):
                    # 只保留关键错误信息
                    if "error" in text.lower() or "exception" in text.lower():
                        return super().write(text)
                    return len(text)

            # 导入TTS模块时重定向输出
            with contextlib.redirect_stdout(NullIO()), contextlib.redirect_stderr(NullIO()):
                try:
                    from tools.i18n.i18n import I18nAuto
                    from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights, \
                        get_tts_wav as real_get_tts_wav

                    # 保存到模块字典
                    self.tts_modules['I18nAuto'] = I18nAuto
                    self.tts_modules['change_gpt_weights'] = change_gpt_weights
                    self.tts_modules['change_sovits_weights'] = change_sovits_weights
                    self.tts_modules['get_tts_wav'] = real_get_tts_wav
                    self.tts_modules['i18n'] = I18nAuto()

                except ImportError as e:
                    print(f"❌ TTS模块导入失败: {e}")
                    self.tts_available = False
                    return False, f"模块导入失败：{str(e)}"

            self.tts_modules_loaded = True
            self.tts_available = True
            print("✅ TTS模块加载成功")

            return True, "模块加载成功"
        except Exception as e:
            print(f"❌ TTS模块加载失败: {e}")
            self.tts_available = False
            return False, f"模块加载失败：{str(e)}"

    def synthesize_text(self, text: str, ref_audio_path: str, ref_text_path: str,
                        auto_play: bool = True) -> Tuple[bool, str]:
        """合成文本为语音"""
        with self.is_tts_synthesizing_lock:
            if self.is_tts_synthesizing:
                return False, "正在合成中，请稍候"
            self.is_tts_synthesizing = True

        # 检查模块是否已加载
        if not self.tts_modules_loaded:
            success, message = self.load_tts_modules()
            if not success:
                with self.is_tts_synthesizing_lock:
                    self.is_tts_synthesizing = False
                return False, message

        if not self.tts_available:
            with self.is_tts_synthesizing_lock:
                self.is_tts_synthesizing = False
            return False, "TTS模块不可用"

        try:
            # 读取参考文本（使用缓存）
            ref_text_content = self.database_manager.get_cached_text(ref_text_path)

            # 检查函数是否可用
            if 'get_tts_wav' not in self.tts_modules:
                with self.is_tts_synthesizing_lock:
                    self.is_tts_synthesizing = False
                return False, "TTS合成函数未初始化"

            # 清理文本
            cleaned_text = self.text_processor.clean_text_for_tts(text)

            # 使用操作系统级别的输出重定向
            if os.name == 'nt':  # Windows
                null_device = 'nul'
            else:  # Linux/Mac
                null_device = '/dev/null'

            # 保存原始的stdout和stderr文件描述符
            original_stdout_fd = os.dup(1)
            original_stderr_fd = os.dup(2)

            # 打开空设备
            null_fd = os.open(null_device, os.O_WRONLY)

            try:
                # 将stdout和stderr重定向到空设备
                os.dup2(null_fd, 1)  # stdout
                os.dup2(null_fd, 2)  # stderr

                # 也重定向Python层的sys.stdout和sys.stderr
                original_sys_stdout = sys.stdout
                original_sys_stderr = sys.stderr

                class NullWriter:
                    def write(self, s):
                        return len(s)

                    def flush(self):
                        pass

                null_writer = NullWriter()
                sys.stdout = null_writer
                sys.stderr = null_writer

                # 设置环境变量确保静默
                os.environ['TQDM_DISABLE'] = '1'
                os.environ['PROGRESS_BAR'] = '0'

                # 抑制日志
                import logging
                logging.getLogger().setLevel(logging.CRITICAL)

                try:
                    # 执行合成
                    get_tts_wav = self.tts_modules['get_tts_wav']
                    i18n = self.tts_modules['i18n']

                    synthesis_result = get_tts_wav(
                        ref_wav_path=ref_audio_path,
                        prompt_text=ref_text_content,
                        prompt_language=i18n(self.default_tts_config["ref_language"]),
                        text=cleaned_text,
                        text_language=i18n(self.default_tts_config["target_language"]),
                        top_p=1.0,
                        temperature=1.0,
                        speed=1.0
                    )
                finally:
                    # 恢复Python层的输出
                    sys.stdout = original_sys_stdout
                    sys.stderr = original_sys_stderr
                    # 恢复日志级别
                    logging.getLogger().setLevel(logging.WARNING)

            finally:
                # 恢复文件描述符
                os.dup2(original_stdout_fd, 1)
                os.dup2(original_stderr_fd, 2)
                # 关闭文件描述符
                os.close(original_stdout_fd)
                os.close(original_stderr_fd)
                os.close(null_fd)

            if synthesis_result:
                result_list = list(synthesis_result)
                if result_list:
                    sampling_rate, audio_data = result_list[-1]

                    # 保存音频文件
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

                    # 使用参考音频的文件名（去掉后缀）+ 时间戳
                    ref_audio_name = os.path.splitext(os.path.basename(ref_audio_path))[0]
                    output_wav = os.path.join(self.default_tts_config["output_path"], f"{ref_audio_name}_{timestamp}.wav")

                    sf.write(output_wav, audio_data, sampling_rate)

                    # 添加到合成文件列表
                    self.database_manager.add_synthesized_file(output_wav)

                    with self.is_tts_synthesizing_lock:
                        self.is_tts_synthesizing = False
                    return True, output_wav

            with self.is_tts_synthesizing_lock:
                self.is_tts_synthesizing = False
            return False, "合成失败：无音频数据返回"
        except Exception as e:
            with self.is_tts_synthesizing_lock:
                self.is_tts_synthesizing = False
            return False, f"合成出错：{str(e)}"

    def synthesize_text_with_retry(self, text: str, ref_audio_path: str, ref_text_path: str,
                                   max_retries: int = 2, retry_delay: float = 1.0) -> Tuple[bool, str]:
        """
        带重试机制的文本合成

        Args:
            text: 要合成的文本
            ref_audio_path: 参考音频路径
            ref_text_path: 参考文本路径
            max_retries: 最大重试次数
            retry_delay: 重试延迟(秒)

        Returns:
            (success, result)
        """
        for attempt in range(max_retries + 1):
            try:
                # 检查是否正在合成
                with self.is_tts_synthesizing_lock:
                    if self.is_tts_synthesizing:
                        if attempt < max_retries:
                            print(f"🔄 第{attempt + 1}次重试: TTS正在合成中，等待{retry_delay}秒...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            return False, "TTS正忙，请稍后再试"

                    # 设置合成标志
                    self.is_tts_synthesizing = True

                # 尝试合成
                success, result = self._synthesize_text_internal(text, ref_audio_path, ref_text_path)

                if success:
                    return True, result
                elif "合成中" in result and attempt < max_retries:
                    print(f"🔄 第{attempt + 1}次重试: {result}")
                    time.sleep(retry_delay)
                else:
                    return success, result

            except Exception as e:
                if attempt < max_retries:
                    print(f"🔄 第{attempt + 1}次重试: 异常 {e}")
                    time.sleep(retry_delay)
                else:
                    return False, f"合成异常: {str(e)}"
            finally:
                # 确保锁被释放
                with self.is_tts_synthesizing_lock:
                    self.is_tts_synthesizing = False

        return False, "达到最大重试次数"

    def _synthesize_text_internal(self, text: str, ref_audio_path: str, ref_text_path: str) -> tuple[bool, str]:
        """
        内部合成方法 - 实际的文本到语音合成逻辑

        Args:
            text: 要合成的文本
            ref_audio_path: 参考音频路径
            ref_text_path: 参考文本路径

        Returns:
            (success, 音频文件路径或错误信息)
        """
        # 检查模块是否已加载
        if not self.tts_modules_loaded:
            success, message = self.load_tts_modules()
            if not success:
                return False, message

        if not self.tts_available:
            return False, "TTS模块不可用"

        # 检查必要文件是否存在
        if not os.path.exists(ref_audio_path):
            return False, f"参考音频文件不存在: {ref_audio_path}"
        if not os.path.exists(ref_text_path):
            return False, f"参考文本文件不存在: {ref_text_path}"

        try:
            # 读取参考文本（使用缓存）
            ref_text_content = self.database_manager.get_cached_text(ref_text_path)

            if not ref_text_content:
                return False, "参考文本内容为空"

            # 检查函数是否可用
            if 'get_tts_wav' not in self.tts_modules:
                return False, "TTS合成函数未初始化"

            # 清理文本
            cleaned_text = self.text_processor.clean_text_for_tts(text)

            # 检查清理后的文本质量
            if not cleaned_text or len(cleaned_text) < 5:
                print(f"⚠️  清理后的文本过短（长度: {len(cleaned_text) if cleaned_text else 0}），使用默认文本")
                cleaned_text = "你好，我是小芸，很高兴为您服务"

            # 检查中文字符占比
            chinese_char_count = len([c for c in cleaned_text if '\u4e00' <= c <= '\u9fff'])
            if chinese_char_count < 2:
                print(f"⚠️  文本中文字符过少（{chinese_char_count}个），使用默认文本")
                cleaned_text = "你好，我是小芸，很高兴为您服务"

            # 使用操作系统级别的输出重定向
            if os.name == 'nt':  # Windows
                null_device = 'nul'
            else:  # Linux/Mac
                null_device = '/dev/null'

            # 保存原始的stdout和stderr文件描述符
            original_stdout_fd = os.dup(1)
            original_stderr_fd = os.dup(2)

            # 打开空设备
            null_fd = os.open(null_device, os.O_WRONLY)

            synthesis_result = None

            try:
                # 将stdout和stderr重定向到空设备
                os.dup2(null_fd, 1)  # stdout
                os.dup2(null_fd, 2)  # stderr

                # 也重定向Python层的sys.stdout和sys.stderr
                original_sys_stdout = sys.stdout
                original_sys_stderr = sys.stderr

                class NullWriter:
                    def write(self, s):
                        return len(s)

                    def flush(self):
                        pass

                null_writer = NullWriter()
                sys.stdout = null_writer
                sys.stderr = null_writer

                # 设置环境变量确保静默
                os.environ['TQDM_DISABLE'] = '1'
                os.environ['PROGRESS_BAR'] = '0'

                # 抑制日志
                import logging
                logging.getLogger().setLevel(logging.CRITICAL)

                try:
                    # 执行合成
                    get_tts_wav = self.tts_modules['get_tts_wav']
                    i18n = self.tts_modules['i18n']

                    # 注意：这里使用默认参数，您可以根据需要调整
                    synthesis_result = get_tts_wav(
                        ref_wav_path=ref_audio_path,
                        prompt_text=ref_text_content,
                        prompt_language=i18n(self.default_tts_config["ref_language"]),
                        text=cleaned_text,
                        text_language=i18n(self.default_tts_config["target_language"]),
                        top_p=1.0,
                        temperature=1.0,
                        speed=1.0
                    )
                finally:
                    # 恢复Python层的输出
                    sys.stdout = original_sys_stdout
                    sys.stderr = original_sys_stderr
                    # 恢复日志级别
                    logging.getLogger().setLevel(logging.WARNING)

            finally:
                # 恢复文件描述符
                os.dup2(original_stdout_fd, 1)
                os.dup2(original_stderr_fd, 2)
                # 关闭文件描述符
                os.close(original_stdout_fd)
                os.close(original_stderr_fd)
                os.close(null_fd)

            if synthesis_result:
                result_list = list(synthesis_result)
                if result_list:
                    sampling_rate, audio_data = result_list[-1]

                    # 保存音频文件
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

                    # 使用参考音频的文件名（去掉后缀）+ 时间戳
                    ref_audio_name = os.path.splitext(os.path.basename(ref_audio_path))[0]
                    output_wav = os.path.join(self.default_tts_config["output_path"], f"{ref_audio_name}_{timestamp}.wav")

                    # 确保目录存在
                    os.makedirs(os.path.dirname(output_wav), exist_ok=True)

                    # 保存音频文件
                    sf.write(output_wav, audio_data, sampling_rate)

                    # 添加到合成文件列表
                    self.database_manager.add_synthesized_file(output_wav)

                    return True, output_wav

            return False, "合成失败：无音频数据返回"

        except Exception as e:
            error_msg = f"合成出错：{str(e)}"
            print(f"❌ TTS合成错误详情: {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg
