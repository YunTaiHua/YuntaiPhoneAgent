"""
handlers - WebSocket消息处理模块
按功能拆分的消息处理器
"""

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
    # 命令处理
    'handle_command', 'handle_multimodal_chat',
    # TTS处理
    'handle_tts_speak', 'handle_tts_synth', 'handle_tts_select_model',
    'handle_tts_load_models', 'handle_tts_settings',
    # 设备处理
    'handle_connect_device', 'handle_disconnect_device',
    'handle_refresh_devices', 'handle_detect_devices',
    # 媒体处理
    'handle_generate_image', 'handle_generate_video',
    'start_video_result_polling',
    # 系统处理
    'handle_terminate', 'handle_start_scrcpy', 'handle_system_check',
    'handle_file_management', 'handle_get_page_data',
    'handle_delete_audio', 'handle_delete_all_audio', 'handle_shortcut',
]
