#!/usr/bin/env python3
"""
工具函数模块
使用 pathlib 进行跨平台路径处理

该模块提供系统工具函数和 TTS（文本转语音）状态管理功能。
主要功能包括：
1. 系统需求检查（ADB、HDC、模型API等）
2. Windows控制台颜色支持
3. TTS状态统一管理（使用单例模式封装）
"""
import sys
import shutil
import subprocess
import logging
import openai
import threading
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from yuntai.core.config import (
    ADB_CHECK_TIMEOUT,
    HDC_CHECK_TIMEOUT,
    API_CHECK_TIMEOUT,
    API_CHECK_MAX_TOKENS,
)

logger = logging.getLogger(__name__)


class Utils:
    """系统工具类 - 提供系统环境检查和工具函数"""

    def __init__(self):
        """初始化工具类"""
        pass

    def enable_windows_color(self) -> None:
        """
        启用Windows控制台颜色支持
        
        在Windows系统上启用ANSI颜色代码支持，
        使得控制台输出可以显示彩色文本。
        """
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except (OSError, AttributeError) as e:
                logger.debug(f"设置Windows控制台颜色失败: {e}")

    def check_system_requirements(self) -> bool:
        """
        检查系统运行环境要求
        
        验证ADB等必要工具是否可用，确保系统满足运行条件。
        
        Returns:
            bool: 所有检查是否通过
        """
        all_passed = True

        # 检查ADB工具是否可用
        if shutil.which("adb") is None:
            all_passed = False
        else:
            try:
                result = subprocess.run(
                    ["adb", "version"],
                    capture_output=True,
                    text=True,
                    timeout=ADB_CHECK_TIMEOUT,
                    encoding="utf-8",
                    errors="ignore"
                )
                if result.returncode == 0:
                    print("")
                else:
                    all_passed = False
            except Exception:
                logger.debug("ADB 版本检查异常")
                all_passed = False

        return all_passed

    def check_hdc(self) -> bool:
        """
        检查HDC工具是否可用
        
        HDC是HarmonyOS设备的调试工具。
        
        Returns:
            bool: HDC工具是否可用
        """
        if shutil.which("hdc") is None:
            return False
        try:
            result = subprocess.run(
                ["hdc", "-v"],
                capture_output=True,
                text=True,
                timeout=HDC_CHECK_TIMEOUT,
                encoding="utf-8",
                errors="ignore"
            )
            return result.returncode == 0
        except Exception:
            logger.debug("HDC 版本检查异常")
            return False

    def check_model_api(self, base_url: str, model_name: str, api_key: str = "EMPTY") -> bool:
        """
        检查模型API是否可用
        
        通过发送简单的测试请求验证API连接和密钥有效性。
        
        Args:
            base_url: API基础URL
            model_name: 模型名称
            api_key: API密钥，默认为"EMPTY"
            
        Returns:
            bool: API是否可用
        """
        try:
            client = openai.OpenAI(base_url=base_url, api_key=api_key, timeout=API_CHECK_TIMEOUT)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=API_CHECK_MAX_TOKENS,
                temperature=0.0,
                stream=False,
            )
            if response.choices and len(response.choices) > 0:
                return True
            else:
                return False
        except Exception as e:
            logger.debug(f"模型API检查异常: {e}")
            return False


