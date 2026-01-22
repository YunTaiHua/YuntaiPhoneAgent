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
import queue
from typing import Optional, Dict, Any, Tuple, List, Callable
import warnings
import logging
import pyaudio
import torch
import soundfile as sf
import re
import wave
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
    ZHIPU_CHAT_MODEL
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

        # 使用统一配置
        self.gpt_sovits_root = GPT_SOVITS_ROOT
        self.bert_model_path = BERT_MODEL_PATH
        self.hubert_model_path = HUBERT_MODEL_PATH

        # 默认TTS配置
        self.default_tts_config = {
            "gpt_model_dir": GPT_MODEL_DIR,
            "sovits_model_dir": SOVITS_MODEL_DIR,
            "ref_audio_root": REF_AUDIO_ROOT,
            "ref_text_root": REF_TEXT_ROOT,
            "ref_language": TTS_REF_LANGUAGE,
            "target_language": TTS_TARGET_LANGUAGE,
            "output_path": TTS_OUTPUT_DIR
        }


        # 状态变量
        self.tts_enabled = False
        self.tts_available = False
        self.tts_modules_loaded = False

        # 线程安全的状态变量
        self.is_tts_synthesizing = False
        self.is_tts_synthesizing_lock = threading.Lock()
        self.is_playing_audio = False
        self.is_playing_audio_lock = threading.Lock()
        self.tts_synthesized_files = []
        self.tts_synthesized_files_lock = threading.Lock()
        self.current_models_lock = threading.Lock()

        # 当前选中的模型
        self.current_gpt_model = None
        self.current_sovits_model = None
        self.current_ref_audio = None
        self.current_ref_text = None

        # TTS模块
        self.tts_modules: Dict[str, Any] = {}

        # 音频播放器
        self.audio_player = None
        self.audio_play_lock = threading.Lock()

        # 线程池执行器
        self.executor = ThreadPoolExecutor(max_workers=3)

        # TTS文件数据库
        self.tts_files_database = {
            "gpt": {},  # {文件名: 正确绝对路径}
            "sovits": {},  # {文件名: 正确绝对路径}
            "audio": {},  # {文件名: 正确绝对路径}
            "text": {}  # {文件名: 正确绝对路径}
        }

        # 缓存
        self._text_cache = {}  # {文件路径: 文本内容}
        self._cache_lock = threading.Lock()

        # 过滤冗余警告
        warnings.filterwarnings('ignore')

        # 初始化音频播放器
        self._init_audio_player()

        # 新增：分段合成相关
        self.max_text_length = TTS_MAX_SEGMENT_LENGTH  # 单个文本片段最大长度
        self.tts_segments = []  # 存储分段音频路径
        self.tts_segments_lock = threading.Lock()

        # 检查音频合并依赖
        self.can_merge_audio = self._check_merge_dependencies()

    def _check_merge_dependencies(self) -> bool:
        """检查音频合并所需的依赖"""
        try:
            import numpy
            import soundfile
            return True
        except ImportError:
            logger.warning("音频合并功能需要额外依赖: pip install numpy soundfile")
            return False

    def _get_cached_text(self, file_path: str) -> str:
        """获取缓存的文本内容"""
        with self._cache_lock:
            if file_path in self._text_cache:
                return self._text_cache[file_path]
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                self._text_cache[file_path] = content
                return content
            except IOError as e:
                logger.error(f"读取文本文件失败: {file_path}, {e}")
                raise

    def synthesize_long_text_serial(self, text: str, ref_audio_path: str, ref_text_path: str) -> tuple[bool, str]:
        """
        分段串行合成长文本语音

        Args:
            text: 要合成的长文本
            ref_audio_path: 参考音频路径
            ref_text_path: 参考文本路径

        Returns:
            (success, 最终音频文件路径)
        """
        try:
            # print(f"📝 开始分段处理文本，总长度: {len(text)} 字符")

            # 清理文本
            cleaned_text = self._clean_text_for_tts(text)

            # 分段文本
            segments = self._split_text_by_numbered_sections(cleaned_text)

            if len(segments) == 1:
                # print(f"📝 文本较短，使用单次合成")
                # 直接合成
                return self.synthesize_text(text, ref_audio_path, ref_text_path, auto_play=False)

            # print(f"📝 文本分为 {len(segments)} 个段落进行串行合成")

            # 串行合成每个分段
            segment_files = []

            for i, segment in enumerate(segments):
                # print(f"🎵 开始合成第 {i + 1}/{len(segments)} 段，长度: {len(segment)} 字符")

                # 使用带重试的合成
                success, result = self.synthesize_text_with_retry(
                    segment, ref_audio_path, ref_text_path, max_retries=1
                )

                if success:
                    # print(f"✅ 第 {i + 1} 段合成成功: {os.path.basename(result)}")
                    segment_files.append((i, result))

                    # 添加延迟避免冲突
                    if i < len(segments) - 1:
                        time.sleep(0.3)  # 300ms延迟
                else:
                    print(f"❌ 第 {i + 1} 段合成失败: {result}")
                    # 尝试用更短的文本重试
                    if len(segment) > 100:
                        short_segment = segment[:100] + "..."
                        retry_success, retry_result = self.synthesize_text_with_retry(
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
            final_audio_path = self._merge_audio_segments(audio_files_to_merge)

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
                # print(f"✅ 分段合成完成，合并为: {os.path.basename(final_audio_path)}")

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

    def _split_text_by_numbered_sections(self, text: str) -> list[str]:
        """
        按序号分段文本（改进版）

        Args:
            text: 要分段的文本

        Returns:
            分段后的文本列表
        """
        segments = []

        # 多种序号模式（优先级从高到低）
        patterns = [
            (r'### (\d+\.)', 3),  # Markdown三级标题
            (r'## (\d+\.)', 2),  # Markdown二级标题
            (r'(\d+\.\s)', 1),  # 数字加点（英文）
            (r'(\d+、\s)', 1),  # 数字加顿号（中文）
            (r'\((\d+)\)\s', 1),  # 括号数字
            (r'一、', 1),  # 中文序号
            (r'二、', 1),
            (r'三、', 1),
            (r'四、', 1),
            (r'五、', 1),
            (r'首先', 1),  # 连接词
            (r'其次', 1),
            (r'再次', 1),
            (r'最后', 1),
        ]

        best_pattern = None
        best_matches = []

        # 寻找最佳分段模式
        for pattern, priority in patterns:
            matches = list(re.finditer(pattern, text))
            if len(matches) >= 2:  # 至少有2个匹配
                if not best_matches or (
                len(matches) > len(best_matches) and priority >= patterns[patterns.index((best_pattern, 0))][
                    1] if best_pattern else 0):
                    best_pattern = pattern
                    best_matches = matches

        # 使用最佳模式分段
        if best_pattern and best_matches:
            # 从第一个分段点开始
            start_pos = 0
            last_end_pos = 0

            for i, match in enumerate(best_matches):
                if i == 0:
                    # 第一段：从开头到第一个分段点
                    segment = text[start_pos:match.start()].strip()
                    if segment and len(segment) > 10:  # 确保不是空段
                        segments.append(segment)
                    start_pos = match.start()
                    last_end_pos = match.start()
                    continue

                # 中间段：从前一个分段点到当前分段点
                segment = text[last_end_pos:match.start()].strip()
                if segment and len(segment) > 10:
                    segments.append(segment)
                last_end_pos = match.start()

            # 最后一段：从最后一个分段点到结尾
            last_segment = text[last_end_pos:].strip()
            if last_segment and len(last_segment) > 10:
                segments.append(last_segment)

            # 检查分段质量
            if segments and len(segments) >= 2:
                avg_length = sum(len(s) for s in segments) / len(segments)
                if 50 <= avg_length <= self.max_text_length * 2:
                    return segments
                else:
                    segments = []

        # 如果没有找到合适的序号分段，尝试按段落分段
        if not segments:
            # 按空行分段
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            if len(paragraphs) >= 2:
                # 合并过短的段落
                merged = []
                buffer = ""

                for para in paragraphs:
                    if len(buffer) + len(para) < self.max_text_length:
                        if buffer:
                            buffer += "\n\n" + para
                        else:
                            buffer = para
                    else:
                        if buffer:
                            merged.append(buffer)
                        buffer = para

                if buffer:
                    merged.append(buffer)

                if len(merged) >= 2:
                    return merged

        # 最后尝试按标点分段
        if not segments:
            segments = self._split_text_by_punctuation(text)

        return segments

    def _split_text_by_punctuation(self, text: str) -> list[str]:
        """
        按标点符号分段

        Args:
            text: 要分段的文本

        Returns:
            分段后的文本列表
        """
        segments = []
        current_segment = ""

        # 标点符号列表
        punctuation_marks = ['。', '！', '？', '；', '.', '!', '?', ';']

        for char in text:
            current_segment += char

            # 如果遇到标点，并且当前段达到一定长度
            if char in punctuation_marks and len(current_segment) >= 50:
                segments.append(current_segment.strip())
                current_segment = ""

            # 如果当前段超过最大长度，强制分段
            elif len(current_segment) >= self.max_text_length:
                # 在最后出现的标点处分段
                last_punct = -1
                for punct in punctuation_marks:
                    pos = current_segment.rfind(punct)
                    if pos > last_punct:
                        last_punct = pos

                if last_punct > 0:
                    segments.append(current_segment[:last_punct + 1].strip())
                    current_segment = current_segment[last_punct + 1:]
                else:
                    # 没有标点，按长度硬切
                    segments.append(current_segment.strip())
                    current_segment = ""

        # 添加最后一段
        if current_segment.strip():
            segments.append(current_segment.strip())

        # 合并过短的段落
        merged_segments = []
        buffer = ""

        for segment in segments:
            if len(buffer) + len(segment) < self.max_text_length * 0.7:
                buffer += " " + segment if buffer else segment
            else:
                if buffer:
                    merged_segments.append(buffer)
                buffer = segment

        if buffer:
            merged_segments.append(buffer)

        print(f"📝 按标点分段，合并后: {len(merged_segments)} 段")
        return merged_segments

    def _synthesize_segment_thread(self, index: int, text: str, ref_audio_path: str,
                                   ref_text_path: str, results_queue: queue.Queue):
        """
        单个分段合成线程

        Args:
            index: 分段索引
            text: 分段文本
            ref_audio_path: 参考音频路径
            ref_text_path: 参考文本路径
            results_queue: 结果队列
        """
        try:
            print(f"🎵 开始合成第 {index + 1} 段，长度: {len(text)} 字符")

            # 合成当前分段
            success, result = self.synthesize_text(
                text, ref_audio_path, ref_text_path, auto_play=False
            )

            if success:
                print(f"✅ 第 {index + 1} 段合成成功: {os.path.basename(result)}")
                results_queue.put((True, index, result))
            else:
                print(f"❌ 第 {index + 1} 段合成失败: {result}")
                results_queue.put((False, index, f"分段{index + 1}失败"))

        except Exception as e:
            print(f"❌ 第 {index + 1} 段合成异常: {e}")
            results_queue.put((False, index, f"分段{index + 1}异常"))

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
            ref_text_content = self._get_cached_text(ref_text_path)

            if not ref_text_content:
                return False, "参考文本内容为空"

            # 检查函数是否可用
            if 'get_tts_wav' not in self.tts_modules:
                return False, "TTS合成函数未初始化"

            # 清理文本
            cleaned_text = self._clean_text_for_tts(text)

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
                    with self.tts_synthesized_files_lock:
                        self.tts_synthesized_files.append((output_wav, os.path.basename(output_wav)))

                    return True, output_wav

            return False, "合成失败：无音频数据返回"

        except Exception as e:
            error_msg = f"合成出错：{str(e)}"
            print(f"❌ TTS合成错误详情: {error_msg}")
            import traceback
            traceback.print_exc()
            return False, error_msg

    def _merge_audio_segments(self, audio_files: List[str]) -> Optional[str]:
        """
        合并多个音频文件

        Args:
            audio_files: 音频文件路径列表

        Returns:
            合并后的音频文件路径，如果失败返回None
        """
        if not audio_files:
            return None

        if len(audio_files) == 1:
            return audio_files[0]  # 只有一个文件，不需要合并

        try:
            import numpy as np
            import soundfile as sf

            # print(f"🔊 开始合并 {len(audio_files)} 个音频文件...")

            # 读取所有音频数据
            all_audio_data = []
            all_sample_rates = []

            for i, audio_file in enumerate(audio_files):
                if os.path.exists(audio_file):
                    data, samplerate = sf.read(audio_file)
                    all_audio_data.append(data)
                    all_sample_rates.append(samplerate)
                    # print(
                    # f"  - 文件 {i + 1}: {os.path.basename(audio_file)}, 采样率: {samplerate}, 长度: {len(data) / samplerate:.2f}秒")
                else:
                    print(f"⚠️  文件不存在: {audio_file}")

            if not all_audio_data:
                return None

            # 检查采样率是否一致
            if len(set(all_sample_rates)) > 1:
                print(f"⚠️  采样率不一致，使用第一个文件的采样率: {all_sample_rates[0]}")

            target_samplerate = all_sample_rates[0]

            # 合并音频数据
            # 对于立体声音频，需要特殊处理
            if len(all_audio_data[0].shape) == 2:  # 立体声
                merged_data = np.vstack(all_audio_data)
            else:  # 单声道
                merged_data = np.concatenate(all_audio_data)

            # 保存合并后的音频 - 使用与普通合成一致的格式
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

            # 从第一个音频文件名中提取参考音频名称
            first_audio_file = audio_files[0]
            first_audio_name = os.path.basename(first_audio_file)

            # 提取参考音频名称（去掉时间戳部分）
            # 格式如: "ref_audio_name_20250119_123456.wav"
            import re
            match = re.match(r'(.+)_\d{8}_\d{6}', first_audio_name)
            if match:
                ref_audio_base = match.group(1)
            else:
                # 如果无法解析，使用默认名称
                ref_audio_base = "tts_merged"

            output_wav = os.path.join(
                self.default_tts_config["output_path"],
                f"{ref_audio_base}_merged_{timestamp}.wav"
            )

            sf.write(output_wav, merged_data, target_samplerate)

            return output_wav

        except ImportError as e:
            print(f"❌ 音频合并需要soundfile和numpy库: {e}")
            print("💡 请安装: pip install soundfile numpy")
            # 返回第一个文件作为备选
            return audio_files[0]

        except Exception as e:
            print(f"❌ 音频合并失败: {e}")
            import traceback
            traceback.print_exc()
            # 返回第一个文件作为备选
            return audio_files[0]

    def should_use_segmented_synthesis(self, text: str) -> bool:
        """
        判断是否应该使用分段合成

        Args:
            text: 要判断的文本

        Returns:
            True如果应该使用分段合成
        """
        if not text:
            return False

        cleaned_text = self._clean_text_for_tts(text)

        # 文本长度超过阈值
        if len(cleaned_text) > self.max_text_length * 1.5:  # 超过750字符
            return True

        # 包含多个序号段落
        numbered_patterns = [r'\d+\.\s', r'\d+、\s', r'\(\d+\)\s']
        for pattern in numbered_patterns:
            if len(re.findall(pattern, cleaned_text)) >= 2:
                return True

        return False

    def speak_text_intelligently(self, text: str) -> bool:
        """
        智能语音合成（自动判断是否分段）

        Args:
            text: 要合成的文本

        Returns:
            True如果合成成功
        """
        try:
            # 检查是否有参考音频和文本
            ref_audio = self.get_current_model("audio")
            ref_text = self.get_current_model("text")

            if not ref_audio or not ref_text:
                print("⚠️  无法语音播报：未选择参考音频或文本")
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
                            self.play_audio_file(audio_path)
                        else:
                            logger.error(f"分段语音合成失败: {audio_path}")

                            # 分段合成失败，尝试普通合成
                            print("🔄 分段失败，尝试普通合成...")
                            # 使用清理后的文本，确保质量
                            fallback_text = self._clean_text_for_tts(text[:500])
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

    def _init_audio_player(self):
        """初始化音频播放器"""
        try:
            self.audio_player = pyaudio.PyAudio()
            print("✅ 音频播放器初始化成功")
        except Exception as e:
            print(f"❌ 初始化音频播放失败: {e}")
            self.audio_player = None

    def init_tts_files_database(self) -> bool:
        """初始化TTS文件数据库"""
        print("🔍 初始化TTS文件数据库...")

        # 确保目录存在
        for dir_path in [
            self.default_tts_config["gpt_model_dir"],
            self.default_tts_config["sovits_model_dir"],
            self.default_tts_config["ref_audio_root"],
            self.default_tts_config["output_path"]
        ]:
            os.makedirs(dir_path, exist_ok=True)
            print(f"📁 确保目录存在: {dir_path}")

        # 扫描GPT模型
        self.tts_files_database["gpt"] = {}
        if os.path.exists(self.default_tts_config["gpt_model_dir"]):
            for root, _, files in os.walk(self.default_tts_config["gpt_model_dir"]):
                for file in files:
                    if file.endswith('.ckpt'):
                        abs_path = os.path.normpath(os.path.join(root, file))
                        self.tts_files_database["gpt"][file] = abs_path
        else:
            print(f"⚠️  GPT模型目录不存在: {self.default_tts_config['gpt_model_dir']}")

        # 扫描SoVITS模型
        self.tts_files_database["sovits"] = {}
        if os.path.exists(self.default_tts_config["sovits_model_dir"]):
            for root, _, files in os.walk(self.default_tts_config["sovits_model_dir"]):
                for file in files:
                    if file.endswith('.pth'):
                        abs_path = os.path.normpath(os.path.join(root, file))
                        self.tts_files_database["sovits"][file] = abs_path
        else:
            print(f"⚠️  SoVITS模型目录不存在: {self.default_tts_config['sovits_model_dir']}")

        # 扫描参考音频
        self.tts_files_database["audio"] = {}
        if os.path.exists(self.default_tts_config["ref_audio_root"]):
            for root, _, files in os.walk(self.default_tts_config["ref_audio_root"]):
                for file in files:
                    if file.endswith(('.wav', '.mp3', '.flac')):
                        abs_path = os.path.normpath(os.path.join(root, file))
                        self.tts_files_database["audio"][file] = abs_path
        else:
            print(f"⚠️  参考音频目录不存在: {self.default_tts_config['ref_audio_root']}")

        # 扫描参考文本
        self.tts_files_database["text"] = {}
        if os.path.exists(self.default_tts_config["ref_text_root"]):
            for root, _, files in os.walk(self.default_tts_config["ref_text_root"]):
                for file in files:
                    if file.endswith('.txt'):
                        abs_path = os.path.normpath(os.path.join(root, file))
                        self.tts_files_database["text"][file] = abs_path
        else:
            print(f"⚠️  参考文本目录不存在: {self.default_tts_config['ref_text_root']}")

        print(f"✅ 文件数据库初始化完成:")
        print(f"   - GPT模型: {len(self.tts_files_database['gpt'])} 个")
        print(f"   - SoVITS模型: {len(self.tts_files_database['sovits'])} 个")
        print(f"   - 参考音频: {len(self.tts_files_database['audio'])} 个")
        print(f"   - 参考文本: {len(self.tts_files_database['text'])} 个")

        return True

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
            if self.tts_files_database["gpt"]:
                first_gpt = list(self.tts_files_database["gpt"].values())[0]
                os.environ["gpt_path"] = first_gpt
                print(f"📌 默认GPT模型: {os.path.basename(first_gpt)}")

            if self.tts_files_database["sovits"]:
                first_sovits = list(self.tts_files_database["sovits"].values())[0]
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
            ref_text_content = self._get_cached_text(ref_text_path)

            # 检查函数是否可用
            if 'get_tts_wav' not in self.tts_modules:
                with self.is_tts_synthesizing_lock:
                    self.is_tts_synthesizing = False
                return False, "TTS合成函数未初始化"

            # 清理文本
            cleaned_text = self._clean_text_for_tts(text)

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
                    with self.tts_synthesized_files_lock:
                        self.tts_synthesized_files.append((output_wav, os.path.basename(output_wav)))

                        # 自动播放
                        if auto_play:
                            def play_thread_func():
                                self.play_audio_file(output_wav)

                            self.executor.submit(play_thread_func)

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

    def _clean_text_for_tts(self, text: str) -> str:
        """清理文本，但不丢失开头部分"""
        if not text:
            return "你好，我是小芸，很高兴为您服务"

        # 保存原始文本以便后续处理
        original_text = text

        # 1. 移除代码块标记
        text = re.sub(r'```[a-zA-Z]*\n?', '', text)
        text = re.sub(r'```', '', text)

        # 2. 移除URL和特殊标记，但保留中文标点
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\[.*?\]', '', text)  # 移除方括号内容

        # 3. 保留中文标点：，。！？；："'
        text = re.sub(r'[^\w\u4e00-\u9fff\s\.,，。!！?？:：;；、\'\"\(\)（）《》【】\-]', '', text)

        # 4. 移除多余空格，但保留一个空格
        text = ' '.join(text.split())

        # 5. 检查清理后的文本长度
        cleaned_text = text.strip()

        # 检查是否主要是英文或特殊字符
        chinese_char_count = len([c for c in cleaned_text if '\u4e00' <= c <= '\u9fff'])
        total_char_count = len(cleaned_text)

        # 如果中文字符占比太低或文本太短，使用兜底文本
        if total_char_count == 0 or (total_char_count > 0 and chinese_char_count / total_char_count < 0.3) or len(cleaned_text) < 3:
            print(f"⚠️  清理后的文本质量不佳（中文字符占比: {chinese_char_count}/{total_char_count}），使用兜底文本")
            # 使用更长的兜底文本，确保GPT-SoVITS能正常处理
            return "你好，我是小芸，很高兴为您服务"

        return cleaned_text

    def play_audio_file(self, audio_path: str):
        """播放指定的音频文件"""
        if not self.audio_player:
            print("❌ 音频播放器未初始化")
            return

        with self.is_playing_audio_lock:
            if self.is_playing_audio:
                print("⚠️ 已有音频正在播放，跳过本次播放请求")
                return
            self.is_playing_audio = True

        if not os.path.exists(audio_path):
            print(f"❌ 音频文件不存在：{audio_path}")
            with self.is_playing_audio_lock:
                self.is_playing_audio = False
            return

        try:
            # 打开音频文件
            wf = wave.open(audio_path, 'rb')

            # 创建音频流
            stream = self.audio_player.open(
                format=self.audio_player.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )

            # 分块播放音频（检查播放状态）
            chunk = 1024
            data = wf.readframes(chunk)

            while data:
                with self.is_playing_audio_lock:
                    if not self.is_playing_audio:
                        break
                stream.write(data)
                data = wf.readframes(chunk)

            # 清理资源
            stream.stop_stream()
            stream.close()
            wf.close()

        except Exception as e:
            print(f"❌ 播放失败：{e}")
            traceback.print_exc()
        finally:
            # 释放播放锁
            with self.is_playing_audio_lock:
                self.is_playing_audio = False

    def stop_current_audio_playback(self) -> bool:
        """停止当前正在播放的音频"""
        with self.is_playing_audio_lock:
            if self.is_playing_audio:
                self.is_playing_audio = False
                print("⏹️ 正在停止音频播放...")
                return True
            else:
                return False

    def load_synthesized_files(self) -> List[Tuple[str, str]]:
        """加载已合成音频文件"""
        with self.tts_synthesized_files_lock:
            self.tts_synthesized_files = []
            output_dir = self.default_tts_config["output_path"]
            if os.path.exists(output_dir):
                wav_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
                for wav_file in sorted(wav_files, reverse=True):
                    abs_path = os.path.join(output_dir, wav_file)
                    self.tts_synthesized_files.append((abs_path, wav_file))
        return self.tts_synthesized_files

    def set_current_model(self, model_type: str, filename: str) -> bool:
        """设置当前选中的模型"""
        with self.current_models_lock:
            if model_type == "gpt":
                if filename in self.tts_files_database["gpt"]:
                    self.current_gpt_model = self.tts_files_database["gpt"][filename]
                    return True
            elif model_type == "sovits":
                if filename in self.tts_files_database["sovits"]:
                    self.current_sovits_model = self.tts_files_database["sovits"][filename]
                    return True
            elif model_type == "audio":
                if filename in self.tts_files_database["audio"]:
                    self.current_ref_audio = self.tts_files_database["audio"][filename]
                    return True
            elif model_type == "text":
                if filename in self.tts_files_database["text"]:
                    self.current_ref_text = self.tts_files_database["text"][filename]
                    return True
        return False

    def get_current_model(self, model_type: str) -> Optional[str]:
        """获取当前选中的模型"""
        with self.current_models_lock:
            if model_type == "gpt":
                return self.current_gpt_model
            elif model_type == "sovits":
                return self.current_sovits_model
            elif model_type == "audio":
                return self.current_ref_audio
            elif model_type == "text":
                return self.current_ref_text
        return None

    def get_model_filename(self, model_type: str) -> str:
        """获取当前选中模型的文件名"""
        model_path = self.get_current_model(model_type)
        if model_path:
            return os.path.basename(model_path)
        return "未选择"

    def cleanup(self):
        """清理TTS资源"""
        print("🧹 清理TTS资源...")

        # 停止音频播放
        self.stop_current_audio_playback()

        # 清理音频播放器
        if self.audio_player:
            try:
                self.audio_player.terminate()
            except:
                pass




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
                self.base_url = "https://open.bigmodel.cn/api/paas/v4"
                self.model = "autoglm-phone"
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

    def detect_devices(self) -> List[str]:
        """检测可用设备"""
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

        # 1. 使用glm-4.7-flash进行任务识别
        task_info = self.task_recognizer.recognize_task_intent(user_input)
        task_type = task_info["task_type"]
        target_app = task_info["target_app"]
        target_object = task_info["target_object"]
        is_auto = task_info["is_auto"]

        print(f"📋 识别结果：任务类型={task_type}, APP={target_app}, 对象={target_object}, 持续={is_auto}\n")

        # 2. 如果glm-4.7-flash没有提取到APP和对象，尝试简单提取
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
        try:
            # 获取历史自由聊天记录
            free_chat_history = self.file_manager.get_recent_free_chats(limit=5)

            # 获取永久记忆
            forever_memory_content = self.file_manager.read_forever_memory()

            # 构建上下文
            context_prompt = ""
            if free_chat_history:
                context_prompt = "\n\n=== 历史对话（最近5条） ===\n"
                for i, chat in enumerate(free_chat_history):
                    context_prompt += f"\n{i + 1}. 用户: {chat.get('user_input', '')}\n"
                    context_prompt += f"   你: {chat.get('assistant_reply', '')}\n"

            # 构建系统提示词
            system_prompt = f"""你是一个友好的助手，名字叫'小芸'（不用刻意用"小芸："放在对话开头做标注），性别为女，请用自然又俏皮可爱的方式回应用户。

你有记忆功能，可以记住之前的对话内容。以下是你们之前的对话记录（最近5条）：
{context_prompt}
{forever_memory_content}

请基于以上历史对话和用户当前的问题，生成一个连贯、友好的回复。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task}
            ]

            response = self.zhipu_client.chat.completions.create(
                model=ZHIPU_CHAT_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            reply = response.choices[0].message.content.strip()

            # 语音播报回复内容（使用智能合成）
            if self.tts_manager.tts_enabled and len(reply) > 5:
                def speak_reply():
                    try:
                        # 使用智能语音合成
                        self.tts_manager.speak_text_intelligently(reply)
                    except Exception as e:
                        print(f"❌ 语音播报失败: {e}")

                # 异步播报，延迟0.5秒避免阻塞
                threading.Timer(0.5, speak_reply).start()

            # 保存到对话历史
            session_data = {
                "type": "free_chat",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "user_input": task,
                "assistant_reply": reply,
                "model_used": ZHIPU_CHAT_MODEL,
                "used_forever_memory": forever_memory_content != ""
            }
            self.file_manager.save_conversation_history(session_data)

            return reply

        except Exception as e:
            error_msg = f"❌ 聊天失败：{str(e)}"
            print(error_msg)
            traceback.print_exc()
            return error_msg

    def _handle_basic_operation(self, task: str, args, device_id: str) -> str:
        """处理基础操作"""
        print(f"📱 执行：{task}\n")

        try:
            # 获取执行结果
            result = self.agent_executor.phone_agent_exec(task, args, "basic", device_id)

            # 提取详细信息
            detailed_info = ""

            # 处理不同类型的返回值
            if isinstance(result, str):
                detailed_info = result
            elif isinstance(result, (list, tuple)):
                # 从列表/元组中提取字符串
                for item in result:
                    if isinstance(item, str) and item.strip():
                        detailed_info = item
                        break

            # 简化详细信息的长度
            if detailed_info:
                # 取第一句话或前100个字符
                if len(detailed_info) > 100:
                    short_info = detailed_info[:100] + "..."
                else:
                    short_info = detailed_info
            else:
                short_info = task

            # 检查执行结果
            if ("失败" in str(result) or "错误" in str(result) or
                    "失败" in short_info or "错误" in short_info):
                return_msg = f"❌ 操作失败"
            else:
                return_msg = f"✅ 操作完成"

                # TTS语音播报
                if self.tts_manager.tts_enabled and short_info and len(short_info) > 2:
                    def speak_result():
                        try:
                            # 清理消息用于TTS
                            cleaned_msg = self.tts_manager._clean_text_for_tts(short_info)
                            # 使用智能语音合成
                            self.tts_manager.speak_text_intelligently(cleaned_msg)
                        except Exception as e:
                            print(f"❌ 语音播报失败: {e}")

                    # 异步播报
                    threading.Thread(target=speak_result, daemon=True).start()

            return return_msg

        except Exception as e:
            error_msg = f"❌ 操作失败：{str(e)}"
            print(error_msg)
            traceback.print_exc()
            return error_msg

    def _handle_single_reply(self, task: str, args, target_app: str, target_object: str,
                             device_id: str) -> str:
        """处理单次回复"""
        print(f"\n🔄 启动单次回复流程")
        print(f"\n🎯 目标：{target_app} -> {target_object}\n")
        print()

        try:
            # 使用TerminableContinuousReplyManager
            from .agent_core import TerminableContinuousReplyManager
            manager = TerminableContinuousReplyManager(args, target_app, target_object, device_id,
                                                       self.zhipu_client, self.file_manager)

            # 1. 获取聊天记录
            current_record = manager.extract_chat_records()

            # 2. 保存原始记录到文件
            filename = self.file_manager.save_record_to_log(1, current_record, target_app, target_object)

            # 3. 解析消息
            messages = manager.parse_messages_simple(current_record)
            if messages:
                # 4. 判断消息归属
                other_messages, my_messages = manager.determine_message_ownership_fixed(messages)

                # 5. 检查是否有对方消息
                if other_messages:
                    # 只取最新的对方消息
                    latest_message = other_messages[-1]

                    # 6. 生成回复
                    # 历史消息：除了最新消息之外的其他消息
                    history_messages = other_messages[:-1] if len(other_messages) > 1 else []

                    reply_message = manager.generate_reply_for_latest_message(latest_message, history_messages)

                    if reply_message and len(reply_message) > 2:
                        # 7. 发送回复
                        success = manager.send_reply_message_fixed(reply_message)

                        if success:
                            # 保存到对话历史
                            session_data = {
                                "type": "chat_session",
                                "session_id": datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
                                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "target_app": target_app,
                                "target_object": target_object,
                                "cycle": 1,
                                "record_file": filename,
                                "reply_generated": reply_message,
                                "other_messages": [latest_message],
                                "sent_success": True
                            }
                            self.file_manager.save_conversation_history(session_data)

                            # 语音播报回复内容
                            if self.tts_manager.tts_enabled and len(reply_message) > 5:
                                def speak_reply():
                                    try:
                                        # 使用智能语音合成
                                        self.tts_manager.speak_text_intelligently(reply_message)
                                    except Exception as e:
                                        print(f"❌ 语音播报失败: {e}")

                                threading.Timer(0.5, speak_reply).start()

                            print(f"\n✅ 回复已发送：{reply_message[:50]}...\n")
                            return f"\n✅ 回复已发送：{reply_message[:50]}..."
                        else:
                            print(f"\n❌ 回复发送失败\n")
                            return f"\n❌ 回复发送失败"
                    else:
                        return f"⚠️  未能生成有效回复"
                else:
                    return f"⚠️  没有发现对方消息"
            else:
                return f"⚠️  未能解析到聊天记录"

        except Exception as e:
            print(f"❌ 单次回复失败: {e}\n")
            traceback.print_exc()
            return f"❌ 单次回复失败: {str(e)}"

    def _handle_continuous_reply(self, args, target_app: str, target_object: str,
                                 device_id: str) -> str:
        """处理持续回复"""
        # 检查设备连接
        if not device_id:
            print(f"❌ 设备未连接\n")
            return "❌ 设备未连接"

        # 使用TerminableContinuousReplyManager
        try:
            from .agent_core import TerminableContinuousReplyManager
            manager = TerminableContinuousReplyManager(
                args, target_app, target_object, device_id,
                self.zhipu_client, self.file_manager,
                terminate_flag=None  # 由控制器传递
            )

            # 确保manager有所有必要的方法
            self._ensure_manager_methods(manager)

            success = manager.run_continuous_loop()

            if success:
                return f"✅ 持续回复完成"
            else:
                return f"⏹️  持续回复已终止"
        except Exception as e:
            print(f"❌ 创建持续回复管理器失败: {e}\n")
            import traceback
            traceback.print_exc()
            return f"❌ 持续回复失败: {str(e)}"

    def _ensure_manager_methods(self, manager):
        """确保管理器有所有必要的方法"""
        # 检查并添加缺失的方法
        if not hasattr(manager, 'parse_messages_simple'):
            print("⚠️  添加缺失的parse_messages_simple方法到管理器")

            def parse_messages_simple(record):
                """解析消息的简化方法"""
                messages = []
                if not record:
                    return messages

                # 这里是简化的解析逻辑
                # 实际应该根据你的聊天记录格式来解析
                lines = record.split('\n')
                for line in lines:
                    line = line.strip()
                    if '内容：' in line:
                        messages.append(line)

                return messages

            manager.parse_messages_simple = parse_messages_simple

        if not hasattr(manager, 'determine_message_ownership_fixed'):
            print("⚠️  警告：管理器缺少determine_message_ownership_fixed方法")

    def _handle_complex_operation(self, task: str, args, device_id: str) -> str:
        """处理复杂操作"""
        print(f"⚙️  执行复杂操作：{task}\n")

        try:
            result, _ = self.agent_executor.phone_agent_exec(task, args, "complex", device_id)

            # 确保结果有换行符
            if result:
                result = result.strip()
                if not result.startswith('\n'):
                    result = '\n' + result
                if not result.endswith('\n'):
                    result = result + '\n'

            # 检查执行结果
            if "失败" in result or "错误" in result:
                return_msg = f"❌ 操作失败：{result}..."
            else:
                # 提取成功消息部分
                success_msg = result.strip()
                # 移除开头的 ✅ 操作完成： 前缀
                if success_msg.startswith("✅ 操作完成："):
                    success_msg = success_msg.replace("✅ 操作完成：", "")

                return_msg = f"✅ 操作完成：{result}..."

                # TTS语音播报回复内容（与自由聊天和单次回复保持一致）
                if self.tts_manager.tts_enabled and len(success_msg) > 5:
                    def speak_result():
                        # 检查是否有参考音频和文本
                        ref_audio = self.tts_manager.get_current_model("audio")
                        ref_text = self.tts_manager.get_current_model("text")

                        if ref_audio and ref_text:
                            # 清理消息用于TTS（使用与自由聊天相同的清理方法）
                            cleaned_msg = self.tts_manager._clean_text_for_tts(success_msg)
                            self.tts_synthesize_text(
                                cleaned_msg,
                                ref_audio,
                                ref_text,
                                auto_play=True
                            )
                        else:
                            print("⚠️  无法语音播报：未选择参考音频或文本")

                    # 异步播报（与自由聊天和单次回复保持一致）
                    threading.Thread(target=speak_result, daemon=True).start()

            return return_msg

        except Exception as e:
            error_msg = f"❌ 操作失败：{str(e)}"
            print(error_msg)
            return error_msg

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