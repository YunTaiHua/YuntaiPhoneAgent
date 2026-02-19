#!/usr/bin/env python3
"""
工具函数模块
"""
import sys
import shutil
import subprocess
import openai
from typing import Tuple




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
        #print(f"\n🔍 检查系统要求...")
        all_passed = True

        #print(f"\n1. 检查ADB安装...", end=" ")
        if shutil.which("adb") is None:
            #print("\n❌ 失败")
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
                    #print("\n❌ 失败")
                    all_passed = False
            except Exception:
                #print("\n❌ 失败")
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
        #print(f"\n🔍 检查模型API...")
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
                #print("✅ 正常")
                return True
            else:
                #print("\n❌ 失败")
                return False
        except Exception as e:
            #print(f"\n❌ 失败: {e}")
            return False


# ==================== TTS 相关工具函数 ====================

import os
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