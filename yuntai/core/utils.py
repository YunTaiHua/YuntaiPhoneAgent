"""
工具函数模块
============

本模块提供系统工具函数和 TTS（文本转语音）状态管理功能。
使用 pathlib 进行跨平台路径处理。

主要功能：
    - 系统需求检查（ADB、HDC、模型 API 等）
    - Windows 控制台颜色支持
    - TTS 状态统一管理（使用单例模式封装）
    - 已合成音频文件加载

类说明：
    - Utils: 系统工具类，提供环境检查功能
    - TTSStateManager: TTS 状态管理器（单例模式）

函数说明：
    - get_tts_state_manager: 获取 TTS 状态管理器实例
    - load_synthesized_files: 加载已合成音频文件
    - get_current_tts_status: 获取当前 TTS 状态
    - cleanup_tts_resources: 清理 TTS 资源

使用示例：
    >>> from yuntai.core import Utils, get_tts_state_manager
    >>> 
    >>> # 检查系统环境
    >>> utils = Utils()
    >>> utils.check_system_requirements()
    >>> 
    >>> # 获取 TTS 状态
    >>> manager = get_tts_state_manager()
    >>> status = manager.get_status_dict()
"""
from __future__ import annotations

import sys
import shutil
import subprocess
import logging
import openai
import threading
from pathlib import Path

from yuntai.core.config import (
    ADB_CHECK_TIMEOUT,
    HDC_CHECK_TIMEOUT,
    API_CHECK_TIMEOUT,
    API_CHECK_MAX_TOKENS,
)

# 配置模块级日志记录器
logger = logging.getLogger(__name__)


class Utils:
    """
    系统工具类
    
    提供系统环境检查和工具函数。
    
    使用示例：
        >>> utils = Utils()
        >>> utils.enable_windows_color()
        >>> if utils.check_system_requirements():
        ...     print("系统环境检查通过")
    """

    def __init__(self):
        """
        初始化工具类
        
        工具类无需初始化参数，所有方法都是实例方法。
        """
        pass

    def enable_windows_color(self) -> None:
        """
        启用 Windows 控制台颜色支持
        
        在 Windows 系统上启用 ANSI 颜色代码支持，
        使得控制台输出可以显示彩色文本。
        对于非 Windows 系统不执行任何操作。
        """
        if sys.platform == "win32":
            try:
                import ctypes
                # 获取 Windows API 句柄
                kernel32 = ctypes.windll.kernel32
                # 设置控制台模式以支持 ANSI 颜色
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                logger.debug("Windows 控制台颜色支持已启用")
            except (OSError, AttributeError) as e:
                # 设置失败时记录调试日志
                logger.debug("设置 Windows 控制台颜色失败: %s", str(e))

    def check_system_requirements(self) -> bool:
        """
        检查系统运行环境要求
        
        验证 ADB 等必要工具是否可用，确保系统满足运行条件。
        
        Returns:
            bool: 所有检查是否通过
        
        使用示例：
            >>> utils = Utils()
            >>> if not utils.check_system_requirements():
            ...     print("请安装 ADB 工具")
        """
        all_passed = True

        # 检查 ADB 工具是否可用
        if shutil.which("adb") is None:
            # ADB 未安装
            logger.warning("ADB 工具未安装")
            all_passed = False
        else:
            # ADB 已安装，验证版本
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
                    # ADB 版本检查通过
                    print("")
                    logger.debug("ADB 版本检查通过")
                else:
                    # ADB 版本检查失败
                    logger.warning("ADB 版本检查失败")
                    all_passed = False
            except subprocess.TimeoutExpired as e:
                logger.warning("ADB 版本检查超时: %s", e)
                all_passed = False
            except FileNotFoundError as e:
                logger.warning("ADB 命令未找到: %s", e)
                all_passed = False
            except Exception as e:
                logger.warning("ADB 版本检查异常: %s", e)
                all_passed = False

        return all_passed

    def check_hdc(self) -> bool:
        """
        检查 HDC 工具是否可用
        
        HDC 是 HarmonyOS 设备的调试工具。
        
        Returns:
            bool: HDC 工具是否可用
        
        使用示例：
            >>> utils = Utils()
            >>> if utils.check_hdc():
            ...     print("HDC 工具可用")
        """
        # 检查 HDC 是否在 PATH 中
        if shutil.which("hdc") is None:
            logger.debug("HDC 工具未安装")
            return False
        
        # 验证 HDC 版本
        try:
            result = subprocess.run(
                ["hdc", "-v"],
                capture_output=True,
                text=True,
                timeout=HDC_CHECK_TIMEOUT,
                encoding="utf-8",
                errors="ignore"
            )
            if result.returncode == 0:
                logger.debug("HDC 版本检查通过")
                return True
            else:
                logger.debug("HDC 版本检查失败")
                return False
        except subprocess.TimeoutExpired as e:
            logger.warning("HDC 版本检查超时: %s", e)
            return False
        except FileNotFoundError as e:
            logger.warning("HDC 命令未找到: %s", e)
            return False
        except Exception as e:
            logger.warning("HDC 版本检查异常: %s", e)
            return False

    def check_model_api(
        self,
        base_url: str,
        model_name: str,
        api_key: str = "EMPTY"
    ) -> bool:
        """
        检查模型 API 是否可用
        
        通过发送简单的测试请求验证 API 连接和密钥有效性。
        
        Args:
            base_url: API 基础 URL
            model_name: 模型名称
            api_key: API 密钥，默认为 "EMPTY"
        
        Returns:
            bool: API 是否可用
        
        使用示例：
            >>> utils = Utils()
            >>> if utils.check_model_api("http://localhost:8000/v1", "model"):
            ...     print("API 可用")
        """
        try:
            # 创建 OpenAI 客户端
            client = openai.OpenAI(
                base_url=base_url,
                api_key=api_key,
                timeout=API_CHECK_TIMEOUT
            )
            
            # 发送测试请求
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=API_CHECK_MAX_TOKENS,
                temperature=0.0,
                stream=False,
            )
            
            # 检查响应是否有效
            if response.choices and len(response.choices) > 0:
                logger.debug("模型 API 检查通过")
                return True
            else:
                logger.debug("模型 API 响应无效")
                return False
        except Exception as e:
            logger.debug("模型 API 检查异常: %s", str(e))
            return False


