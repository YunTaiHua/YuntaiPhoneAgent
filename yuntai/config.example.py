#!/usr/bin/env python3
"""
配置管理模块
"""

# ==================== 核心配置 ====================
ZHIPU_API_KEY = "替换为你的智谱 API key"
ZHIPU_CLIENT = None  # 将在主文件中初始化

# 文件配置
CONVERSATION_HISTORY_FILE = "conversation_history.json"
RECORD_LOGS_DIR = "record_logs"
FOREVER_MEMORY_FILE = r"E:\PyCode\YuntaiPhoneAgent\forever.txt"
CONNECTION_CONFIG_FILE = "connection_config.json"

# 系统配置
MAX_HISTORY_LENGTH = 50
MAX_CYCLE_TIMES = 30
MAX_RETRY_TIMES = 3
WAIT_INTERVAL = 1

# 快捷键映射
SHORTCUTS = {
    'w': '打开微信',
    'q': '打开QQ',
    'd': '打开抖音',
    'k': '打开快手',
    't': '打开淘宝',
    'm': '打开QQ音乐'
}

