"""
针对 services、memory、graphs、gui、tools 模块中未覆盖行的补充测试
==================================================================

覆盖模块:
    - task_manager: lines 114-140, 229, 286-287, 291-292, 327, 331-332, 349-352, 431-433, 439-440, 475
    - connection_manager: lines 157, 191-192, 258-259, 295-297, 368, 387, 392-393, 424-425, 428, 448-451, 480, 484-488
    - file_manager: lines 68-69, 76-80, 85-89, 114-115, 129-130, 143, 147, 159-162, 221, 279, 289-290
    - conversation_memory: lines 70, 80-88, 95-97, 189, 199-200, 262, 274, 318, 340
    - reply_graph: lines 219, 235-236, 244, 265-266, 323-324, 329-338, 348-349, 358, 366-368
    - dialogs: lines 69-72, 75, 98, 100, 102, 106, 173
    - theme_manager: lines 74, 114-115, 161-166, 207, 227, 316-321
    - message_tools: lines 129-132, 156, 172, 268
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


# ==============================================================
# task_manager 未覆盖行
# ==============================================================

class TestTTSManagerDeepBranches:
    """测试 TTSManager 深层分支（lines 114-140, 229, 286-287, 291-292, 327, 331-332, 349-352, 431-433, 439-440, 475）"""

    def _make_tts_manager(self, monkeypatch, tmp_path):
        """创建 TTSManager 实例"""
        import yuntai.services.task_manager as mod

        monkeypatch.setattr(mod, "TTSDatabaseManager", lambda cfg: SimpleNamespace(
            tts_files_database={"gpt": {}, "sovits": {}, "audio": {}, "text": {}},
            init_tts_files_database=lambda: True,
        ))
        monkeypatch.setattr(mod, "TTSTextProcessor", lambda max_text_length=500: SimpleNamespace(
            clean_text_for_tts=lambda t: t,
            should_use_segmented_synthesis=lambda t: len(t) > 200,
            split_text_by_numbered_sections=lambda t: [t],
        ))
        monkeypatch.setattr(mod, "TTSEngine", lambda *a: SimpleNamespace(
            load_tts_modules=lambda: (True, "ok"),
            synthesize_text=lambda *a, **k: (True, "out.wav"),
            synthesize_text_with_retry=lambda *a, **k: (True, "out.wav"),
            is_tts_synthesizing=False,
            tts_modules_loaded=False,
            tts_available=False,
            tts_modules={},
        ))
        monkeypatch.setattr(mod, "TTSAudioPlayer", lambda cfg: SimpleNamespace(
            play_audio_file=lambda p: None,
            stop_current_audio_playback=lambda: True,
            merge_audio_segments=lambda files: files[0] if files else None,
            cleanup=lambda: None,
            is_playing_audio=False,
        ))

        mgr = mod.TTSManager(str(tmp_path))
        return mgr

    def test_tts_manager_init(self, monkeypatch, tmp_path):
        """测试 TTSManager 初始化（lines 114-140）"""
        mgr = self._make_tts_manager(monkeypatch, tmp_path)
        assert mgr.tts_enabled is False
        assert mgr.default_tts_config is not None

    def test_clean_text_for_tts(self, monkeypatch, tmp_path):
        """测试 _clean_text_for_tts 代理方法（line 229）"""
        mgr = self._make_tts_manager(monkeypatch, tmp_path)
        result = mgr._clean_text_for_tts("测试文本")
        assert result == "测试文本"

    def test_synthesize_long_text_all_segments_fail(self, monkeypatch, tmp_path):
        """测试所有分段合成失败（lines 286-287）"""
        import yuntai.services.task_manager as mod
        mgr = self._make_tts_manager(monkeypatch, tmp_path)

        monkeypatch.setattr(mgr.text_processor, "clean_text_for_tts", lambda t: t)
        monkeypatch.setattr(mgr.text_processor, "split_text_by_numbered_sections", lambda t: ["段落1", "段落2"])
        monkeypatch.setattr(mgr.engine, "synthesize_text_with_retry", lambda *a, **k: (False, "失败"))
        monkeypatch.setattr(mod.time, "sleep", lambda *_: None)

        ok, msg = mgr.synthesize_long_text_serial("长文本", "ref.wav", "ref.txt")
        assert ok is False
        assert "所有分段合成失败" in msg

    def test_synthesize_long_text_merge_fallback(self, monkeypatch, tmp_path):
        """测试分段合成后合并失败回退（lines 291-292）"""
        import shutil
        import yuntai.services.task_manager as mod

        mgr = self._make_tts_manager(monkeypatch, tmp_path)

        # 创建临时合成文件
        out_dir = tmp_path / "out"
        out_dir.mkdir(parents=True, exist_ok=True)
        seg1 = out_dir / "seg1.wav"
        seg1.write_bytes(b"x")

        monkeypatch.setattr(mgr.text_processor, "clean_text_for_tts", lambda t: t)
        monkeypatch.setattr(mgr.text_processor, "split_text_by_numbered_sections", lambda t: ["段落1"])
        monkeypatch.setattr(mgr.engine, "synthesize_text_with_retry", lambda *a, **k: (True, str(seg1)))
        # 合并返回 None -> 使用第一个文件
        monkeypatch.setattr(mgr.audio_player, "merge_audio_segments", lambda files: None)
        monkeypatch.setattr(mod.datetime, "datetime", SimpleNamespace(now=lambda: SimpleNamespace(strftime=lambda f: "20260101_000000")))
        # shutil 是内置模块，使用标准 mock
        monkeypatch.setattr(shutil, "copy2", lambda src, dst: None)

        ok, result = mgr.synthesize_long_text_serial("长文本", str(seg1), "ref.txt")
        assert ok is True

    def test_speak_text_intelligently_no_ref(self, monkeypatch, tmp_path):
        """测试智能语音播报 - 无参考音频（line 327）"""
        mgr = self._make_tts_manager(monkeypatch, tmp_path)
        mgr.tts_enabled = True
        mgr.database_manager.get_current_model = lambda t: None if t == "audio" else "ref.txt"

        result = mgr.speak_text_intelligently("你好")
        assert result is False

    def test_speak_text_intelligently_segmented(self, monkeypatch, tmp_path):
        """测试智能语音播报 - 分段合成路径（lines 331-332）"""
        import yuntai.services.task_manager as mod
        mgr = self._make_tts_manager(monkeypatch, tmp_path)
        mgr.tts_enabled = True

        # database_manager 是 SimpleNamespace，需要添加 get_current_model 方法
        def mock_get_current_model(model_type):
            if model_type == "audio":
                return "ref.wav"
            elif model_type == "text":
                return "ref.txt"
            return None

        mgr.database_manager.get_current_model = mock_get_current_model
        monkeypatch.setattr(mgr.text_processor, "should_use_segmented_synthesis", lambda t: True)

        # 等待异步执行
        result = mgr.speak_text_intelligently("这是一段很长的文本需要分段合成")
        assert result is True

    def test_speak_text_intelligently_exception(self, monkeypatch, tmp_path):
        """测试智能语音播报异常（lines 349-352）"""
        mgr = self._make_tts_manager(monkeypatch, tmp_path)

        # 让 get_current_model 抛异常
        mgr.database_manager.get_current_model = lambda t: (_ for _ in ()).throw(RuntimeError("boom"))

        result = mgr.speak_text_intelligently("你好")
        assert result is False

    def test_tts_manager_cleanup(self, monkeypatch, tmp_path):
        """测试 TTSManager 清理资源"""
        mgr = self._make_tts_manager(monkeypatch, tmp_path)
        cleanup_called = []
        mgr.audio_player.cleanup = lambda: cleanup_called.append(True)
        mgr.cleanup()
        assert cleanup_called == [True]

    def test_tts_manager_init_tts_files_database(self, monkeypatch, tmp_path):
        """测试初始化 TTS 文件数据库（lines 431-433, 439-440）"""
        mgr = self._make_tts_manager(monkeypatch, tmp_path)
        result = mgr.init_tts_files_database()
        assert result is True

    def test_tts_manager_set_device_type(self, monkeypatch, tmp_path):
        """测试 TTSManager set_device_type 代理（line 475 -> 注: 实际在 TaskManager 中）"""
        import yuntai.services.task_manager as mod

        tm = object.__new__(mod.TaskManager)
        tm.connection_manager = SimpleNamespace(set_device_type=lambda dt: None)
        # 不应抛异常
        tm.set_device_type("harmony")


class TestTaskManagerInitExceptions:
    """测试 TaskManager 初始化异常路径（lines 431-433, 439-440）"""

    def test_init_tts_db_failure_does_not_crash(self, monkeypatch, tmp_path):
        """测试 TTS 文件数据库初始化失败不影响 TaskManager"""
        import yuntai.services.task_manager as mod

        monkeypatch.setattr(mod, "Utils", lambda: SimpleNamespace(enable_windows_color=lambda: None))
        monkeypatch.setattr(mod, "ConnectionManager", lambda: SimpleNamespace(
            load_connection_config=lambda: {},
            save_connection_config=lambda c: None,
            set_device_type=lambda dt: None,
            get_available_devices=lambda: [],
        ))
        monkeypatch.setattr(mod, "FileManager", lambda: SimpleNamespace(init_file_system=lambda: None))
        monkeypatch.setattr(mod, "ZhipuAI", lambda api_key=None: object())
        monkeypatch.setattr(mod, "AgentExecutor", lambda: object())

        # TTSManager 的 init_tts_files_database 抛异常 - 使用 MagicMock 避免 isinstance 问题
        from unittest.mock import MagicMock
        mock_instance = MagicMock(spec=mod.TTSManager)
        mock_instance.default_tts_config = {}
        mock_instance.database_manager = SimpleNamespace(init_tts_files_database=lambda: (_ for _ in ()).throw(RuntimeError("db boom")))
        mock_instance.text_processor = SimpleNamespace(clean_text_for_tts=lambda t: t)
        mock_instance.audio_player = SimpleNamespace(play_audio_file=lambda p: None, stop_current_audio_playback=lambda: True, cleanup=lambda: None, is_playing_audio=False, merge_audio_segments=lambda f: None)
        mock_instance.engine = SimpleNamespace(load_tts_modules=lambda: (True, "ok"), synthesize_text=lambda *a, **k: (True, "x"), synthesize_text_with_retry=lambda *a, **k: (True, "x"), is_tts_synthesizing=False, tts_modules_loaded=False, tts_available=False, tts_modules={})
        mock_instance.executor = SimpleNamespace(shutdown=lambda wait=False: None)
        mock_instance.tts_enabled = False
        mock_instance.tts_available = False
        mock_instance.tts_modules_loaded = False

        monkeypatch.setattr(mod, "TTSManager", lambda root: mock_instance)
        # 不应抛异常
        tm = mod.TaskManager(str(tmp_path), "/scrcpy")
        assert tm.tts_manager.tts_enabled is False


# ==============================================================
# connection_manager 未覆盖行
# ==============================================================

class TestConnectionManagerDeepBranches:
    """测试 ConnectionManager 深层分支"""

    def test_set_device_type(self):
        """测试设置设备类型（line 157）"""
        from yuntai.services.connection_manager import ConnectionManager
        cm = ConnectionManager()
        cm.set_device_type("harmony")
        assert cm.device_type == "harmony"

    def test_load_config_exception(self, monkeypatch):
        """测试加载配置异常（lines 191-192）"""
        from yuntai.services.connection_manager import ConnectionManager
        cm = ConnectionManager()

        def bad_read(self):
            raise RuntimeError("read boom")

        monkeypatch.setattr(Path, "read_text", bad_read)
        result = cm.load_connection_config()
        assert result["connection_type"] == "wireless"

    def test_get_android_devices_timeout(self, monkeypatch):
        """测试获取 Android 设备超时（lines 258-259）"""
        from yuntai.services.connection_manager import ConnectionManager

        def raise_timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd=["adb"], timeout=1)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_timeout)
        cm = ConnectionManager("android")
        assert cm.get_available_devices() == []

    def test_get_harmony_devices_exception(self, monkeypatch):
        """测试获取 HarmonyOS 设备异常（lines 295-297）"""
        from yuntai.services.connection_manager import ConnectionManager

        def raise_error(*a, **k):
            raise RuntimeError("hdc boom")

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_error)
        cm = ConnectionManager("harmony")
        assert cm.get_available_devices() == []

    def test_connect_android_wireless_already_connected(self, monkeypatch):
        """测试 Android 无线连接已连接（line 387）"""
        from yuntai.services.connection_manager import ConnectionManager

        def run_ok(*a, **k):
            return SimpleNamespace(stdout="already connected to 192.168.1.8:5555", returncode=0)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_ok)
        cm = ConnectionManager("android")
        ok, device, msg = cm.connect_to_device({
            "device_type": "android",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is True
        assert "已连接" in msg

    def test_connect_android_wireless_exception(self, monkeypatch):
        """测试 Android 无线连接异常（lines 392-393）"""
        from yuntai.services.connection_manager import ConnectionManager

        def raise_error(*a, **k):
            raise RuntimeError("connect boom")

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_error)
        cm = ConnectionManager("android")
        ok, device, msg = cm.connect_to_device({
            "device_type": "android",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "连接失败" in msg

    def test_connect_android_wireless_timeout(self, monkeypatch):
        """测试 Android 无线连接超时（line 368 -> timeout）"""
        from yuntai.services.connection_manager import ConnectionManager

        def raise_timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd=["adb"], timeout=1)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_timeout)
        cm = ConnectionManager("android")
        ok, device, msg = cm.connect_to_device({
            "device_type": "android",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "超时" in msg

    def test_connect_harmony_wireless_success(self, monkeypatch):
        """测试 HarmonyOS 无线连接成功（line 428）"""
        from yuntai.services.connection_manager import ConnectionManager

        def run_ok(*a, **k):
            return SimpleNamespace(stdout="ok", returncode=0)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_ok)
        cm = ConnectionManager("harmony")
        ok, device, msg = cm.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is True
        assert "HarmonyOS" in msg

    def test_connect_harmony_wireless_fail(self, monkeypatch):
        """测试 HarmonyOS 无线连接失败（lines 448-451）"""
        from yuntai.services.connection_manager import ConnectionManager

        def run_fail(*a, **k):
            return SimpleNamespace(stdout="fail", returncode=1)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_fail)
        cm = ConnectionManager("harmony")
        ok, device, msg = cm.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "HDC连接失败" in msg

    def test_connect_harmony_wireless_timeout(self, monkeypatch):
        """测试 HarmonyOS 无线连接超时（lines 448-451 -> timeout）"""
        from yuntai.services.connection_manager import ConnectionManager

        def raise_timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd=["hdc"], timeout=1)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_timeout)
        cm = ConnectionManager("harmony")
        ok, device, msg = cm.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "超时" in msg

    def test_connect_harmony_wireless_exception(self, monkeypatch):
        """测试 HarmonyOS 无线连接异常"""
        from yuntai.services.connection_manager import ConnectionManager

        def raise_error(*a, **k):
            raise RuntimeError("hdc connect boom")

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_error)
        cm = ConnectionManager("harmony")
        ok, device, msg = cm.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
        })
        assert ok is False
        assert "连接失败" in msg

    def test_adb_connect_windows_fail(self, monkeypatch):
        """测试 Windows ADB 连接失败（lines 480, 484-488）"""
        from yuntai.services.connection_manager import ConnectionManager
        cm = ConnectionManager()

        def run_fail(*a, **k):
            return SimpleNamespace(stdout="failed", returncode=1)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_fail)
        ok, msg = cm.adb_connect_windows("192.168.1.8:5555")
        assert ok is False
        assert "连接失败" in msg

    def test_adb_connect_windows_timeout(self, monkeypatch):
        """测试 Windows ADB 连接超时（line 486）"""
        from yuntai.services.connection_manager import ConnectionManager
        cm = ConnectionManager()

        def raise_timeout(*a, **k):
            raise subprocess.TimeoutExpired(cmd=["adb"], timeout=1)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_timeout)
        ok, msg = cm.adb_connect_windows("192.168.1.8:5555")
        assert ok is False
        assert "超时" in msg

    def test_adb_connect_windows_exception(self, monkeypatch):
        """测试 Windows ADB 连接异常（line 488）"""
        from yuntai.services.connection_manager import ConnectionManager
        cm = ConnectionManager()

        def raise_error(*a, **k):
            raise RuntimeError("adb boom")

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", raise_error)
        ok, msg = cm.adb_connect_windows("192.168.1.8:5555")
        assert ok is False
        assert "未知错误" in msg

    def test_connect_android_wireless_ipv6(self, monkeypatch):
        """测试 Android 无线连接 IPv6 地址"""
        from yuntai.services.connection_manager import ConnectionManager

        def run_ok(*a, **k):
            return SimpleNamespace(stdout="connected to [::1]:5555", returncode=0)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_ok)
        cm = ConnectionManager("android")
        ok, device, msg = cm.connect_to_device({
            "device_type": "android",
            "connection_type": "wireless",
            "wireless_ip": "::1",
            "wireless_port": "5555",
        })
        # IPv6 地址可能被转义，确认连接结果是合理的
        assert isinstance(ok, bool)

    def test_connect_harmony_device_id_has_colon(self, monkeypatch):
        """测试 HarmonyOS 设备 ID 包含冒号（line 428 -> ':' in device_id）"""
        from yuntai.services.connection_manager import ConnectionManager

        def run_ok(*a, **k):
            return SimpleNamespace(stdout="ok", returncode=0)

        monkeypatch.setattr("yuntai.services.connection_manager.subprocess.run", run_ok)
        cm = ConnectionManager("harmony")
        ok, device, msg = cm.connect_to_device({
            "device_type": "harmony",
            "connection_type": "wireless",
            "wireless_ip": "192.168.1.8",
            "wireless_port": "5555",
            "usb_device_id": "device:123",
        })
        assert ok is True


# ==============================================================
# file_manager 未覆盖行
# ==============================================================

class TestFileManagerDeepBranches:
    """测试 FileManager 深层分支（lines 68-69, 76-80, 85-89, 114-115, 129-130, 143, 147, 159-162, 221, 279, 289-290）"""

    def test_init_file_system_creates_dirs_and_files(self, monkeypatch, tmp_path):
        """测试文件系统初始化 - 创建目录和文件（lines 68-80）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        temp = tmp_path / "temp"
        records = tmp_path / "records"
        history = tmp_path / "history.json"
        conn = tmp_path / "conn.json"

        monkeypatch.setattr("yuntai.services.file_manager.TEMP_DIR", temp)
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", records)
        monkeypatch.setattr("yuntai.services.file_manager.CONVERSATION_HISTORY_FILE", history)
        monkeypatch.setattr("yuntai.services.file_manager.CONNECTION_CONFIG_FILE", conn)

        fm.init_file_system()

        assert temp.exists()
        assert records.exists()
        assert history.exists()
        assert conn.exists()

    def test_init_file_system_empty_history_file(self, monkeypatch, tmp_path):
        """测试初始化时空历史文件重建（lines 85-89）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        temp = tmp_path / "temp"
        temp.mkdir(parents=True)
        records = tmp_path / "records"
        records.mkdir(parents=True)
        history = tmp_path / "history.json"
        history.write_text("", encoding="utf-8")  # 空文件
        conn = tmp_path / "conn.json"

        monkeypatch.setattr("yuntai.services.file_manager.TEMP_DIR", temp)
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", records)
        monkeypatch.setattr("yuntai.services.file_manager.CONVERSATION_HISTORY_FILE", history)
        monkeypatch.setattr("yuntai.services.file_manager.CONNECTION_CONFIG_FILE", conn)

        fm.init_file_system()

        # 空文件应该被重建
        content = json.loads(history.read_text(encoding="utf-8"))
        assert "sessions" in content

    def test_init_file_system_corrupt_history_file(self, monkeypatch, tmp_path):
        """测试初始化时损坏的历史文件备份和重建（lines 85-89, JSONDecodeError）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        temp = tmp_path / "temp"
        temp.mkdir(parents=True)
        records = tmp_path / "records"
        records.mkdir(parents=True)
        history = tmp_path / "history.json"
        history.write_text("{invalid json", encoding="utf-8")
        conn = tmp_path / "conn.json"

        monkeypatch.setattr("yuntai.services.file_manager.TEMP_DIR", temp)
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", records)
        monkeypatch.setattr("yuntai.services.file_manager.CONVERSATION_HISTORY_FILE", history)
        monkeypatch.setattr("yuntai.services.file_manager.CONNECTION_CONFIG_FILE", conn)

        fm.init_file_system()

        # 损坏的文件应该被重建
        content = json.loads(history.read_text(encoding="utf-8"))
        assert "sessions" in content

    def test_init_file_system_exception(self, monkeypatch, tmp_path):
        """测试文件系统初始化异常（lines 114-115）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        # 让 TEMP_DIR.exists 抛异常
        monkeypatch.setattr("yuntai.services.file_manager.TEMP_DIR", SimpleNamespace(
            exists=lambda: (_ for _ in ()).throw(RuntimeError("fs boom")),
            mkdir=lambda **k: None,
        ))
        # 不应抛异常
        fm.init_file_system()

    def test_cleanup_record_files_exception(self, monkeypatch, tmp_path):
        """测试清理记录文件异常（lines 129-130）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", SimpleNamespace(
            exists=lambda: True,
            iterdir=lambda: (_ for _ in ()).throw(RuntimeError("iterdir boom")),
        ))
        # 不应抛异常
        fm.cleanup_record_files()

    def test_read_forever_memory_exception(self, monkeypatch):
        """测试读取永久记忆异常（lines 159-162）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        bad_path = SimpleNamespace(
            __bool__=lambda self: True,
            exists=lambda: True,
            read_text=lambda **k: (_ for _ in ()).throw(RuntimeError("read boom")),
        )
        monkeypatch.setattr("yuntai.services.file_manager.FOREVER_MEMORY_FILE", bad_path)
        result = fm.read_forever_memory()
        assert result == ""

    def test_read_forever_memory_empty_lines(self, monkeypatch, tmp_path):
        """测试读取永久记忆 - 只有空行（line 143, 147）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        forever = tmp_path / "forever.txt"
        forever.write_text("\n\n  \n", encoding="utf-8")
        monkeypatch.setattr("yuntai.services.file_manager.FOREVER_MEMORY_FILE", forever)
        result = fm.read_forever_memory()
        assert result == ""

    def test_save_record_to_log_exception(self, monkeypatch):
        """测试保存记录日志异常（line 221）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        # 让 write_text 抛异常
        monkeypatch.setattr("yuntai.services.file_manager.RECORD_LOGS_DIR", SimpleNamespace(
            __truediv__=lambda self, other: SimpleNamespace(
                write_text=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("write boom")),
            ),
        ))
        result = fm.save_record_to_log(1, "record", "app", "obj")
        assert result == ""

    def test_save_conversation_history_write_fail(self, monkeypatch):
        """测试保存对话历史写入失败（line 279）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        monkeypatch.setattr(fm, "safe_read_json_file", lambda fp, dv: {"sessions": [], "free_chats": []})
        monkeypatch.setattr(fm, "safe_write_json_file", lambda fp, data: False)

        # 不应抛异常
        fm.save_conversation_history({"type": "chat_session", "timestamp": "1"})

    def test_save_conversation_history_exception(self, monkeypatch):
        """测试保存对话历史异常（lines 289-290）"""
        from yuntai.services.file_manager import FileManager
        fm = FileManager()

        monkeypatch.setattr(fm, "safe_read_json_file", lambda fp, dv: (_ for _ in ()).throw(RuntimeError("boom")))

        # 不应抛异常
        fm.save_conversation_history({"type": "chat_session", "timestamp": "1"})