class TTSStateManager:
    """
    TTS（文本转语音）状态管理器
    
    使用单例模式统一管理 TTS 相关的所有状态变量，避免全局变量污染。
    提供线程安全的状态访问和修改方法。
    
    Attributes:
        _tts_page_synthesizing: TTS 页面是否正在合成
        _is_tts_synthesizing: TTS 是否正在合成
        _is_playing_audio: 是否正在播放音频
        _tts_synthesized_files: 已合成文件列表
    
    使用示例：
        >>> manager = TTSStateManager()
        >>> manager.is_tts_synthesizing = True
        >>> status = manager.get_status_dict()
    """
    
    # 类变量：单例实例
    _instance: TTSStateManager | None = None
    # 类变量：线程锁
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> TTSStateManager:
        """
        单例模式实现
        
        确保全局只有一个 TTSStateManager 实例。
        使用双重检查锁定模式保证线程安全。
        
        Returns:
            TTSStateManager: 单例实例
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    # 创建实例
                    cls._instance = super().__new__(cls)
                    # 标记未初始化
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """
        初始化 TTS 状态管理器
        
        仅在首次创建时执行初始化。
        """
        # 检查是否已初始化
        if self._initialized:
            return
        
        logger.debug("初始化 TTSStateManager")
            
        # TTS 页面合成状态
        self._tts_page_synthesizing: bool = False
        
        # TTS 合成状态和锁
        self._is_tts_synthesizing: bool = False
        self._is_tts_synthesizing_lock: threading.Lock = threading.Lock()
        
        # 音频播放状态和锁
        self._is_playing_audio: bool = False
        self._is_playing_audio_lock: threading.Lock = threading.Lock()
        
        # 已合成文件列表和锁
        self._tts_synthesized_files: list[tuple[str, str]] = []
        self._tts_synthesized_files_lock: threading.Lock = threading.Lock()
        
        # 标记已初始化
        self._initialized = True
    
    @property
    def tts_page_synthesizing(self) -> bool:
        """
        获取 TTS 页面是否正在合成
        
        Returns:
            bool: 是否正在合成
        """
        return self._tts_page_synthesizing
    
    @tts_page_synthesizing.setter
    def tts_page_synthesizing(self, value: bool) -> None:
        """
        设置 TTS 页面合成状态
        
        Args:
            value: 是否正在合成
        """
        self._tts_page_synthesizing = value
        logger.debug("TTS 页面合成状态: %s", value)
    
    @property
    def is_tts_synthesizing(self) -> bool:
        """
        获取 TTS 是否正在合成（线程安全）
        
        Returns:
            bool: 是否正在合成
        """
        with self._is_tts_synthesizing_lock:
            return self._is_tts_synthesizing
    
    @is_tts_synthesizing.setter
    def is_tts_synthesizing(self, value: bool) -> None:
        """
        设置 TTS 合成状态（线程安全）
        
        Args:
            value: 是否正在合成
        """
        with self._is_tts_synthesizing_lock:
            self._is_tts_synthesizing = value
        logger.debug("TTS 合成状态: %s", value)
    
    @property
    def is_playing_audio(self) -> bool:
        """
        获取是否正在播放音频（线程安全）
        
        Returns:
            bool: 是否正在播放
        """
        with self._is_playing_audio_lock:
            return self._is_playing_audio
    
    @is_playing_audio.setter
    def is_playing_audio(self, value: bool) -> None:
        """
        设置音频播放状态（线程安全）
        
        Args:
            value: 是否正在播放
        """
        with self._is_playing_audio_lock:
            self._is_playing_audio = value
        logger.debug("音频播放状态: %s", value)
    
    def get_synthesized_files(self) -> list[tuple[str, str]]:
        """
        获取已合成文件列表（线程安全）
        
        Returns:
            list[tuple[str, str]]: 已合成文件列表，每个元素为 (文件路径, 文件名)
        """
        with self._tts_synthesized_files_lock:
            return list(self._tts_synthesized_files)
    
    def set_synthesized_files(self, files: list[tuple[str, str]]) -> None:
        """
        设置已合成文件列表（线程安全）
        
        Args:
            files: 要设置的文件列表
        """
        with self._tts_synthesized_files_lock:
            self._tts_synthesized_files = list(files)
        logger.debug("设置已合成文件列表，数量: %d", len(files))
    
    def add_synthesized_file(self, file_path: str, file_name: str) -> None:
        """
        添加已合成文件（线程安全）
        
        Args:
            file_path: 文件完整路径
            file_name: 文件名
        """
        with self._tts_synthesized_files_lock:
            self._tts_synthesized_files.append((file_path, file_name))
        logger.debug("添加已合成文件: %s", file_name)
    
    def clear_synthesized_files(self) -> None:
        """
        清空已合成文件列表（线程安全）
        """
        with self._tts_synthesized_files_lock:
            self._tts_synthesized_files.clear()
        logger.debug("已清空合成文件列表")
    
    def get_synthesized_files_count(self) -> int:
        """
        获取已合成文件数量（线程安全）
        
        Returns:
            int: 已合成文件数量
        """
        with self._tts_synthesized_files_lock:
            return len(self._tts_synthesized_files)
    
    def get_status_dict(self) -> dict[str, object]:
        """
        获取完整的 TTS 状态字典
        
        Returns:
            dict[str, object]: 包含所有 TTS 状态的字典
        """
        return {
            "tts_page_synthesizing": self._tts_page_synthesizing,
            "is_tts_synthesizing": self.is_tts_synthesizing,
            "is_playing_audio": self.is_playing_audio,
            "tts_synthesized_files_count": self.get_synthesized_files_count(),
        }
    
    def reset_all(self) -> None:
        """
        重置所有 TTS 状态到初始值
        
        清空所有状态变量和文件列表。
        """
        logger.info("重置所有 TTS 状态")
        self._tts_page_synthesizing = False
        self.is_tts_synthesizing = False
        self.is_playing_audio = False
        self.clear_synthesized_files()


# 全局 TTS 状态管理器实例（单例）
_tts_state_manager: TTSStateManager | None = None


def get_tts_state_manager() -> TTSStateManager:
    """
    获取 TTS 状态管理器实例（懒加载）
    
    使用懒加载模式，首次调用时才创建实例。
    
    Returns:
        TTSStateManager: 全局 TTS 状态管理器单例
    
    使用示例：
        >>> manager = get_tts_state_manager()
        >>> manager.is_tts_synthesizing = True
    """
    global _tts_state_manager
    if _tts_state_manager is None:
        _tts_state_manager = TTSStateManager()
        logger.debug("创建 TTSStateManager 实例")
    return _tts_state_manager


def load_synthesized_files(output_dir: str) -> list[tuple[str, str]]:
    """
    加载已合成音频文件
    
    从指定目录扫描并加载所有 .wav 音频文件。
    文件按名称降序排列。
    
    Args:
        output_dir: 输出目录路径
    
    Returns:
        list[tuple[str, str]]: 已合成文件列表，每个元素为 (文件路径, 文件名)
    
    使用示例：
        >>> files = load_synthesized_files("/path/to/output")
        >>> for path, name in files:
        ...     print(f"文件: {name}, 路径: {path}")
    """
    logger.info("加载已合成文件，目录: %s", output_dir)
    
    # 获取状态管理器
    manager = get_tts_state_manager()
    manager.clear_synthesized_files()
    
    # 检查目录是否存在
    output_path = Path(output_dir)
    if output_path.exists():
        # 扫描 .wav 文件
        wav_files = [f for f in output_path.iterdir() if f.is_file() and f.suffix == '.wav']
        
        # 按文件名降序排列并添加到列表
        for wav_file in sorted(wav_files, key=lambda x: x.name, reverse=True):
            manager.add_synthesized_file(str(wav_file), wav_file.name)
        
        logger.debug("找到 %d 个 .wav 文件", len(wav_files))
    
    return manager.get_synthesized_files()


def get_current_tts_status() -> dict[str, object]:
    """
    获取当前 TTS 状态
    
    Returns:
        dict[str, object]: 包含 TTS 所有状态的字典
    
    使用示例：
        >>> status = get_current_tts_status()
        >>> print(f"正在合成: {status['is_tts_synthesizing']}")
    """
    manager = get_tts_state_manager()
    return manager.get_status_dict()


def cleanup_tts_resources() -> None:
    """
    清理 TTS 资源
    
    重置所有 TTS 相关状态，清空已合成文件列表，
    确保资源被正确释放。
    
    使用示例：
        >>> cleanup_tts_resources()
    """
    manager = get_tts_state_manager()
    manager.reset_all()
    logger.info("TTS 资源已清理完成")
