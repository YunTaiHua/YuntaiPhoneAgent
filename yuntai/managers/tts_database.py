"""
TTS数据库管理器 - 负责TTS文件扫描和数据库管理
"""

import os
import threading
from typing import Optional, Tuple, List


class TTSDatabaseManager:
    """TTS数据库管理器"""

    def __init__(self, default_tts_config: dict):
        """
        初始化TTS数据库管理器

        Args:
            default_tts_config: 默认TTS配置
        """
        self.default_tts_config = default_tts_config

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

        # 当前选中的模型
        self.current_gpt_model = None
        self.current_sovits_model = None
        self.current_ref_audio = None
        self.current_ref_text = None
        self.current_models_lock = threading.Lock()

        # 合成的文件列表
        self.tts_synthesized_files = []
        self.tts_synthesized_files_lock = threading.Lock()

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

    def get_cached_text(self, file_path: str) -> str:
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
                print(f"❌ 读取文本文件失败: {file_path}, {e}")
                raise

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

    def add_synthesized_file(self, audio_path: str):
        """添加合成的音频文件到列表"""
        with self.tts_synthesized_files_lock:
            self.tts_synthesized_files.append((audio_path, os.path.basename(audio_path)))
