"""
system_handler.py - 系统相关处理
=================================

负责处理系统检查、投屏、文件管理等系统级操作。

主要功能:
    - handle_terminate: 处理任务终止操作
    - handle_start_scrcpy: 启动手机投屏
    - handle_system_check: 系统环境检查
    - handle_file_management: 文件管理信息
    - handle_get_page_data: 获取页面数据
    - handle_delete_audio: 删除单个音频
    - handle_delete_all_audio: 删除所有音频
    - handle_shortcut: 处理快捷键操作

系统检查内容:
    - ADB/HDC环境检查
    - 模型API检查
    - TTS功能检查
    - 设备连接状态检查

使用示例:
    >>> await handle_system_check(websocket, controller)
    >>> await handle_start_scrcpy(websocket, {"always_on_top": True}, controller)
"""

import os
import glob
import asyncio
import threading
import datetime
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from yuntai.core.config import SHORTCUTS, TTS_OUTPUT_DIR

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ..controller import WebController


async def handle_terminate(websocket, controller: "WebController"):
    """处理终止操作"""
    if not controller.is_executing and not controller.is_continuous_mode:
        await controller.send_toast("没有正在执行的操作", "info")
        return

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await controller.send_output(f"\n{'═' * 9} [{timestamp} 操作终止] {'═' * 9}\n", "output")
    await controller.send_output("🛑 正在发送终止信号...\n", "output")

    # 设置终止标志
    controller.terminate_flag.set()

    def terminate_thread():
        """异步终止线程"""
        try:
            # 停止持续回复
            if controller._current_reply_chain:
                controller._current_reply_chain.stop()

            try:
                if controller.task_chain:
                    controller.task_chain.stop_continuous_reply()
            except AttributeError as e:
                logger.debug(f"task_chain不可用: {e}")
            except Exception as e:
                logger.warning(f"停止持续回复失败: {e}")

            # 等待任务真正结束（检查ReplyChain是否还在运行）
            import time
            max_wait = 30  # 最多等待30秒
            waited = 0

            while waited < max_wait:
                # 检查ReplyChain是否还在运行
                is_still_running = False
                if controller._current_reply_chain:
                    try:
                        is_still_running = controller._current_reply_chain.is_running()
                    except AttributeError as e:
                        logger.debug(f"ReplyChain不可用: {e}")

                # 如果不再运行，退出等待
                if not is_still_running and not controller.is_executing:
                    break

                time.sleep(0.2)
                waited += 0.2

            # 强制更新状态
            controller.is_continuous_mode = False
            controller.is_executing = False

            # 发送状态更新
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_output("✅ 任务已完全终止\n", "output"))
                loop.run_until_complete(controller.send_state_update({
                    "is_executing": False,
                    "is_continuous_mode": False,
                    "execute_button_enabled": True,
                    "terminate_button_enabled": False
                }))
                loop.run_until_complete(controller.send_toast("任务已终止", "warning"))
            finally:
                loop.close()

        except Exception as e:
            logger.error("终止操作出错: %s", str(e), exc_info=True)
            # 确保状态被更新
            controller.is_continuous_mode = False
            controller.is_executing = False

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_state_update({
                    "is_executing": False,
                    "is_continuous_mode": False,
                    "execute_button_enabled": True,
                    "terminate_button_enabled": False
                }))
            finally:
                loop.close()

    threading.Thread(target=terminate_thread, daemon=True).start()