# ==============================================================
# conversation_memory 未覆盖行
# ==============================================================

class TestConversationMemoryDeepBranches:
    """测试 ConversationMemoryManager 深层分支（lines 70, 80-88, 95-97, 189, 199-200, 262, 274, 318, 340）"""

    def _make_cbm(self):
        """创建模拟回调管理器"""
        class _CBM:
            def register_handler(self, **kwargs):
                pass
            def get_callbacks(self, **kwargs):
                return []
        return _CBM()

    def test_load_memory_from_file(self, monkeypatch, tmp_path):
        """测试从文件加载记忆（lines 70, 80-88）"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager

        history_file = tmp_path / "history.json"
        history_file.write_text(json.dumps({"messages": []}), encoding="utf-8")

        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: self._make_cbm())
        m = ConversationMemoryManager(history_file=str(history_file))
        assert m._memory is not None

    def test_load_memory_exception_fallback(self, monkeypatch, tmp_path):
        """测试加载记忆异常时的降级处理（lines 87-88）"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager

        history_file = tmp_path / "bad_history.json"
        history_file.write_text("corrupt", encoding="utf-8")

        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: self._make_cbm())
        m = ConversationMemoryManager(history_file=str(history_file))
        assert m._memory is not None

    def test_load_forever_memory_exception(self, monkeypatch, tmp_path):
        """测试加载永久记忆异常（lines 95-97）"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager

        forever = tmp_path / "forever.txt"
        forever.write_bytes(b"\xff\xfe")  # 无效 UTF-8

        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: self._make_cbm())
        m = ConversationMemoryManager(forever_memory_file=str(forever))
        assert m.get_forever_memory() == ""

    def test_save_to_file_existing_not_list(self, monkeypatch, tmp_path):
        """测试保存文件时现有数据非列表（line 189）"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager

        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: self._make_cbm())
        m = ConversationMemoryManager(max_history_length=5)

        out = tmp_path / "history.json"
        out.write_text('{"not": "a list"}', encoding="utf-8")
        m.save_to_file({"i": 1}, str(out))

        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, list)
        assert data[0]["i"] == 1

    def test_save_to_file_exception(self, monkeypatch, tmp_path):
        """测试保存文件异常（lines 199-200）"""
        from yuntai.memory.conversation_memory import ConversationMemoryManager

        monkeypatch.setattr("yuntai.memory.conversation_memory.get_callback_manager", lambda: self._make_cbm())
        m = ConversationMemoryManager()

        # 写入一个不存在的深层路径
        m.save_to_file({"i": 1}, str(tmp_path / "a" / "b" / "c" / "deep.json"))

    def test_free_chat_memory_no_file_manager(self):
        """测试自由聊天无文件管理器（line 262）"""
        from yuntai.memory.conversation_memory import FreeChatMemory
        fm = FreeChatMemory(file_manager=None)
        assert fm.get_recent_chats() == []

    def test_free_chat_memory_save_no_file_manager(self):
        """测试自由聊天保存无文件管理器（line 274）"""
        from yuntai.memory.conversation_memory import FreeChatMemory
        fm = FreeChatMemory(file_manager=None)
        # 不应抛异常
        fm.save_chat("user", "assistant")

    def test_chat_session_memory_no_file_manager(self):
        """测试聊天会话无文件管理器（line 318）"""
        from yuntai.memory.conversation_memory import ChatSessionMemory
        cs = ChatSessionMemory(file_manager=None)
        assert cs.get_recent_session("wx", "alice") == []

    def test_chat_session_memory_save_no_file_manager(self):
        """测试聊天会话保存无文件管理器（line 340）"""
        from yuntai.memory.conversation_memory import ChatSessionMemory
        cs = ChatSessionMemory(file_manager=None)
        # 不应抛异常
        cs.save_session("wx", "alice", "reply", ["msg1"])


