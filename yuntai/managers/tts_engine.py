"""
TTS引擎 - 负责GPT-SoVITS模型加载、环境设置和核心合成调用
使用 pathlib 进行跨平台路径处理

该模块提供文本到语音(TTS)合成的核心功能，包括：
- TTS模块加载和环境配置
- 文本预处理和清理
- 音频合成和保存
- 重试机制支持
"""

from __future__ import annotations

import io
import os
import sys
import time
import contextlib
import threading
import datetime
import logging
from typing import Any, TYPE_CHECKING
from pathlib import Path

import torch
import soundfile as sf
import warnings

if TYPE_CHECKING:
    from .tts_database import TTSDatabaseManager
    from .tts_text import TTSTextProcessor

logger: logging.Logger = logging.getLogger(__name__)


class NullIO(io.StringIO):
    """
    空输出流类
    
    用于抑制不需要的控制台输出，同时保留错误信息。
    在TTS模块加载和合成过程中使用，避免大量调试输出。
    """
    
    def write(self, text: str) -> int:
        """
        写入文本，仅保留错误信息
        
        Args:
            text: 待写入的文本
        
        Returns:
            文本长度
        """
        if "error" in text.lower() or "exception" in text.lower():
            return super().write(text)
        return len(text)


class NullWriter:
    """
    空写入器类
    
    用于重定向标准输出和标准错误，抑制冗余输出。
    """
    
    def write(self, s: str) -> int:
        """写入并返回字符串长度"""
        return len(s)
    
    def flush(self) -> None:
        """刷新缓冲区（空操作）"""
        pass


