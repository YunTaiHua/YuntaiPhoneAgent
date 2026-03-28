"""
文件管理模块
============

使用 pathlib 进行跨平台路径处理，管理对话历史、永久记忆、聊天记录等文件。

主要功能:
    - init_file_system: 初始化文件系统
    - read_forever_memory: 读取永久记忆
    - save_conversation_history: 保存对话历史
    - get_recent_conversation_history: 获取最近对话历史
    - get_recent_free_chats: 获取最近自由聊天记录
    - save_record_to_log: 保存聊天记录到日志

使用示例:
    >>> file_manager = FileManager()
    >>> file_manager.init_file_system()
    >>> memory = file_manager.read_forever_memory()
"""
import datetime
import json
import logging
import shutil
from pathlib import Path
from typing import Any

from yuntai.core.config import (
    CONVERSATION_HISTORY_FILE,
    RECORD_LOGS_DIR,
    FOREVER_MEMORY_FILE,
    MAX_HISTORY_LENGTH,
    CONNECTION_CONFIG_FILE,
    TEMP_DIR,
)

logger = logging.getLogger(__name__)


class FileManager:
    """
    文件管理器
    
    负责管理对话历史、永久记忆、聊天记录等文件的读写操作。
    
    Example:
        >>> file_manager = FileManager()
        >>> file_manager.init_file_system()
        >>> memory = file_manager.read_forever_memory()
        >>> file_manager.save_conversation_history({"type": "free_chat", ...})
    """
    
    def __init__(self) -> None:
        """初始化文件管理器"""
        pass

    def init_file_system(self) -> None:
        """
        初始化文件系统
        
        创建必要的目录和文件，包括:
        - 临时目录 (TEMP_DIR)
        - 记录日志目录 (RECORD_LOGS_DIR)
        - 对话历史文件 (CONVERSATION_HISTORY_FILE)
        - 连接配置文件 (CONNECTION_CONFIG_FILE)
        """
        try:
            if not TEMP_DIR.exists():
                TEMP_DIR.mkdir(parents=True)
                print(f"📁 创建目录: {TEMP_DIR}")

            if not RECORD_LOGS_DIR.exists():
                RECORD_LOGS_DIR.mkdir(parents=True)
                print(f"📁 创建目录: {RECORD_LOGS_DIR}")

            if not CONVERSATION_HISTORY_FILE.exists():
                CONVERSATION_HISTORY_FILE.write_text(
                    json.dumps({"sessions": [], "free_chats": []}, ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )
                print(f"📁 创建文件: {CONVERSATION_HISTORY_FILE}")
            else:
                try:
                    content = CONVERSATION_HISTORY_FILE.read_text(encoding='utf-8').strip()
                    if not content:
                        CONVERSATION_HISTORY_FILE.write_text(
                            json.dumps({"sessions": [], "free_chats": []}, ensure_ascii=False, indent=2),
                            encoding='utf-8'
                        )
                        print(f"📁 重建空文件: {CONVERSATION_HISTORY_FILE}")
                    else:
                        json.loads(content)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    backup_file = CONVERSATION_HISTORY_FILE.with_suffix(
                        f'.backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                    )
                    shutil.copy2(str(CONVERSATION_HISTORY_FILE), str(backup_file))
                    print(f"⚠️  JSON文件格式错误，已备份到: {backup_file}")
                    CONVERSATION_HISTORY_FILE.write_text(
                        json.dumps({"sessions": [], "free_chats": []}, ensure_ascii=False, indent=2),
                        encoding='utf-8'
                    )
                    print(f"📁 重建JSON文件: {CONVERSATION_HISTORY_FILE}")

            if not CONNECTION_CONFIG_FILE.exists():
                CONNECTION_CONFIG_FILE.write_text(
                    json.dumps({
                        "connection_type": "wireless",
                        "wireless_ip": "",
                        "wireless_port": "5555",
                        "usb_device_id": ""
                    }, ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )
        except Exception as e:
            print(f"⚠️  文件系统初始化失败: {e}")

    def cleanup_record_files(self) -> None:
        """
        清理记录文件
        
        删除 RECORD_LOGS_DIR 中所有以 "record_" 开头的 .txt 文件。
        """
        try:
            if RECORD_LOGS_DIR.exists():
                for filepath in RECORD_LOGS_DIR.iterdir():
                    if filepath.name.startswith("record_") and filepath.suffix == ".txt":
                        filepath.unlink()
                print(f"🧹 已清理 {RECORD_LOGS_DIR} 中的record文件")
        except Exception as e:
            print(f"⚠️  清理文件失败: {e}")

    def read_forever_memory(self) -> str:
        """
        读取永久记忆文件内容
        
        从 FOREVER_MEMORY_FILE 读取永久记忆内容，并格式化为带编号的列表。
        
        Returns:
            格式化的永久记忆字符串，如果文件不存在或为空则返回空字符串
        """
        try:
            if not FOREVER_MEMORY_FILE or not FOREVER_MEMORY_FILE.exists():
                return ""

            content = FOREVER_MEMORY_FILE.read_text(encoding='utf-8').strip()
            if not content:
                return ""

            memories: list[str] = []
            lines = content.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                if line:
                    memories.append(f"{i + 1}. {line}")

            if memories:
                return "\n永久记忆:\n" + "\n".join(memories)
            else:
                return ""
        except Exception as e:
            print(f"⚠️  读取永久记忆失败: {e}")
            return ""

    def save_record_to_log(
        self,
        cycle_count: int,
        record: str,
        target_app: str,
        target_object: str
    ) -> str:
        """
        保存聊天记录到日志文件
        
        Args:
            cycle_count: 循环次数
            record: 聊天记录内容
            target_app: 目标 APP 名称
            target_object: 聊天对象名称
        
        Returns:
            保存的文件名，失败时返回空字符串
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"record_{timestamp}_cycle{cycle_count}_{target_app}_{target_object}.txt"
            filepath = RECORD_LOGS_DIR / filename

            filepath.write_text(
                f"=== Record Info ===\n"
                f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"目标: {target_app} -> {target_object}\n"
                f"循环: {cycle_count}\n"
                f"=== 聊天记录 ===\n\n"
                f"{record}",
                encoding='utf-8'
            )

            return filename
        except Exception as e:
            print(f"⚠️  保存record失败: {e}")
            return ""

    def safe_read_json_file(self, filepath: str, default_value: Any) -> Any:
        """
        安全读取 JSON 文件
        
        Args:
            filepath: 文件路径
            default_value: 默认值，当文件不存在或读取失败时返回
        
        Returns:
            JSON 解析后的数据，或默认值
        """
        try:
            path = Path(filepath)
            if not path.exists():
                return default_value

            content = path.read_text(encoding='utf-8').strip()
            if not content:
                return default_value
            return json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
            print(f"⚠️  读取JSON文件失败 {filepath}: {e}")
            return default_value

    def safe_write_json_file(self, filepath: str, data: Any) -> bool:
        """
        安全写入 JSON 文件
        
        使用临时文件写入，然后移动到目标位置，避免写入过程中断导致数据丢失。
        
        Args:
            filepath: 文件路径
            data: 要写入的数据
        
        Returns:
            是否写入成功
        """
        try:
            path = Path(filepath)
            parent = path.parent
            if parent and not parent.exists():
                parent.mkdir(parents=True, exist_ok=True)

            temp_filepath = path.with_suffix(path.suffix + '.tmp')
            temp_filepath.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )

            shutil.move(str(temp_filepath), str(path))
            return True
        except Exception as e:
            print(f"⚠️  写入JSON文件失败 {filepath}: {e}")
            return False

    def save_conversation_history(self, session_data: dict[str, Any]) -> None:
        """
        保存对话历史到 JSON 文件
        
        Args:
            session_data: 会话数据字典，包含以下字段:
                - type: 会话类型 ("free_chat" 或其他)
                - timestamp: 时间戳
                - target_app: 目标 APP (非自由聊天)
                - target_object: 聊天对象 (非自由聊天)
                - 其他自定义字段
        """
        try:
            history = self.safe_read_json_file(
                str(CONVERSATION_HISTORY_FILE),
                {"sessions": [], "free_chats": []}
            )

            if session_data.get("type") == "free_chat":
                history.setdefault("free_chats", []).append(session_data)
                if len(history["free_chats"]) > MAX_HISTORY_LENGTH:
                    history["free_chats"] = history["free_chats"][-MAX_HISTORY_LENGTH:]
            else:
                history.setdefault("sessions", []).append(session_data)
                if len(history["sessions"]) > MAX_HISTORY_LENGTH:
                    history["sessions"] = history["sessions"][-MAX_HISTORY_LENGTH:]

            success = self.safe_write_json_file(str(CONVERSATION_HISTORY_FILE), history)
            if not success:
                print(f"⚠️  保存对话历史失败，但程序继续运行")

        except Exception as e:
            print(f"⚠️  保存对话历史失败: {e}")

    def get_recent_conversation_history(
        self,
        target_app: str,
        target_object: str,
        limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        获取最近的对话历史
        
        Args:
            target_app: 目标 APP 名称
            target_object: 聊天对象名称
            limit: 返回的最大记录数
        
        Returns:
            最近的对话历史列表，按时间倒序排列
        """
        try:
            history = self.safe_read_json_file(
                str(CONVERSATION_HISTORY_FILE),
                {"sessions": [], "free_chats": []}
            )

            relevant_sessions: list[dict[str, Any]] = []
            for session in history.get("sessions", []):
                if (session.get("target_app") == target_app and
                        session.get("target_object") == target_object):
                    relevant_sessions.append(session)

            relevant_sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return relevant_sessions[:limit]

        except Exception as e:
            print(f"⚠️  读取对话历史失败: {e}")
            return []

    def get_recent_free_chats(self, limit: int = 5) -> list[dict[str, Any]]:
        """
        获取最近的自由聊天记录
        
        Args:
            limit: 返回的最大记录数
        
        Returns:
            最近的自由聊天记录列表，按时间倒序排列
        """
        try:
            history = self.safe_read_json_file(
                str(CONVERSATION_HISTORY_FILE),
                {"sessions": [], "free_chats": []}
            )
            free_chats = history.get("free_chats", [])

            free_chats.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return free_chats[:limit]
        except Exception as e:
            print(f"⚠️  读取自由聊天历史失败: {e}")
            return []