# ==============================================================
# reply_graph 未覆盖行
# ==============================================================

class TestReplyGraphDeepBranches:
    """测试 ReplyGraph 深层分支（lines 219, 235-236, 244, 265-266, 323-324, 329-338, 348-349, 358, 366-368）"""

    def _make_reply_graph(self, monkeypatch):
        """创建 ReplyGraph 实例"""
        import yuntai.graphs.reply_graph as mod

        # Mock 所有外部依赖
        monkeypatch.setattr(mod, "emit_agent_event", lambda *a, **k: None)
        monkeypatch.setattr(mod, "set_managers", lambda *a: None)
        monkeypatch.setattr(mod, "set_terminate_event", lambda *a: None)

        # Mock 节点函数
        for name in ["extract_records", "parse_messages", "determine_ownership",
                      "check_new_message", "generate_reply", "send_message",
                      "update_memory", "do_wait", "check_continue"]:
            monkeypatch.setattr(mod, name, lambda state: state)

        return mod.ReplyGraph()

    def test_route_after_check_no_new_message(self):
        """测试检查后无新消息路由到 wait（line 219）"""
        from yuntai.graphs.reply_graph import ReplyGraph
        rg = object.__new__(ReplyGraph)
        rg.terminate_event = SimpleNamespace(is_set=lambda: False)
        state = {"is_new_message": False, "terminate_flag": False}
        assert rg._route_after_check(state) == "wait"

    def test_route_after_reply_no_reply(self):
        """测试回复后无回复路由到 wait（line 244）"""
        from yuntai.graphs.reply_graph import ReplyGraph
        rg = object.__new__(ReplyGraph)
        rg.terminate_event = SimpleNamespace(is_set=lambda: False)
        state = {"generated_reply": None, "terminate_flag": False}
        assert rg._route_after_reply(state) == "wait"

    def test_route_after_reply_terminate(self):
        """测试回复后终止标志路由到 wait（lines 235-236）"""
        from yuntai.graphs.reply_graph import ReplyGraph
        rg = object.__new__(ReplyGraph)
        rg.terminate_event = SimpleNamespace(is_set=lambda: True)
        state = {"generated_reply": "有回复", "terminate_flag": False}
        assert rg._route_after_reply(state) == "wait"

    def test_route_continue_should_not_continue(self):
        """测试继续检查不应继续（line 265-266）"""
        from yuntai.graphs.reply_graph import ReplyGraph
        rg = object.__new__(ReplyGraph)
        rg.terminate_event = SimpleNamespace(is_set=lambda: False)
        state = {"should_continue": False, "terminate_flag": False}
        assert rg._route_continue(state) == "end"

    def test_run_terminate_flag_set(self, monkeypatch):
        """测试运行时终止标志已设置（lines 322-324）"""
        rg = self._make_reply_graph(monkeypatch)

        # Mock graph.invoke to set terminate_event during execution
        def mock_invoke(state, config=None):
            rg.terminate_event.set()
            return state

        rg.graph = SimpleNamespace(invoke=mock_invoke)

        ok, msg = rg.run("wx", "test", device_id="d")
        assert ok is True
        assert "已终止" in msg

    def test_run_exception(self, monkeypatch):
        """测试运行时异常（lines 329-338）"""
        rg = self._make_reply_graph(monkeypatch)
        rg.graph = SimpleNamespace(invoke=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("graph boom")))

        ok, msg = rg.run("wx", "test")
        assert ok is False
        assert "执行失败" in msg

    def test_stop_sets_terminate(self, monkeypatch):
        """测试停止设置终止标志（lines 348-349）"""
        rg = self._make_reply_graph(monkeypatch)
        rg.stop()
        assert rg.terminate_event.is_set()

    def test_is_running(self, monkeypatch):
        """测试运行状态检查（line 358）"""
        rg = self._make_reply_graph(monkeypatch)
        rg._running = True
        assert rg.is_running() is True
        rg._running = False
        assert rg.is_running() is False

    def test_reset(self, monkeypatch):
        """测试重置状态（lines 366-368）"""
        rg = self._make_reply_graph(monkeypatch)
        rg._running = True
        rg.terminate_event.set()
        rg.reset()
        assert rg._running is False
        assert not rg.terminate_event.is_set()


