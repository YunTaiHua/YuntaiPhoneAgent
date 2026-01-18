"""
工具函数模块
重构后的工具函数
"""

import os
import sys
import threading
from typing import List, Tuple

# 全局TTS合成标志
tts_page_synthesizing = False

# 状态变量
is_tts_synthesizing_lock = threading.Lock()
is_tts_synthesizing = False
is_playing_audio_lock = threading.Lock()
is_playing_audio = False
tts_synthesized_files_lock = threading.Lock()
tts_synthesized_files = []  # 存储合成的音频文件列表


def load_synthesized_files(output_dir: str) -> List[Tuple[str, str]]:
    """加载已合成音频文件"""
    global tts_synthesized_files
    with tts_synthesized_files_lock:
        tts_synthesized_files = []
        if os.path.exists(output_dir):
            wav_files = [f for f in os.listdir(output_dir) if f.endswith('.wav')]
            for wav_file in sorted(wav_files, reverse=True):
                abs_path = os.path.join(output_dir, wav_file)
                tts_synthesized_files.append((abs_path, wav_file))
    return tts_synthesized_files


def get_current_tts_status() -> dict:
    """获取当前TTS状态"""
    global tts_page_synthesizing, is_tts_synthesizing, is_playing_audio, tts_synthesized_files

    return {
        "tts_page_synthesizing": tts_page_synthesizing,
        "is_tts_synthesizing": is_tts_synthesizing,
        "is_playing_audio": is_playing_audio,
        "tts_synthesized_files_count": len(tts_synthesized_files),
    }


def cleanup_tts_resources():
    """清理TTS资源"""
    global tts_synthesized_files
    with tts_synthesized_files_lock:
        tts_synthesized_files.clear()