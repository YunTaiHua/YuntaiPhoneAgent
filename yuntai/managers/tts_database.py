"""
TTS 数据库管理器模块
====================

负责 TTS 文件扫描和数据库管理，使用 pathlib 进行跨平台路径处理。

主要功能:
    - init_tts_files_database: 初始化 TTS 文件数据库
    - get_cached_text: 获取缓存的文本内容
    - set_current_model: 设置当前选中的模型
    - get_current_model: 获取当前选中的模型
    - load_synthesized_files: 加载已合成音频文件

使用示例:
    >>> from yuntai.managers import TTSDatabaseManager
    >>> manager = TTSDatabaseManager(default_tts_config)
    >>> manager.init_tts_files_database()
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TTSDatabaseManager:
    """
    TTS 数据库管理器
    
    负责 TTS 文件扫描和数据库管理，支持模型文件、参考音频和参考文本的管理。
    
    Attributes:
        default_tts_config: 默认 TTS 配置
        tts_files_database: TTS 文件数据库，包含 gpt、sovits、audio、text 四类
        current_gpt_model: 当前选中的 GPT 模型
        current_sovits_model: 当前选中的 SoVITS 模型
        current_ref_audio: 当前选中的参考音频
        current_ref_text: 当前选中的参考文本
        tts_synthesized_files: 已合成的音频文件列表
        
    Args:
        default_tts_config: 默认 TTS 配置字典
    """

    def __init__(self, default_tts_config: dict[str, Any]) -> None:
        """
        初始化 TTS 数据库管理器

        Args:
            default_tts_config: 默认 TTS 配置
        """
        self.default_tts_config: dict[str, Any] = default_tts_config

        self.tts_files_database: dict[str, dict[str, str]] = {
            "gpt": {},
            "sovits": {},
            "audio": {},
            "text": {}
        }

        self._text_cache: dict[str, str] = {}
        self._cache_lock: threading.Lock = threading.Lock()

        self.current_gpt_model: str | None = None
        self.current_sovits_model: str | None = None
        self.current_ref_audio: str | None = None
        self.current_ref_text: str | None = None
        self.current_models_lock: threading.Lock = threading.Lock()

        self.tts_synthesized_files: list[tuple[str, str]] = []
        self.tts_synthesized_files_lock: threading.Lock = threading.Lock()
        logger.debug("TTSDatabaseManager 初始化完成")

    def init_tts_files_database(self) -> bool:
        """
        初始化 TTS 文件数据库
        
        扫描配置的目录，加载 GPT 模型、SoVITS 模型、参考音频和参考文本。
        
        Returns:
            初始化成功返回 True
        """
        print("🔍 初始化TTS文件数据库...")
        logger.info("开始初始化 TTS 文件数据库")

        for dir_key in ["gpt_model_dir", "sovits_model_dir", "ref_audio_root", "output_path"]:
            dir_path = Path(self.default_tts_config[dir_key])
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 确保目录存在: {dir_path}")
            logger.debug("确保目录存在: %s", dir_path)

        self.tts_files_database["gpt"] = {}
        gpt_model_dir = Path(self.default_tts_config["gpt_model_dir"])
        if gpt_model_dir.exists():
            for ckpt_file in gpt_model_dir.rglob("*.ckpt"):
                abs_path = ckpt_file.resolve()
                self.tts_files_database["gpt"][ckpt_file.name] = str(abs_path)
        else:
            print(f"⚠️  GPT模型目录不存在: {gpt_model_dir}")
            logger.warning("GPT 模型目录不存在: %s", gpt_model_dir)

        self.tts_files_database["sovits"] = {}
        sovits_model_dir = Path(self.default_tts_config["sovits_model_dir"])
        if sovits_model_dir.exists():
            for pth_file in sovits_model_dir.rglob("*.pth"):
                abs_path = pth_file.resolve()
                self.tts_files_database["sovits"][pth_file.name] = str(abs_path)
        else:
            print(f"⚠️  SoVITS模型目录不存在: {sovits_model_dir}")
            logger.warning("SoVITS 模型目录不存在: %s", sovits_model_dir)

        self.tts_files_database["audio"] = {}
        ref_audio_root = Path(self.default_tts_config["ref_audio_root"])
        if ref_audio_root.exists():
            for audio_file in ref_audio_root.rglob("*"):
                if audio_file.suffix.lower() in ('.wav', '.mp3', '.flac'):
                    abs_path = audio_file.resolve()
                    self.tts_files_database["audio"][audio_file.name] = str(abs_path)
        else:
            print(f"⚠️  参考音频目录不存在: {ref_audio_root}")
            logger.warning("参考音频目录不存在: %s", ref_audio_root)

        self.tts_files_database["text"] = {}
        ref_text_root = Path(self.default_tts_config["ref_text_root"])
        if ref_text_root.exists():
            for text_file in ref_text_root.rglob("*.txt"):
                abs_path = text_file.resolve()
                self.tts_files_database["text"][text_file.name] = str(abs_path)
        else:
            print(f"⚠️  参考文本目录不存在: {ref_text_root}")
            logger.warning("参考文本目录不存在: %s", ref_text_root)

        print("✅ 文件数据库初始化完成:")
        print(f"   - GPT模型: {len(self.tts_files_database['gpt'])} 个")
        print(f"   - SoVITS模型: {len(self.tts_files_database['sovits'])} 个")
        print(f"   - 参考音频: {len(self.tts_files_database['audio'])} 个")
        print(f"   - 参考文本: {len(self.tts_files_database['text'])} 个")
        logger.info("TTS 文件数据库初始化完成: GPT=%d, SoVITS=%d, Audio=%d, Text=%d",
                   len(self.tts_files_database['gpt']),
                   len(self.tts_files_database['sovits']),
                   len(self.tts_files_database['audio']),
                   len(self.tts_files_database['text']))

        return True

    def get_cached_text(self, file_path: str) -> str:
        """
        获取缓存的文本内容
        
        从缓存中读取文本内容，如果缓存未命中则从文件读取并缓存。
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            文本内容
            
        Raises:
            IOError: 文件读取失败
        """
        with self._cache_lock:
            if file_path in self._text_cache:
                logger.debug("从缓存获取文本: %s", file_path)
                return self._text_cache[file_path]
            try:
                text_file = Path(file_path)
                content = text_file.read_text(encoding="utf-8").strip()
                self._text_cache[file_path] = content
                logger.debug("从文件读取文本并缓存: %s", file_path)
                return content
            except IOError as e:
                print(f"❌ 读取文本文件失败: {file_path}, {e}")
                logger.error("读取文本文件失败: %s, %s", file_path, str(e))
                raise

    def set_current_model(self, model_type: str, filename: str) -> bool:
        """
        设置当前选中的模型
        
        Args:
            model_type: 模型类型 (gpt/sovits/audio/text)
            filename: 模型文件名
            
        Returns:
            设置成功返回 True，文件不存在返回 False
        """
        with self.current_models_lock:
            if model_type == "gpt":
                if filename in self.tts_files_database["gpt"]:
                    self.current_gpt_model = self.tts_files_database["gpt"][filename]
                    logger.debug("设置 GPT 模型: %s", filename)
                    return True
            elif model_type == "sovits":
                if filename in self.tts_files_database["sovits"]:
                    self.current_sovits_model = self.tts_files_database["sovits"][filename]
                    logger.debug("设置 SoVITS 模型: %s", filename)
                    return True
            elif model_type == "audio":
                if filename in self.tts_files_database["audio"]:
                    self.current_ref_audio = self.tts_files_database["audio"][filename]
                    logger.debug("设置参考音频: %s", filename)
                    return True
            elif model_type == "text":
                if filename in self.tts_files_database["text"]:
                    self.current_ref_text = self.tts_files_database["text"][filename]
                    logger.debug("设置参考文本: %s", filename)
                    return True
        return False

    def get_current_model(self, model_type: str) -> str | None:
        """
        获取当前选中的模型
        
        Args:
            model_type: 模型类型 (gpt/sovits/audio/text)
            
        Returns:
            当前模型的路径，未设置返回 None
        """
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
        """
        获取当前选中模型的文件名
        
        Args:
            model_type: 模型类型 (gpt/sovits/audio/text)
            
        Returns:
            模型文件名，未设置返回 "未选择"
        """
        model_path = self.get_current_model(model_type)
        if model_path:
            return Path(model_path).name
        return "未选择"

    def load_synthesized_files(self) -> list[tuple[str, str]]:
        """
        加载已合成音频文件
        
        扫描输出目录，加载所有 WAV 文件。
        
        Returns:
            音频文件列表，每个元素为 (文件路径, 文件名) 元组
        """
        with self.tts_synthesized_files_lock:
            self.tts_synthesized_files = []
            output_dir = Path(self.default_tts_config["output_path"])
            if output_dir.exists():
                wav_files = [f for f in output_dir.iterdir() if f.is_file() and f.suffix == '.wav']
                for wav_file in sorted(wav_files, key=lambda x: x.name, reverse=True):
                    self.tts_synthesized_files.append((str(wav_file), wav_file.name))
        logger.debug("加载已合成音频文件: %d 个", len(self.tts_synthesized_files))
        return self.tts_synthesized_files

    def add_synthesized_file(self, audio_path: str) -> None:
        """
        添加合成的音频文件到列表
        
        Args:
            audio_path: 音频文件路径
        """
        with self.tts_synthesized_files_lock:
            audio_file = Path(audio_path)
            self.tts_synthesized_files.append((str(audio_file), audio_file.name))
        logger.debug("添加合成音频文件: %s", audio_path)