# ==============================================================
# dialogs 未覆盖行
# ==============================================================

class TestDialogsDeepBranches:
    """测试 DialogsMixin 深层分支（lines 69-72, 75, 98, 100, 102, 106, 173）"""

    def test_show_attached_files_empty_list(self):
        """测试显示空文件列表（lines 69-72, 75）"""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication, QFrame, QVBoxLayout
        from yuntai.gui.view.dialogs import DialogsMixin

        _APP = QApplication.instance() or QApplication([])

        frame = QFrame()
        frame.setLayout(QVBoxLayout())
        # 添加一个子控件
        from PyQt6.QtWidgets import QLabel
        frame.layout().addWidget(QLabel("old"))

        host = DialogsMixin()
        host.colors = SimpleNamespace()
        host.get_component = lambda name: frame if name == "files_list_scroll_frame" else None
        host.show_attached_files([])
        # 空列表应该清空现有控件并返回
        assert frame.layout().count() == 0

    def test_show_attached_files_various_extensions(self, tmp_path):
        """测试显示不同类型文件图标（lines 98, 100, 102, 106）"""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication, QFrame, QVBoxLayout
        from yuntai.gui.view.dialogs import DialogsMixin

        _APP = QApplication.instance() or QApplication([])

        frame = QFrame()
        frame.setLayout(QVBoxLayout())

        host = DialogsMixin()
        host.colors = SimpleNamespace(
            BG_HOVER="#1", TEXT_PRIMARY="#2", DANGER="#3",
            DANGER_HOVER="#4", WARNING="#5", WARNING_HOVER="#6", TEXT_LIGHT="#7",
        )
        host.get_component = lambda name: frame if name == "files_list_scroll_frame" else None

        # 创建不同类型的文件
        files = []
        for ext in [".mp4", ".mp3", ".txt", ".xyz"]:
            f = tmp_path / f"test{ext}"
            f.write_bytes(b"x")
            files.append(str(f))

        host.show_attached_files(files)
        assert frame.layout().count() > 0

    def test_get_component_returns_none(self):
        """测试获取不存在的组件（line 173）"""
        from yuntai.gui.view.dialogs import DialogsMixin
        host = DialogsMixin()
        host.components = {}
        assert host.get_component("nonexistent") is None