class TTSStateManager:
    """
    TTS（文本转语音）状态管理器 - 单例模式
    
    统一管理TTS相关的所有状态变量，避免全局变量污染。
    提供线程安全的状态访问和修改方法。
    """
    
    _instance: Optional['TTSStateManager'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'TTSStateManager':
        """
        单例模式实现 - 确保全局只有一个实例
        
        Returns:
            TTSStateManager: 单例实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化TTS状态管理器（仅执行一次）"""
        if self._initialized:
            return
            
        # TTS页面合成状态
        self._tts_page_synthesizing: bool = False
        
        # TTS合成状态和锁
        self._is_tts_synthesizing: bool = False
        self._is_tts_synthesizing_lock: threading.Lock = threading.Lock()
        
        # 音频播放状态和锁
        self._is_playing_audio: bool = False
        self._is_playing_audio_lock: threading.Lock = threading.Lock()
        
        # 已合成文件列表和锁
        self._tts_synthesized_files: List[Tuple[str, str]] = []
        self._tts_synthesized_files_lock: threading.Lock = threading.Lock()
        
        self._initialized = True
    
    @property
    def tts_page_synthesizing(self) -> bool:
        """获取TTS页面是否正在合成"""
        return self._tts_page_synthesizing
    
    @tts_page_synthesizing.setter
    def tts_page_synthesizing(self, value: bool) -> None:
        """设置TTS页面合成状态"""
        self._tts_page_synthesizing = value
    
    @property
    def is_tts_synthesizing(self) -> bool:
        """获取TTS是否正在合成（线程安全）"""
        with self._is_tts_synthesizing_lock:
            return self._is_tts_synthesizing
    
    @is_tts_synthesizing.setter
    def is_tts_synthesizing(self, value: bool) -> None:
        """设置TTS合成状态（线程安全）"""
        with self._is_tts_synthesizing_lock:
            self._is_tts_synthesizing = value
    
    @property
    def is_playing_audio(self) -> bool:
        """获取是否正在播放音频（线程安全）"""
        with self._is_playing_audio_lock:
            return self._is_playing_audio
    
    @is_playing_audio.setter
    def is_playing_audio(self, value: bool) -> None:
        """设置音频播放状态（线程安全）"""
        with self._is_playing_audio_lock:
            self._is_playing_audio = value
    
    def get_synthesized_files(self) -> List[Tuple[str, str]]:
        """
        获取已合成文件列表（线程安全）
        
        Returns:
            List[Tuple[str, str]]: 已合成文件列表，每个元素为(文件路径, 文件名)
        """
        with self._tts_synthesized_files_lock:
            return list(self._tts_synthesized_files)
    
    def set_synthesized_files(self, files: List[Tuple[str, str]]) -> None:
        """
        设置已合成文件列表（线程安全）
        
        Args:
            files: 要设置的文件列表
        """
        with self._tts_synthesized_files_lock:
            self._tts_synthesized_files = list(files)
    
    def add_synthesized_file(self, file_path: str, file_name: str) -> None:
        """
        添加已合成文件（线程安全）
        
        Args:
            file_path: 文件完整路径
            file_name: 文件名
        """
        with self._tts_synthesized_files_lock:
            self._tts_synthesized_files.append((file_path, file_name))
    
    def clear_synthesized_files(self) -> None:
        """清空已合成文件列表（线程安全）"""
        with self._tts_synthesized_files_lock:
            self._tts_synthesized_files.clear()
    
    def get_synthesized_files_count(self) -> int:
        """
        获取已合成文件数量（线程安全）
        
        Returns:
            int: 已合成文件数量
        """
        with self._tts_synthesized_files_lock:
            return len(self._tts_synthesized_files)
    
    def get_status_dict(self) -> Dict[str, Any]:
        """
        获取完整的TTS状态字典
        
        Returns:
            Dict[str, Any]: 包含所有TTS状态的字典
        """
        return {
            "tts_page_synthesizing": self._tts_page_synthesizing,
            "is_tts_synthesizing": self.is_tts_synthesizing,
            "is_playing_audio": self.is_playing_audio,
            "tts_synthesized_files_count": self.get_synthesized_files_count(),
        }
    
    def reset_all(self) -> None:
        """重置所有TTS状态到初始值"""
        self._tts_page_synthesizing = False
        self.is_tts_synthesizing = False
        self.is_playing_audio = False
        self.clear_synthesized_files()


# 全局TTS状态管理器实例（单例）
_tts_state_manager: Optional[TTSStateManager] = None


def get_tts_state_manager() -> TTSStateManager:
    """
    获取TTS状态管理器实例（懒加载）
    
    Returns:
        TTSStateManager: 全局TTS状态管理器单例
    """
    global _tts_state_manager
    if _tts_state_manager is None:
        _tts_state_manager = TTSStateManager()
    return _tts_state_manager


def load_synthesized_files(output_dir: str) -> List[Tuple[str, str]]:
    """
    加载已合成音频文件
    
    从指定目录扫描并加载所有.wav音频文件。
    
    Args:
        output_dir: 输出目录路径
        
    Returns:
        List[Tuple[str, str]]: 已合成文件列表，按文件名降序排列
    """
    manager = get_tts_state_manager()
    manager.clear_synthesized_files()
    
    output_path = Path(output_dir)
    if output_path.exists():
        wav_files = [f for f in output_path.iterdir() if f.is_file() and f.suffix == '.wav']
        for wav_file in sorted(wav_files, key=lambda x: x.name, reverse=True):
            manager.add_synthesized_file(str(wav_file), wav_file.name)
    
    return manager.get_synthesized_files()


def get_current_tts_status() -> Dict[str, Any]:
    """
    获取当前TTS状态
    
    Returns:
        Dict[str, Any]: 包含TTS所有状态的字典
    """
    manager = get_tts_state_manager()
    return manager.get_status_dict()


def cleanup_tts_resources() -> None:
    """
    清理TTS资源
    
    重置所有TTS相关状态，清空已合成文件列表，
    确保资源被正确释放。
    """
    manager = get_tts_state_manager()
    manager.reset_all()
    logger.info("TTS资源已清理完成")
