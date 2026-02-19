#!/usr/bin/env python3
"""
文件管理模块
"""
import os
import shutil
import json
import datetime
from typing import Any, List, Dict

from yuntai.core.config import (
    CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR,
    FOREVER_MEMORY_FILE, MAX_HISTORY_LENGTH, CONNECTION_CONFIG_FILE
)


class FileManager:
    def __init__(self):
        pass

    def init_file_system(self):
        """初始化文件系统，创建必要的目录"""
        try:
            # 创建record_logs目录
            if not os.path.exists(RECORD_LOGS_DIR):
                os.makedirs(RECORD_LOGS_DIR)
                print(f"📁 创建目录: {RECORD_LOGS_DIR}")

            # 确保conversation_history.json文件存在且格式正确
            if not os.path.exists(CONVERSATION_HISTORY_FILE):
                with open(CONVERSATION_HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump({"sessions": [], "free_chats": []}, f, ensure_ascii=False, indent=2)
                print(f"📁 创建文件: {CONVERSATION_HISTORY_FILE}")
            else:
                # 检查文件是否为空或格式错误
                try:
                    with open(CONVERSATION_HISTORY_FILE, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        if not content:
                            # 文件为空，重新创建
                            with open(CONVERSATION_HISTORY_FILE, 'w', encoding='utf-8') as f:
                                json.dump({"sessions": [], "free_chats": []}, f, ensure_ascii=False, indent=2)
                            print(f"📁 重建空文件: {CONVERSATION_HISTORY_FILE}")
                        else:
                            # 尝试解析JSON
                            json.loads(content)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # JSON格式错误，备份并重新创建
                    backup_file = f"{CONVERSATION_HISTORY_FILE}.backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.copy2(CONVERSATION_HISTORY_FILE, backup_file)
                    print(f"⚠️  JSON文件格式错误，已备份到: {backup_file}")
                    with open(CONVERSATION_HISTORY_FILE, 'w', encoding='utf-8') as f:
                        json.dump({"sessions": [], "free_chats": []}, f, ensure_ascii=False, indent=2)
                    print(f"📁 重建JSON文件: {CONVERSATION_HISTORY_FILE}")

            # 确保连接配置文件存在
            if not os.path.exists(CONNECTION_CONFIG_FILE):
                with open(CONNECTION_CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump({
                        "connection_type": "wireless",
                        "wireless_ip": "",
                        "wireless_port": "5555",
                        "usb_device_id": ""
                    }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  文件系统初始化失败: {e}")

    def cleanup_record_files(self):
        """清理record文件"""
        try:
            if os.path.exists(RECORD_LOGS_DIR):
                for filename in os.listdir(RECORD_LOGS_DIR):
                    if filename.startswith("record_") and filename.endswith(".txt"):
                        file_path = os.path.join(RECORD_LOGS_DIR, filename)
                        os.remove(file_path)
                print(f"🧹 已清理 {RECORD_LOGS_DIR} 中的record文件")
        except Exception as e:
            print(f"⚠️  清理文件失败: {e}")

    def read_forever_memory(self) -> str:
        """读取永久记忆文件内容"""
        try:
            if not os.path.exists(FOREVER_MEMORY_FILE):
                return ""

            with open(FOREVER_MEMORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return ""

                # 简单格式化记忆内容
                memories = []
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

    def save_record_to_log(self, cycle_count: int, record: str, target_app: str, target_object: str) -> str:
        """保存record到record_logs文件夹"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"record_{timestamp}_cycle{cycle_count}_{target_app}_{target_object}.txt"
            filepath = os.path.join(RECORD_LOGS_DIR, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== Record Info ===\n")
                f.write(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"目标: {target_app} -> {target_object}\n")
                f.write(f"循环: {cycle_count}\n")
                f.write(f"=== 聊天记录 ===\n\n")
                f.write(record)

            return filename
        except Exception as e:
            print(f"⚠️  保存record失败: {e}")
            return ""

    def safe_read_json_file(self, filepath: str, default_value: Any) -> Any:
        """安全读取JSON文件"""
        try:
            if not os.path.exists(filepath):
                return default_value

            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return default_value
                return json.loads(content)
        except (json.JSONDecodeError, UnicodeDecodeError, Exception) as e:
            print(f"⚠️  读取JSON文件失败 {filepath}: {e}")
            return default_value

    def safe_write_json_file(self, filepath: str, data: Any):
        """安全写入JSON文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

            # 写入临时文件
            temp_filepath = f"{filepath}.tmp"
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 替换原文件
            shutil.move(temp_filepath, filepath)
            return True
        except Exception as e:
            print(f"⚠️  写入JSON文件失败 {filepath}: {e}")
            return False

    def save_conversation_history(self, session_data: Dict[str, Any]):
        """保存对话历史到JSON文件"""
        try:
            # 读取现有历史
            history = self.safe_read_json_file(CONVERSATION_HISTORY_FILE, {"sessions": [], "free_chats": []})

            # 添加新会话
            if session_data.get("type") == "free_chat":
                history.setdefault("free_chats", []).append(session_data)
                # 限制自由聊天历史记录长度
                if len(history["free_chats"]) > MAX_HISTORY_LENGTH:
                    history["free_chats"] = history["free_chats"][-MAX_HISTORY_LENGTH:]
            else:
                history.setdefault("sessions", []).append(session_data)
                # 限制聊天历史记录长度
                if len(history["sessions"]) > MAX_HISTORY_LENGTH:
                    history["sessions"] = history["sessions"][-MAX_HISTORY_LENGTH:]

            # 保存文件
            success = self.safe_write_json_file(CONVERSATION_HISTORY_FILE, history)
            if not success:
                print(f"⚠️  保存对话历史失败，但程序继续运行")

        except Exception as e:
            print(f"⚠️  保存对话历史失败: {e}")

    def get_recent_conversation_history(self, target_app: str, target_object: str, limit: int = 5) -> List[Dict]:
        """获取最近的对话历史"""
        try:
            history = self.safe_read_json_file(CONVERSATION_HISTORY_FILE, {"sessions": [], "free_chats": []})

            # 筛选相关会话并按时间排序
            relevant_sessions = []
            for session in history.get("sessions", []):
                if (session.get("target_app") == target_app and
                        session.get("target_object") == target_object):
                    relevant_sessions.append(session)

            # 按时间戳排序（最新的在前）
            relevant_sessions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return relevant_sessions[:limit]

        except Exception as e:
            print(f"⚠️  读取对话历史失败: {e}")
            return []

    def get_recent_free_chats(self, limit: int = 5) -> List[Dict]:
        """获取最近的自由聊天记录"""
        try:
            history = self.safe_read_json_file(CONVERSATION_HISTORY_FILE, {"sessions": [], "free_chats": []})
            free_chats = history.get("free_chats", [])

            # 按时间戳排序（最新的在前）
            free_chats.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

            return free_chats[:limit]
        except Exception as e:
            print(f"⚠️  读取自由聊天历史失败: {e}")
            return []