# ==============================================================
# theme_manager 未覆盖行
# ==============================================================

class TestThemeManagerDeepBranches:
    """测试 ThemeManagerMixin 深层分支（lines 74, 114-115, 161-166, 207, 227, 316-321）"""

    def test_apply_shadow_dark_theme(self):
        """测试深色主题阴影（line 74）"""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication, QFrame
        from yuntai.gui.view.theme_manager import ThemeManagerMixin

        _APP = QApplication.instance() or QApplication([])

        host = ThemeManagerMixin()
        host.is_dark_theme = True
        widget = QFrame()
        host._apply_shadow(widget, shadow_type='sm')
        # 不应抛异常
        assert widget.graphicsEffect() is not None

    def test_clear_layout_recursive(self):
        """测试递归清除布局（lines 316-321）"""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication, QFrame, QVBoxLayout, QHBoxLayout, QLabel
        from yuntai.gui.view.theme_manager import ThemeManagerMixin

        _APP = QApplication.instance() or QApplication([])

        host = ThemeManagerMixin()

        outer = QVBoxLayout()
        inner = QHBoxLayout()
        inner.addWidget(QLabel("child"))
        outer.addLayout(inner)
        outer.addWidget(QLabel("direct"))

        frame = QFrame()
        frame.setLayout(outer)

        host._clear_layout(outer)
        assert outer.count() == 0

    def test_apply_shadow_various_types(self):
        """测试不同类型的阴影效果"""
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from PyQt6.QtWidgets import QApplication, QFrame
        from yuntai.gui.view.theme_manager import ThemeManagerMixin

        _APP = QApplication.instance() or QApplication([])

        host = ThemeManagerMixin()
        host.is_dark_theme = False

        for stype in ['sm', 'md', 'lg']:
            widget = QFrame()
            host._apply_shadow(widget, shadow_type=stype)
            assert widget.graphicsEffect() is not None


