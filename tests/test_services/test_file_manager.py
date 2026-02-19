"""
文件管理模块测试
测试 yuntai.services.file_manager 模块
"""
import os
import json
from unittest.mock import patch, MagicMock, mock_open

import pytest


class TestFileManagerInit:
    """测试FileManager初始化"""
    
    def test_file_manager_init(self, mock_env_vars):
        """测试FileManager初始化"""
        from yuntai.services.file_manager import FileManager
        
        fm = FileManager()
        assert fm is not None


class TestInitFileSystem:
    """测试文件系统初始化"""
    
    def test_init_file_system_creates_temp_dir(self, temp_dir, mock_env_vars):
        """测试创建临时目录"""
        with patch('yuntai.services.file_manager.TEMP_DIR', temp_dir):
            with patch('yuntai.services.file_manager.RECORD_LOGS_DIR', os.path.join(temp_dir, 'record_logs')):
                with patch('yuntai.services.file_manager.CONVERSATION_HISTORY_FILE', os.path.join(temp_dir, 'history.json')):
                    with patch('yuntai.services.file_manager.CONNECTION_CONFIG_FILE', os.path.join(temp_dir, 'config.json')):
                        from yuntai.services.file_manager import FileManager
                        
                        fm = FileManager()
                        fm.init_file_system()
                        
                        assert os.path.exists(temp_dir)
    
    def test_init_file_system_idempotent(self, temp_dir, mock_env_vars):
        """测试重复初始化不会出错"""
        with patch('yuntai.services.file_manager.TEMP_DIR', temp_dir):
            with patch('yuntai.services.file_manager.RECORD_LOGS_DIR', os.path.join(temp_dir, 'record_logs')):
                with patch('yuntai.services.file_manager.CONVERSATION_HISTORY_FILE', os.path.join(temp_dir, 'history.json')):
                    with patch('yuntai.services.file_manager.CONNECTION_CONFIG_FILE', os.path.join(temp_dir, 'config.json')):
                        from yuntai.services.file_manager import FileManager
                        
                        fm = FileManager()
                        fm.init_file_system()
                        fm.init_file_system()


class TestReadForeverMemory:
    """测试读取永久记忆"""
    
    def test_read_forever_memory_file_not_exists(self, temp_dir, mock_env_vars):
        """测试文件不存在时返回空"""
        with patch('yuntai.services.file_manager.FOREVER_MEMORY_FILE', '/nonexistent/file.txt'):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            result = fm.read_forever_memory()
            
            assert result == ""
    
    def test_read_forever_memory_empty_file(self, temp_dir, mock_env_vars):
        """测试空文件返回空"""
        empty_file = os.path.join(temp_dir, 'empty.txt')
        with open(empty_file, 'w') as f:
            f.write("")
        
        with patch('yuntai.services.file_manager.FOREVER_MEMORY_FILE', empty_file):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            result = fm.read_forever_memory()
            
            assert result == ""
    
    def test_read_forever_memory_with_content(self, temp_forever_memory_file, mock_env_vars):
        """测试有内容时正确读取"""
        with patch('yuntai.services.file_manager.FOREVER_MEMORY_FILE', temp_forever_memory_file):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            result = fm.read_forever_memory()
            
            assert "测试记忆内容" in result


class TestSafeReadJsonFile:
    """测试安全读取JSON文件"""
    
    def test_read_nonexistent_file(self, mock_env_vars):
        """测试读取不存在的文件"""
        from yuntai.services.file_manager import FileManager
        
        fm = FileManager()
        result = fm.safe_read_json_file('/nonexistent/file.json', {'default': 'value'})
        
        assert result == {'default': 'value'}
    
    def test_read_valid_json(self, temp_json_file, mock_env_vars):
        """测试读取有效JSON"""
        import json
        test_data = {'key': 'value', 'number': 123}
        with open(temp_json_file, 'w') as f:
            json.dump(test_data, f)
        
        from yuntai.services.file_manager import FileManager
        
        fm = FileManager()
        result = fm.safe_read_json_file(temp_json_file, {})
        
        assert result == test_data
    
    def test_read_empty_file(self, temp_json_file, mock_env_vars):
        """测试读取空文件"""
        from yuntai.services.file_manager import FileManager
        
        fm = FileManager()
        result = fm.safe_read_json_file(temp_json_file, {'default': True})
        
        assert result == {'default': True}
    
    def test_read_malformed_json(self, temp_json_file, mock_env_vars):
        """测试读取格式错误的JSON"""
        with open(temp_json_file, 'w') as f:
            f.write("{not valid json}")
        
        from yuntai.services.file_manager import FileManager
        
        fm = FileManager()
        result = fm.safe_read_json_file(temp_json_file, {'fallback': True})
        
        assert result == {'fallback': True}


