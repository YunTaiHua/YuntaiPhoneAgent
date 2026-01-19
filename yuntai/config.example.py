#!/usr/bin/env python3
"""
配置管理模块
支持通过.env文件进行环境变量配置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== 核心配置 ====================
# AI模型相关配置

# 智谱AI API 密钥 - 通过环境变量配置，提高安全性
ZHIPU_API_KEY = os.getenv('ZHIPU_API_KEY')
assert ZHIPU_API_KEY is not None, "ZHIPU_API_KEY 环境变量未设置"
ZHIPU_CLIENT = None  # 将在主文件中初始化

# ==================== 文件配置 ====================
# 各种数据文件的路径配置

# 对话历史记录文件 - 相对路径
CONVERSATION_HISTORY_FILE = "conversation_history.json"

# 记录日志目录 - 相对路径
RECORD_LOGS_DIR = "record_logs"

# 永久记忆文件 - 通过环境变量配置，支持自定义路径
FOREVER_MEMORY_FILE = os.getenv('FOREVER_MEMORY_FILE')

# 连接配置文件 - 相对路径
CONNECTION_CONFIG_FILE = "connection_config.json"

# ==================== 系统配置 ====================
# 系统运行时的各种参数配置

# 历史记录最大长度 - 控制对话历史的保留数量
MAX_HISTORY_LENGTH = 50

# 最大循环次数 - 持续回复时的最大轮数，避免无限循环
MAX_CYCLE_TIMES = 30

# 最大重试次数 - 操作失败时的重试次数
MAX_RETRY_TIMES = 3

# 等待间隔（秒） - 操作间的延迟时间
WAIT_INTERVAL = 1

# ==================== 快捷键配置 ====================
# 快捷键映射配置，用于快速启动应用

# 快捷键字典 - 键为单字符快捷键，值为对应的应用名称
SHORTCUTS = {
    'w': '打开微信',     # w键打开微信
    'q': '打开QQ',       # q键打开QQ
    'd': '打开抖音',     # d键打开抖音
    'k': '打开快手',     # k键打开快手
    't': '打开淘宝',     # t键打开淘宝
    'm': '打开QQ音乐'    # m键打开QQ音乐
}

