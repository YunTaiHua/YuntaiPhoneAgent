"""
TTS数据库管理器 - 负责TTS文件扫描和数据库管理
使用 pathlib 进行跨平台路径处理
"""

import threading
from typing import Optional, Tuple, List
from pathlib import Path


class TTSDatabaseManager:
    """TTS数据库管理器"""

    def __init__(self, default_tts_config: dict):
        """
        初始化TTS数据库管理器

        Args:
            default_tts_config: 默认TTS配置
        """
        self.default_tts_config = default_tts_config

        self.tts_files_database = {
            "gpt": {},
            "sovits": {},
            "audio": {},
            "text": {}
        }

        self._text_cache = {}
        self._cache_lock = threading.Lock()

        self.current_gpt_model = None
        self.current_sovits_model = None
        self.current_ref_audio = None
        self.current_ref_text = None
        self.current_models_lock = threading.Lock()

        self.tts_synthesized_files = []
        self.tts_synthesized_files_lock = threading.Lock()

    def init_tts_files_database(self) -> bool:
        """初始化TTS文件数据库"""
        print("🔍 初始化TTS文件数据库...")

        for dir_key in ["gpt_model_dir", "sovits_model_dir", "ref_audio_root", "output_path"]:
            dir_path = Path(self.default_tts_config[dir_key])
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 确保目录存在: {dir_path}")

        self.tts_files_database["gpt"] = {}
        gpt_model_dir = Path(self.default_tts_config["gpt_model_dir"])
        if gpt_model_dir.exists():
            for ckpt_file in gpt_model_dir.rglob("*.ckpt"):
                abs_path = ckpt_file.resolve()
                self.tts_files_database["gpt"][ckpt_file.name] = str(abs_path)
        else:
            print(f"⚠️  GPT模型目录不存在: {gpt_model_dir}")

        self.tts_files_database["sovits"] = {}
        sovits_model_dir = Path(self.default_tts_config["sovits_model_dir"])
        if sovits_model_dir.exists():
            for pth_file in sovits_model_dir.rglob("*.pth"):
                abs_path = pth_file.resolve()
                self.tts_files_database["sovits"][pth_file.name] = str(abs_path)
        else:
            print(f"⚠️  SoVITS模型目录不存在: {sovits_model_dir}")

        self.tts_files_database["audio"] = {}
        ref_audio_root = Path(self.default_tts_config["ref_audio_root"])
        if ref_audio_root.exists():
            for audio_file in ref_audio_root.rglob("*"):
                if audio_file.suffix.lower() in ('.wav', '.mp3', '.flac'):
                    abs_path = audio_file.resolve()
                    self.tts_files_database["audio"][audio_file.name] = str(abs_path)
        else:
            print(f"⚠️  参考音频目录不存在: {ref_audio_root}")

        self.tts_files_database["text"] = {}
        ref_text_root = Path(self.default_tts_config["ref_text_root"])
        if ref_text_root.exists():
            for text_file in ref_text_root.rglob("*.txt"):
                abs_path = text_file.resolve()
                self.tts_files_database["text"][text_file.name] = str(abs_path)
        else:
            print(f"⚠️  参考文本目录不存在: {ref_text_root}")

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
                text_file = Path(file_path)
                content = text_file.read_text(encoding="utf-8").strip()
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
            return Path(model_path).name
        return "未选择"

    def load_synthesized_files(self) -> List[Tuple[str, str]]:
        """加载已合成音频文件"""
        with self.tts_synthesized_files_lock:
            self.tts_synthesized_files = []
            output_dir = Path(self.default_tts_config["output_path"])
            if output_dir.exists():
                wav_files = [f for f in output_dir.iterdir() if f.is_file() and f.suffix == '.wav']
                for wav_file in sorted(wav_files, key=lambda x: x.name, reverse=True):
                    self.tts_synthesized_files.append((str(wav_file), wav_file.name))
        return self.tts_synthesized_files

    def add_synthesized_file(self, audio_path: str):
        """添加合成的音频文件到列表"""
        with self.tts_synthesized_files_lock:
            audio_file = Path(audio_path)
            self.tts_synthesized_files.append((str(audio_file), audio_file.name))
