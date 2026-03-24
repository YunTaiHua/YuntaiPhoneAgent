#!/usr/bin/env python3
"""
工具函数模块
使用 pathlib 进行跨平台路径处理
"""
import sys
import shutil
import subprocess
import openai
from pathlib import Path
from typing import Tuple, List




class Utils:
    def __init__(self):
        pass

    def enable_windows_color(self):
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass

    def check_system_requirements(self) -> bool:
        all_passed = True

        if shutil.which("adb") is None:
            all_passed = False
        else:
            try:
                result = subprocess.run(
                    ["adb", "version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding="utf-8",
                    errors="ignore"
                )
                if result.returncode == 0:
                    print("")
                else:
                    all_passed = False
            except Exception:
                all_passed = False

        return all_passed

    def check_hdc(self) -> bool:
        """检查HDC工具是否可用"""
        if shutil.which("hdc") is None:
            return False
        try:
            result = subprocess.run(
                ["hdc", "-v"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
                errors="ignore"
            )
            return result.returncode == 0
        except Exception:
            return False

    def check_model_api(self, base_url: str, model_name: str, api_key: str = "EMPTY") -> bool:
        try:
            client = openai.OpenAI(base_url=base_url, api_key=api_key, timeout=30.0)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                temperature=0.0,
                stream=False,
            )
            if response.choices and len(response.choices) > 0:
                return True
            else:
                return False
        except Exception as e:
            return False


import threading

tts_page_synthesizing = False

is_tts_synthesizing_lock = threading.Lock()
is_tts_synthesizing = False
is_playing_audio_lock = threading.Lock()
is_playing_audio = False
tts_synthesized_files_lock = threading.Lock()
tts_synthesized_files: List[Tuple[str, str]] = []


def load_synthesized_files(output_dir: str) -> List[Tuple[str, str]]:
    """加载已合成音频文件"""
    global tts_synthesized_files
    with tts_synthesized_files_lock:
        tts_synthesized_files = []
        output_path = Path(output_dir)
        if output_path.exists():
            wav_files = [f for f in output_path.iterdir() if f.is_file() and f.suffix == '.wav']
            for wav_file in sorted(wav_files, key=lambda x: x.name, reverse=True):
                tts_synthesized_files.append((str(wav_file), wav_file.name))
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