async def handle_start_scrcpy(websocket, data: dict, controller: "WebController"):
    """处理启动手机投屏"""
    try:
        if not controller.task_manager.is_connected:
            await controller.send_toast("请先连接设备", "warning")
            return

        import subprocess
        scrcpy_path = controller.scrcpy_path
        always_on_top = data.get("always_on_top", False) if data else False

        # 构建scrcpy命令参数
        cmd_args = []
        if scrcpy_path and Path(scrcpy_path).exists():
            cmd_args.append(scrcpy_path)
        else:
            cmd_args.append("scrcpy")

        # 添加窗口置顶参数
        if always_on_top:
            cmd_args.append("--always-on-top")

        # 启动scrcpy
        if os.name == 'nt':
            # Windows: 使用CREATE_NO_WINDOW隐藏控制台窗口，但不影响GUI窗口
            subprocess.Popen(cmd_args, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            # Linux/Mac: 直接启动
            subprocess.Popen(cmd_args)

        await controller.ws_manager.broadcast({
            "type": "scrcpy_started"
        })
    except Exception as e:
        await controller.send_toast(f"启动投屏失败: {str(e)}", "error")


async def handle_system_check(websocket, controller: "WebController"):
    """处理系统检查请求"""
    def check_thread():
        try:
            result_text = ""
            success = True

            # 检查ADB/HDC
            try:
                if controller.device_type == "harmonyos":
                    tool_result = controller.task_manager.utils.check_hdc()
                    tool_name = "HDC"
                else:
                    tool_result = controller.task_manager.utils.check_system_requirements()
                    tool_name = "ADB"
            except AttributeError as e:
                logger.debug(f"设备检查工具不可用: {e}")
                tool_result = False
                tool_name = "ADB"
            except Exception as e:
                logger.warning(f"设备检查失败: {e}")
                tool_result = False
                tool_name = "ADB"

            result_text += "=" * 50 + "\n"
            result_text += f"📱 {tool_name} 环境检查\n"
            result_text += "=" * 50 + "\n"
            if tool_result:
                result_text += f"✅ {tool_name}检查通过\n"
            else:
                result_text += f"❌ {tool_name}检查失败\n"
                success = False
            result_text += "\n"

            # 检查API
            try:
                from yuntai.core.config import ZHIPU_API_BASE_URL, ZHIPU_MODEL, ZHIPU_API_KEY
                api_result = controller.task_manager.utils.check_model_api(
                    ZHIPU_API_BASE_URL, ZHIPU_MODEL, ZHIPU_API_KEY
                )
            except AttributeError as e:
                logger.debug(f"API检查工具不可用: {e}")
                api_result = False
            except Exception as e:
                logger.warning(f"API检查失败: {e}")
                api_result = False

            result_text += "=" * 50 + "\n"
            result_text += "🤖 模型API检查\n"
            result_text += "=" * 50 + "\n"
            if api_result:
                result_text += "✅ 模型API检查通过\n"
            else:
                result_text += "❌ 模型API检查失败\n"
                success = False
            result_text += "\n"

            # 检查TTS
            result_text += "=" * 50 + "\n"
            result_text += "🎤 TTS功能检查\n"
            result_text += "=" * 50 + "\n"
            if controller.task_manager.tts_manager.tts_available:
                result_text += "✅ TTS模块可用\n"
            else:
                result_text += "⚠️ TTS模块不可用\n"
            result_text += "\n"

            # 检查设备连接
            result_text += "=" * 50 + "\n"
            result_text += "📱 设备连接检查\n"
            result_text += "=" * 50 + "\n"
            if controller.task_manager.is_connected:
                result_text += f"✅ 设备已连接: {controller.task_manager.device_id}\n"
            else:
                result_text += "⚠️ 设备未连接\n"
            result_text += "\n"

            result_text += "=" * 50 + "\n"
            result_text += "📋 检查结论\n"
            result_text += "=" * 50 + "\n"
            if success:
                result_text += "🎉 系统检查通过，核心组件正常\n"
            else:
                result_text += "⚠️ 系统检查发现一些问题\n"

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_personal_message({
                    "type": "system_check_result",
                    "result": result_text,
                    "status": "检查完成，核心组件正常" if success else "检查完成，发现一些问题",
                    "success": success
                }, websocket))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_personal_message({
                    "type": "system_check_result",
                    "result": f"检查出错: {str(e)}",
                    "status": "检查出错",
                    "success": False
                }, websocket))
            finally:
                loop.close()

    threading.Thread(target=check_thread, daemon=True).start()