class TestSafeWriteJsonFile:
    """测试安全写入JSON文件"""
    
    def test_write_json_success(self, temp_json_file, mock_env_vars):
        """测试成功写入JSON"""
        from yuntai.services.file_manager import FileManager
        
        fm = FileManager()
        test_data = {'test': 'data', 'nested': {'key': 'value'}}
        result = fm.safe_write_json_file(temp_json_file, test_data)
        
        assert result is True
        assert os.path.exists(temp_json_file)
    
    def test_written_json_readable(self, temp_json_file, mock_env_vars):
        """测试写入的JSON可读"""
        from yuntai.services.file_manager import FileManager
        
        fm = FileManager()
        test_data = {'test': 'data'}
        fm.safe_write_json_file(temp_json_file, test_data)
        
        with open(temp_json_file, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == test_data


class TestSaveConversationHistory:
    """测试保存对话历史"""
    
    def test_save_free_chat(self, temp_history_file, mock_env_vars):
        """测试保存自由聊天"""
        with patch('yuntai.services.file_manager.CONVERSATION_HISTORY_FILE', temp_history_file):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            session_data = {
                'type': 'free_chat',
                'timestamp': '2026-01-15 10:00:00',
                'user_input': '你好',
                'assistant_reply': '你好！'
            }
            fm.save_conversation_history(session_data)
            
            with open(temp_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert len(data['free_chats']) == 1
            assert data['free_chats'][0]['user_input'] == '你好'
    
    def test_save_session(self, temp_history_file, mock_env_vars):
        """测试保存会话"""
        with patch('yuntai.services.file_manager.CONVERSATION_HISTORY_FILE', temp_history_file):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            session_data = {
                'type': 'chat_session',
                'timestamp': '2026-01-15 10:00:00',
                'target_app': '微信',
                'target_object': '张三'
            }
            fm.save_conversation_history(session_data)
            
            with open(temp_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert len(data['sessions']) == 1


class TestGetRecentConversationHistory:
    """测试获取最近对话历史"""
    
    def test_get_empty_history(self, temp_history_file, mock_env_vars):
        """测试获取空历史"""
        with patch('yuntai.services.file_manager.CONVERSATION_HISTORY_FILE', temp_history_file):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            result = fm.get_recent_conversation_history('微信', '张三')
            
            assert result == []
    
    def test_get_history_with_limit(self, temp_history_file, mock_env_vars):
        """测试带限制获取历史"""
        with patch('yuntai.services.file_manager.CONVERSATION_HISTORY_FILE', temp_history_file):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            
            for i in range(10):
                fm.save_conversation_history({
                    'type': 'chat_session',
                    'timestamp': f'2026-01-{15+i:02d} 10:00:00',
                    'target_app': '微信',
                    'target_object': '张三'
                })
            
            result = fm.get_recent_conversation_history('微信', '张三', limit=3)
            assert len(result) == 3


class TestGetRecentFreeChats:
    """测试获取最近自由聊天"""
    
    def test_get_empty_free_chats(self, temp_history_file, mock_env_vars):
        """测试获取空自由聊天"""
        with patch('yuntai.services.file_manager.CONVERSATION_HISTORY_FILE', temp_history_file):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            result = fm.get_recent_free_chats()
            
            assert result == []
    
    def test_get_free_chats_with_limit(self, temp_history_file, mock_env_vars):
        """测试带限制获取自由聊天"""
        with patch('yuntai.services.file_manager.CONVERSATION_HISTORY_FILE', temp_history_file):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            
            for i in range(10):
                fm.save_conversation_history({
                    'type': 'free_chat',
                    'timestamp': f'2026-01-{15+i:02d} 10:00:00',
                    'user_input': f'问题{i}',
                    'assistant_reply': f'回答{i}'
                })
            
            result = fm.get_recent_free_chats(limit=5)
            assert len(result) == 5


class TestCleanupRecordFiles:
    """测试清理记录文件"""
    
    def test_cleanup_empty_dir(self, temp_dir, mock_env_vars):
        """测试清理空目录"""
        record_dir = os.path.join(temp_dir, 'record_logs')
        os.makedirs(record_dir)
        
        with patch('yuntai.services.file_manager.RECORD_LOGS_DIR', record_dir):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            fm.cleanup_record_files()
    
    def test_cleanup_with_files(self, temp_dir, mock_env_vars):
        """测试清理有文件的目录"""
        record_dir = os.path.join(temp_dir, 'record_logs')
        os.makedirs(record_dir)
        
        for i in range(3):
            with open(os.path.join(record_dir, f'record_20260115_{i}.txt'), 'w') as f:
                f.write("test")
        
        with open(os.path.join(record_dir, 'other.txt'), 'w') as f:
            f.write("keep")
        
        with patch('yuntai.services.file_manager.RECORD_LOGS_DIR', record_dir):
            from yuntai.services.file_manager import FileManager
            
            fm = FileManager()
            fm.cleanup_record_files()
            
            remaining = os.listdir(record_dir)
            assert len(remaining) == 1
            assert 'other.txt' in remaining