class TTSEngine:
    """
    TTS引擎 - 核心合成功能
    
    负责GPT-SoVITS模型的加载、环境配置和语音合成。
    支持单次合成和带重试机制的合成。
    
    Attributes:
        default_tts_config: 默认TTS配置字典
        database_manager: TTS数据库管理器
        text_processor: TTS文本处理器
        tts_enabled: TTS功能是否启用
        tts_available: TTS模块是否可用
        tts_modules_loaded: TTS模块是否已加载
        is_tts_synthesizing: 是否正在合成
    """

    def __init__(
        self,
        default_tts_config: dict[str, Any],
        database_manager: TTSDatabaseManager,
        text_processor: TTSTextProcessor
    ) -> None:
        """
        初始化TTS引擎
        
        Args:
            default_tts_config: 默认TTS配置，包含模型路径、输出路径等
            database_manager: 数据库管理器实例，管理模型和合成文件
            text_processor: 文本处理器实例，负责文本预处理
        """
        self.default_tts_config: dict[str, Any] = default_tts_config
        self.database_manager: TTSDatabaseManager = database_manager
        self.text_processor: TTSTextProcessor = text_processor

        self.bert_model_path: Path | None = (
            Path(default_tts_config.get("bert_model_path"))
            if default_tts_config.get("bert_model_path")
            else None
        )
        self.hubert_model_path: Path | None = (
            Path(default_tts_config.get("hubert_model_path"))
            if default_tts_config.get("hubert_model_path")
            else None
        )

        self.tts_enabled: bool = False
        self.tts_available: bool = False
        self.tts_modules_loaded: bool = False

        self.is_tts_synthesizing: bool = False
        self.is_tts_synthesizing_lock: threading.Lock = threading.Lock()

        self.tts_modules: dict[str, Any] = {}

        warnings.filterwarnings('ignore')

    def load_tts_modules(self) -> tuple[bool, str]:
        """
        加载TTS模块
        
        初始化TTS运行环境，加载必要的模型和依赖。
        包括设置环境变量、配置日志级别和导入TTS模块。
        
        Returns:
            元组 (是否成功, 消息)
        """
        if self.tts_modules_loaded:
            return True, "模块已加载"

        try:
            print("📦 正在加载TTS模块...")

            self._setup_environment()
            self._setup_model_paths()
            self._setup_tts_config()

            with contextlib.redirect_stdout(NullIO()), contextlib.redirect_stderr(NullIO()):
                try:
                    self._load_custom_tts_modules()
                except Exception as e:
                    print(f"⚠️  自定义TTS不可用，降级到原始版本: {e}")
                    self._load_original_tts_modules()

            self.tts_modules_loaded = True
            self.tts_available = True
            print("✅ TTS模块加载成功")

            return True, "模块加载成功"
        except Exception as e:
            print(f"❌ TTS模块加载失败: {e}")
            self.tts_available = False
            return False, f"模块加载失败：{str(e)}"

    def _setup_environment(self) -> None:
        """设置TTS运行环境变量"""
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TQDM_DISABLE"] = "1"
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        logging.getLogger("transformers").setLevel(logging.ERROR)
        logging.getLogger("torch").setLevel(logging.WARNING)

    def _setup_model_paths(self) -> None:
        """设置模型路径环境变量"""
        if self.bert_model_path and self.bert_model_path.exists():
            os.environ["bert_path"] = str(self.bert_model_path)
            print("✅ BERT模型路径已设置")

        if self.hubert_model_path and self.hubert_model_path.exists():
            os.environ["cnhubert_base_path"] = str(self.hubert_model_path)
            print("✅ HuBERT模型路径已设置")

        if self.database_manager.tts_files_database["gpt"]:
            first_gpt = list(self.database_manager.tts_files_database["gpt"].values())[0]
            os.environ["gpt_path"] = first_gpt
            print(f"📌 默认GPT模型: {Path(first_gpt).name}")

        if self.database_manager.tts_files_database["sovits"]:
            first_sovits = list(self.database_manager.tts_files_database["sovits"].values())[0]
            os.environ["sovits_path"] = first_sovits
            print(f"📌 默认SoVITS模型: {Path(first_sovits).name}")

    def _setup_tts_config(self) -> None:
        """设置TTS配置环境变量"""
        os.environ["version"] = "v2"
        os.environ["is_half"] = "True" if torch.cuda.is_available() else "False"
        os.environ["language"] = "Auto"
        os.environ["infer_ttswebui"] = "9872"
        os.environ["is_share"] = "False"

    def _load_custom_tts_modules(self) -> None:
        """加载自定义TTS模块"""
        from yuntai.managers.gpt_sovits_custom import (
            get_tts_wav,
            change_gpt_weights,
            change_sovits_weights,
            I18nAuto
        )

        self.tts_modules['I18nAuto'] = I18nAuto
        self.tts_modules['change_gpt_weights'] = change_gpt_weights
        self.tts_modules['change_sovits_weights'] = change_sovits_weights
        self.tts_modules['get_tts_wav'] = get_tts_wav
        self.tts_modules['i18n'] = I18nAuto()
        print("✅ 使用自定义TTS模块（已移除冗余输出）")

    def _load_original_tts_modules(self) -> None:
        """加载原始TTS模块"""
        from tools.i18n.i18n import I18nAuto
        from GPT_SoVITS.inference_webui import change_gpt_weights, change_sovits_weights, \
            get_tts_wav as real_get_tts_wav

        self.tts_modules['I18nAuto'] = I18nAuto
        self.tts_modules['change_gpt_weights'] = change_gpt_weights
        self.tts_modules['change_sovits_weights'] = change_sovits_weights
        self.tts_modules['get_tts_wav'] = real_get_tts_wav
        self.tts_modules['i18n'] = I18nAuto()

    def synthesize_text(
        self,
        text: str,
        ref_audio_path: str,
        ref_text_path: str,
        auto_play: bool = True
    ) -> tuple[bool, str]:
        """
        合成文本为语音
        
        将输入文本转换为语音文件，支持自动播放。
        
        Args:
            text: 要合成的文本内容
            ref_audio_path: 参考音频文件路径
            ref_text_path: 参考文本文件路径
            auto_play: 是否自动播放（此参数保留用于兼容性）
        
        Returns:
            元组 (是否成功, 音频文件路径或错误信息)
        """
        with self.is_tts_synthesizing_lock:
            if self.is_tts_synthesizing:
                return False, "正在合成中，请稍候"
            self.is_tts_synthesizing = True

        try:
            success, result = self._do_synthesis(text, ref_audio_path, ref_text_path)
            return success, result
        finally:
            with self.is_tts_synthesizing_lock:
                self.is_tts_synthesizing = False

    def synthesize_text_with_retry(
        self,
        text: str,
        ref_audio_path: str,
        ref_text_path: str,
        max_retries: int = 2,
        retry_delay: float = 1.0
    ) -> tuple[bool, str]:
        """
        带重试机制的文本合成
        
        当合成失败或系统繁忙时自动重试，提高合成成功率。
        
        Args:
            text: 要合成的文本内容
            ref_audio_path: 参考音频文件路径
            ref_text_path: 参考文本文件路径
            max_retries: 最大重试次数，默认2次
            retry_delay: 重试间隔时间(秒)，默认1.0秒
        
        Returns:
            元组 (是否成功, 音频文件路径或错误信息)
        """
        for attempt in range(max_retries + 1):
            try:
                with self.is_tts_synthesizing_lock:
                    if self.is_tts_synthesizing:
                        if attempt < max_retries:
                            print(f"🔄 第{attempt + 1}次重试: TTS正在合成中，等待{retry_delay}秒...")
                            time.sleep(retry_delay)
                            continue
                        else:
                            return False, "TTS正忙，请稍后再试"

                    self.is_tts_synthesizing = True

                success, result = self._do_synthesis(text, ref_audio_path, ref_text_path)

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
                with self.is_tts_synthesizing_lock:
                    self.is_tts_synthesizing = False

        return False, "达到最大重试次数"

    def _do_synthesis(
        self,
        text: str,
        ref_audio_path: str,
        ref_text_path: str
    ) -> tuple[bool, str]:
        """
        执行实际的文本到语音合成
        
        核心合成逻辑，包括文本预处理、模型调用和音频保存。
        
        Args:
            text: 要合成的文本内容
            ref_audio_path: 参考音频文件路径
            ref_text_path: 参考文本文件路径
        
        Returns:
            元组 (是否成功, 音频文件路径或错误信息)
        """
        if not self.tts_modules_loaded:
            success, message = self.load_tts_modules()
            if not success:
                return False, message

        if not self.tts_available:
            return False, "TTS模块不可用"

        ref_audio_file = Path(ref_audio_path)
        ref_text_file = Path(ref_text_path)

        if not ref_audio_file.exists():
            return False, f"参考音频文件不存在: {ref_audio_path}"
        if not ref_text_file.exists():
            return False, f"参考文本文件不存在: {ref_text_path}"

        try:
            ref_text_content = self.database_manager.get_cached_text(ref_text_path)

            if not ref_text_content:
                return False, "参考文本内容为空"

            if 'get_tts_wav' not in self.tts_modules:
                return False, "TTS合成函数未初始化"

            cleaned_text = self.text_processor.clean_text_for_tts(text)

            if not cleaned_text or len(cleaned_text) < 5:
                print(f"⚠️  清理后的文本过短（长度: {len(cleaned_text) if cleaned_text else 0}），使用默认文本")
                cleaned_text = "你好，我是小芸，很高兴为您服务"

            chinese_char_count = len([c for c in cleaned_text if '\u4e00' <= c <= '\u9fff'])
            if chinese_char_count < 2:
                print(f"⚠️  文本中文字符过少（{chinese_char_count}个），使用默认文本")
                cleaned_text = "你好，我是小芸，很高兴为您服务"

            synthesis_result = self._execute_synthesis(
                cleaned_text, 
                ref_audio_path, 
                ref_text_content
            )

            if synthesis_result:
                return self._save_synthesis_result(synthesis_result, ref_audio_path)

            return False, "合成失败：无音频数据返回"

        except Exception as e:
            error_msg = f"合成出错：{str(e)}"
            print(f"❌ TTS合成错误详情: {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg

    def _execute_synthesis(
        self,
        cleaned_text: str,
        ref_audio_path: str,
        ref_text_content: str
    ) -> Any:
        """
        执行TTS合成调用
        
        在抑制冗余输出的环境中调用TTS模型进行合成。
        
        Args:
            cleaned_text: 清理后的待合成文本
            ref_audio_path: 参考音频路径
            ref_text_content: 参考文本内容
        
        Returns:
            合成结果（生成器或音频数据）
        """
        null_device = 'nul' if os.name == 'nt' else '/dev/null'

        original_stdout_fd = os.dup(1)
        original_stderr_fd = os.dup(2)
        null_fd = os.open(null_device, os.O_WRONLY)

        synthesis_result = None

        try:
            os.dup2(null_fd, 1)
            os.dup2(null_fd, 2)

            original_sys_stdout = sys.stdout
            original_sys_stderr = sys.stderr

            sys.stdout = NullWriter()
            sys.stderr = NullWriter()

            os.environ['TQDM_DISABLE'] = '1'
            os.environ['PROGRESS_BAR'] = '0'
            logging.getLogger().setLevel(logging.CRITICAL)

            try:
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
                sys.stdout = original_sys_stdout
                sys.stderr = original_sys_stderr
                logging.getLogger().setLevel(logging.WARNING)

        finally:
            os.dup2(original_stdout_fd, 1)
            os.dup2(original_stderr_fd, 2)
            os.close(original_stdout_fd)
            os.close(original_stderr_fd)
            os.close(null_fd)

        return synthesis_result

    def _save_synthesis_result(
        self,
        synthesis_result: Any,
        ref_audio_path: str
    ) -> tuple[bool, str]:
        """
        保存合成结果到音频文件
        
        将合成结果转换为WAV文件并保存到输出目录。
        
        Args:
            synthesis_result: 合成结果数据
            ref_audio_path: 参考音频路径（用于命名输出文件）
        
        Returns:
            元组 (是否成功, 音频文件路径或错误信息)
        """
        result_list = list(synthesis_result)
        if not result_list:
            return False, "合成失败：无音频数据返回"

        sampling_rate, audio_data = result_list[-1]

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        ref_audio_name = Path(ref_audio_path).stem
        output_path = Path(self.default_tts_config["output_path"])
        output_wav = output_path / f"{ref_audio_name}_{timestamp}.wav"

        output_path.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_wav), audio_data, sampling_rate)

        self.database_manager.add_synthesized_file(str(output_wav))

        return True, str(output_wav)