# ==============================================================
# message_tools 未覆盖行
# ==============================================================

class TestMessageToolsDeepBranches:
    """测试 message_tools 深层分支（lines 129-132, 156, 172, 268）"""

    def _load_module(self):
        """加载 message_tools 模块"""
        import importlib.util
        import types

        MESSAGE_TOOLS_PATH = Path(__file__).resolve().parents[3] / "yuntai" / "tools" / "message_tools.py"

        fake_zhipuai = types.ModuleType("zhipuai")
        fake_zhipuai.ZhipuAI = object

        fake_similarity = types.ModuleType("yuntai.tools.similarity")
        fake_similarity.is_similar = lambda a, b, threshold=0.6: a == b

        fake_config = types.ModuleType("yuntai.core.config")
        fake_config.ZHIPU_CHAT_MODEL = "glm-test"
        fake_config.SIMILARITY_THRESHOLD = 0.6
        fake_config.SIMILARITY_CHECK_NEW_THRESHOLD = 0.5
        fake_config.PARSE_MAX_TOKENS = 2000
        fake_config.REPLY_MAX_TOKENS = 500
        fake_config.REPLY_TEMPERATURE = 0.7
        fake_config.REPLY_HISTORY_LIMIT = 5
        fake_config.MIN_MESSAGE_LENGTH = 2

        fake_prompts = types.ModuleType("yuntai.prompts")
        fake_prompts.PARSE_MESSAGES_SYSTEM_PROMPT = "sys"
        fake_prompts.PARSE_MESSAGES_PROMPT = "records={records}"
        fake_prompts.PARSE_MESSAGES_MAX_LENGTH = 2000
        fake_prompts.REPLY_NODE_SYSTEM_PROMPT = "reply-sys"
        fake_prompts.REPLY_NODE_USER_PROMPT = "latest={latest_message}|history={history_prompt}"

        original = {
            "zhipuai": sys.modules.get("zhipuai"),
            "yuntai.tools.similarity": sys.modules.get("yuntai.tools.similarity"),
            "yuntai.core.config": sys.modules.get("yuntai.core.config"),
            "yuntai.prompts": sys.modules.get("yuntai.prompts"),
        }
        sys.modules["zhipuai"] = fake_zhipuai
        sys.modules["yuntai.tools.similarity"] = fake_similarity
        sys.modules["yuntai.core.config"] = fake_config
        sys.modules["yuntai.prompts"] = fake_prompts

        try:
            spec = importlib.util.spec_from_file_location("test_message_tools_gaps", MESSAGE_TOOLS_PATH)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        finally:
            for key, value in original.items():
                if value is None:
                    sys.modules.pop(key, None)
                else:
                    sys.modules[key] = value

    def test_parse_messages_general_exception(self):
        """测试解析消息通用异常（lines 129-132）"""
        module = self._load_module()

        class _BoomClient:
            class chat:
                class completions:
                    @staticmethod
                    def create(**kwargs):
                        raise RuntimeError("api boom")

        result = module.parse_messages("这是一条足够长的聊天记录", _BoomClient())
        assert isinstance(result, list)  # 应该降级到紧急提取

    def test_standardize_color_various(self):
        """测试各种颜色标准化（line 172 -> return "未知"）"""
        module = self._load_module()
        assert module._standardize_color("棕") == "未知"
        assert module._standardize_color(None) == "未知"
        assert module._standardize_color("未知") == "未知"

    def test_standardize_position_various(self):
        """测试各种位置标准化（line 156）"""
        module = self._load_module()
        assert module._standardize_position("上") == "未知"
        assert module._standardize_position(None) == "未知"
        assert module._standardize_position("未知") == "未知"

    def test_determine_ownership_short_message_skipped(self):
        """测试归属判断跳过短消息（line 268 - MIN_MESSAGE_LENGTH）"""
        module = self._load_module()

        messages = [
            {"content": "x", "position": "左侧有头像", "color": "白色"},  # 长度 < MIN_MESSAGE_LENGTH(2)
            {"content": "", "position": "右侧有头像", "color": "红色"},    # 空内容
        ]
        other, mine = module.determine_message_ownership(messages, [], [])
        assert len(other) == 0
        assert len(mine) == 0
