"""
WebSocket 消息处理模块
======================

按功能拆分的 WebSocket 消息处理器。

主要组件:
    - handle_command: 命令处理
    - handle_multimodal_chat: 多模态聊天处理
    - handle_tts_speak: TTS 语音播放
    - handle_tts_synth: TTS 语音合成
    - handle_tts_select_model: TTS 模型选择
    - handle_tts_load_models: TTS 模型加载
    - handle_tts_settings: TTS 设置
    - handle_connect_device: 设备连接
    - handle_disconnect_device: 设备断开
    - handle_refresh_devices: 刷新设备列表
    - handle_detect_devices: 检测设备
    - handle_generate_image: 图像生成
    - handle_generate_video: 视频生成
    - handle_terminate: 终止操作
    - handle_start_scrcpy: 启动投屏
    - handle_system_check: 系统检查
    - handle_file_management: 文件管理
    - handle_get_page_data: 获取页面数据
    - handle_delete_audio: 删除音频
    - handle_delete_all_audio: 删除所有音频
    - handle_shortcut: 快捷键处理
"""
import logging

logger = logging.getLogger(__name__)

from .command_handler import handle_command, handle_multimodal_chat
from .tts_handler import (
    handle_tts_speak, handle_tts_synth, handle_tts_select_model,
    handle_tts_load_models, handle_tts_settings
)
from .device_handler import (
    handle_connect_device, handle_disconnect_device,
    handle_refresh_devices, handle_detect_devices
)
from .media_handler import (
    handle_generate_image, handle_generate_video,
    start_video_result_polling
)
from .system_handler import (
    handle_terminate, handle_start_scrcpy, handle_system_check,
    handle_file_management, handle_get_page_data,
    handle_delete_audio, handle_delete_all_audio, handle_shortcut
)

__all__ = [
    'handle_command', 'handle_multimodal_chat',
    'handle_tts_speak', 'handle_tts_synth', 'handle_tts_select_model',
    'handle_tts_load_models', 'handle_tts_settings',
    'handle_connect_device', 'handle_disconnect_device',
    'handle_refresh_devices', 'handle_detect_devices',
    'handle_generate_image', 'handle_generate_video',
    'start_video_result_polling',
    'handle_terminate', 'handle_start_scrcpy', 'handle_system_check',
    'handle_file_management', 'handle_get_page_data',
    'handle_delete_audio', 'handle_delete_all_audio', 'handle_shortcut',
]