async def handle_file_management(websocket, controller: "WebController"):
    """处理文件管理请求"""
    try:
        from yuntai.core.config import (
            CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR,
            FOREVER_MEMORY_FILE, CONNECTION_CONFIG_FILE
        )

        result_text = f"""文件管理:

历史记录文件: {CONVERSATION_HISTORY_FILE}
日志目录: {RECORD_LOGS_DIR}
永久记忆文件: {FOREVER_MEMORY_FILE}
连接配置文件: {CONNECTION_CONFIG_FILE}

TTS相关目录:
• GPT模型目录: {controller.task_manager.tts_manager.default_tts_config.get('gpt_model_dir', 'N/A')}
• SoVITS模型目录: {controller.task_manager.tts_manager.default_tts_config.get('sovits_model_dir', 'N/A')}
• 参考音频目录: {controller.task_manager.tts_manager.default_tts_config.get('ref_audio_root', 'N/A')}
• TTS输出目录: {controller.task_manager.tts_manager.default_tts_config.get('output_path', 'N/A')}

文件状态:
• 历史记录文件: {'存在' if Path(CONVERSATION_HISTORY_FILE).exists() else '不存在'}
• 日志目录: {'存在' if Path(RECORD_LOGS_DIR).exists() else '不存在'}
• 永久记忆文件: {'存在' if FOREVER_MEMORY_FILE and Path(FOREVER_MEMORY_FILE).exists() else '不存在'}
• 连接配置文件: {'存在' if Path(CONNECTION_CONFIG_FILE).exists() else '不存在'}
"""

        await controller.send_personal_message({
            "type": "file_management_result",
            "result": result_text
        }, websocket)
    except Exception as e:
        await controller.send_personal_message({
            "type": "file_management_result",
            "result": f"获取文件信息失败: {str(e)}"
        }, websocket)


async def handle_get_page_data(websocket, page: str, controller: "WebController"):
    """处理获取页面数据"""
    if page == "tts":
        await controller.send_personal_message({
            "type": "page_data",
            "page": "tts",
            "data": {
                "models": controller.get_tts_models(),
                "audio_history": controller.get_audio_history()
            }
        }, websocket)
    elif page == "connection":
        devices = controller.get_available_devices()
        await controller.send_personal_message({
            "type": "page_data",
            "page": "connection",
            "data": {
                "devices": devices,
                "is_connected": controller.task_manager.is_connected if hasattr(controller.task_manager, 'is_connected') else False,
                "device_id": controller.task_manager.device_id if hasattr(controller.task_manager, 'device_id') else ""
            }
        }, websocket)
    elif page == "history":
        await controller.send_personal_message({
            "type": "page_data",
            "page": "history",
            "data": {
                "history": controller.get_history()
            }
        }, websocket)
    elif page == "dynamic":
        await controller.send_personal_message({
            "type": "page_data",
            "page": "dynamic",
            "data": controller.get_dynamic_features()
        }, websocket)


async def handle_delete_audio(websocket, data: dict, controller: "WebController"):
    """处理删除单个音频"""
    filename = data.get("filename")
    if filename:
        try:
            filepath = Path(TTS_OUTPUT_DIR) / filename
            if filepath.exists():
                filepath.unlink()
            await controller.send_toast(f"已删除: {filename}", "success")
            await controller.ws_manager.broadcast({
                "type": "audio_deleted",
                "audio_history": controller.get_audio_history()
            })
        except Exception as e:
            await controller.send_toast(f"删除失败: {str(e)}", "error")


async def handle_delete_all_audio(websocket, controller: "WebController"):
    """处理删除所有音频"""
    try:
        # 删除TTS输出目录下的所有wav文件
        tts_dir = Path(TTS_OUTPUT_DIR)
        audio_files = list(tts_dir.glob("*.wav"))
        deleted_count = 0
        for filepath in audio_files:
            try:
                filepath.unlink()
                deleted_count += 1
            except OSError as e:
                logger.warning(f"删除文件失败 {filepath}: {e}")

        await controller.send_toast(f"已删除 {deleted_count} 个音频文件", "success")
        await controller.ws_manager.broadcast({
            "type": "audio_deleted",
            "audio_history": controller.get_audio_history()
        })
    except Exception as e:
        await controller.send_toast(f"删除失败: {str(e)}", "error")


async def handle_shortcut(websocket, data: dict, controller: "WebController"):
    """处理快捷键"""
    from .command_handler import handle_command
    key = data.get("key")
    if key in SHORTCUTS:
        command = SHORTCUTS[key]
        await handle_command(websocket, {"command": command}, controller)
