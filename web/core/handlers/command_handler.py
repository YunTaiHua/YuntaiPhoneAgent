"""
command_handler.py - 命令执行处理
==================================

负责处理用户命令执行的核心模块。

主要功能:
    - handle_command: 处理普通命令执行
    - handle_multimodal_chat: 处理多模态聊天（文本+文件）

处理流程:
    1. 接收命令和附件文件
    2. 启动输出捕获
    3. 执行任务链处理
    4. 支持持续回复模式
    5. 保存历史记录

使用示例:
    >>> await handle_command(websocket, {"command": "打开微信"}, controller)
"""

import asyncio
import threading
import datetime
import traceback
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from phone_agent.events import get_global_event_emitter

logger = logging.getLogger(__name__)

DIVIDER = "═" * 50


def _is_content_event(event_type: str) -> bool:
    return event_type in {
        "thinking_chunk",
        "action_decoded",
        "performance_metric",
        "result",
        "error",
    }


def _format_action_lines(action: dict) -> str:
    if not isinstance(action, dict):
        return str(action)
    lines = []
    for key, value in action.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)

if TYPE_CHECKING:
    from ..controller import WebController


def _format_agent_event_text(event: dict) -> str:
    """Fallback text renderer for structured events."""
    event_type = event.get("type", "")
    payload = event.get("payload", {}) or {}
    if event_type == "thinking_chunk":
        return payload.get("text", "")
    if event_type == "thinking_complete":
        return "\n"
    if event_type == "task_type":
        task_type = payload.get("task_type", "")
        if task_type == "free_chat":
            return f"📋 任务类型: {task_type}\n"
        return f"📋 任务类型: {task_type}\n\n{DIVIDER}\n💭 思考过程\n{DIVIDER}\n"
    if event_type == "run_started":
        return ""
    if event_type == "action_decoded":
        action = payload.get("action", {})
        action_text = _format_action_lines(action)
        return f"\n{DIVIDER}\n🎯 动作\n{DIVIDER}\n{action_text}\n"
    if event_type == "action_executed":
        return ""
    if event_type == "performance_metric":
        if payload.get("name") == "label":
            return f"\n{DIVIDER}\n⏱️  性能指标\n{DIVIDER}\n"
        return f"{payload.get('label', payload.get('name', 'metric'))}: {payload.get('value', '')}{payload.get('unit', '')}\n"
    if event_type == "result":
        msg = payload.get("message", "")
        return f"\n🎉 结果：{msg}\n" if msg else ""
    if event_type == "error":
        return f"❌ 错误：{payload.get('message', '')}\n"
    if event_type == "status":
        return f"{payload.get('message', '')}\n"
    if event_type == "run_finished":
        return ""
    return ""


async def handle_command(websocket, data: dict, controller: "WebController"):
    """
    处理命令执行
    
    接收用户命令，通过任务链处理并返回结果。
    支持多模态输入（文本+附件文件）和持续回复模式。
    
    Args:
        websocket: WebSocket连接
        data: 请求数据，包含command字段
        controller: Web控制器实例
    """
    if controller.is_executing:
        await controller.send_toast("请等待当前任务完成", "warning")
        return

    command = data.get("command", "").strip()
    has_attachments = len(controller.attached_files) > 0

    if not command and not has_attachments:
        await controller.send_toast("请输入命令或选择文件", "warning")
        return

    controller.is_executing = True
    await controller.send_state_update({
        "is_executing": True,
        "execute_button_enabled": False,
        "terminate_button_enabled": True
    })

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await controller.send_output(f"\n{'═' * 9} [{timestamp} 对话开始] {'═' * 9}\n", "output")

    if has_attachments:
        await controller.send_output(f"💭 多模态指令: {command if command else '[无文本]'}\n", "output")
        await controller.send_output(f"📌 附件数量: {len(controller.attached_files)} 个文件\n", "output")
    else:
        await controller.send_output(f"💭 指令: {command}\n", "output")

    loop = asyncio.get_event_loop()
    emitter = get_global_event_emitter()

    def on_agent_event(event: dict):
        asyncio.run_coroutine_threadsafe(controller.send_agent_event(event), loop)
        text = _format_agent_event_text(event)
        if text:
            asyncio.run_coroutine_threadsafe(controller.send_output(text, "output"), loop)

    def run_command():
        result_text = ""
        event_seen = False

        def on_agent_event_with_flag(event: dict):
            nonlocal event_seen
            if _is_content_event(event.get("type", "")):
                event_seen = True
            on_agent_event(event)

        emitter.on(on_agent_event_with_flag)
        try:
            if has_attachments:
                result = handle_multimodal_chat(command, controller.attached_files, controller, loop)
                result_text = result
            else:
                try:
                    controller.task_chain.device_id = controller.task_manager.device_id if controller.task_manager.is_connected else ""
                    controller.task_chain.task_args = controller.task_manager.task_args if controller.task_manager.is_connected else None
                    result, task_info = controller.task_chain.process(command)
                    result_text = str(result) if result else ""

                    # 检查是否是持续回复模式
                    if result_text and result_text.startswith("🔄CONTINUOUS_REPLY:"):
                        parts = result_text.split(":")
                        if len(parts) >= 3:
                            app_name = parts[1]
                            chat_object = parts[2]
                            # 启动持续回复线程
                            controller.is_continuous_mode = True
                            asyncio.run_coroutine_threadsafe(
                                controller.send_state_update({
                                    "is_continuous_mode": True
                                }), loop)

                            def run_continuous_reply():
                                try:
                                    # 直接调用continuous_reply而不是start_continuous_reply_async
                                    # 因为start_continuous_reply_async会创建新线程导致外层线程提前结束
                                    controller.task_chain.reply_chain.continuous_reply(
                                        app_name, chat_object, max_cycles=100
                                    )
                                except Exception as e:
                                    logger.error("持续回复错误: %s", str(e), exc_info=True)
                                    asyncio.run_coroutine_threadsafe(
                                        controller.send_agent_event({
                                            "type": "error",
                                            "source": "web.command_handler",
                                            "level": "error",
                                            "payload": {"message": f"持续回复错误: {str(e)}"}
                                        }),
                                        loop,
                                    )
                                finally:
                                    emitter.off(on_agent_event_with_flag)
                                    controller.is_continuous_mode = False
                                    asyncio.run_coroutine_threadsafe(
                                        controller.send_state_update({
                                            "is_continuous_mode": False,
                                            "is_executing": False,
                                            "execute_button_enabled": True,
                                            "terminate_button_enabled": False
                                        }), loop)

                            threading.Thread(target=run_continuous_reply, daemon=True).start()
                            # 不输出任何结果信息
                            result_text = ""
                except Exception as e:
                    result = f"❌ 执行失败: {str(e)}"
                    result_text = result

            # 保存历史记录
            if command:
                controller.save_history(command, result_text)

        except Exception as e:
            traceback.print_exc()
            result_text = f"❌ 错误：{str(e)}"

        finally:
            if not controller.is_continuous_mode:
                emitter.off(on_agent_event_with_flag)
            if result_text and not has_attachments and not event_seen:
                fallback_text = result_text if result_text.startswith("❌") else f"🎉 结果：{result_text}\n"
                asyncio.run_coroutine_threadsafe(
                    controller.send_agent_event({
                        "type": "result" if not result_text.startswith("❌") else "error",
                        "source": "web.command_handler",
                        "level": "error" if result_text.startswith("❌") else "info",
                        "payload": {
                            "message": result_text if result_text.startswith("❌") else result_text
                        },
                    }),
                    loop,
                )
                asyncio.run_coroutine_threadsafe(controller.send_output(fallback_text, "output"), loop)

            controller.attached_files.clear()
            if not controller.is_continuous_mode:
                controller.is_executing = False
                asyncio.run_coroutine_threadsafe(
                    controller.send_state_update({
                        "is_executing": False,
                        "execute_button_enabled": True,
                        "terminate_button_enabled": False,
                        "attached_files": []
                    }), loop)

    threading.Thread(target=run_command, daemon=True).start()


def handle_multimodal_chat(text: str, file_paths: list, controller: "WebController", loop) -> str:
    """
    处理多模态聊天
    
    处理包含文件的聊天请求，支持图片、文档等多种文件类型。
    
    Args:
        text: 用户输入的文本
        file_paths: 附加文件路径列表
        controller: Web控制器实例
        loop: 事件循环
    
    Returns:
        str: 处理结果文本
    """
    try:
        valid_files = [f for f in file_paths if Path(f).exists()]
        if not valid_files:
            return "没有有效的文件"

        from yuntai.processors.multimodal_processor import MultimodalProcessor
        processor = MultimodalProcessor()

        asyncio.run_coroutine_threadsafe(
            controller.send_output("🖼️ 正在处理多模态内容...\n", "output"), loop)

        def on_info(text: str):
            asyncio.run_coroutine_threadsafe(controller.send_output(text, "output"), loop)

        def on_token(text: str):
            asyncio.run_coroutine_threadsafe(controller.send_output(text, "output"), loop)

        success, response, _ = processor.process_with_files(
            text=text, file_paths=valid_files, history=[],
            temperature=0.7, max_tokens=2000,
            on_token=on_token,
            on_info=on_info,
        )

        if success:
            asyncio.run_coroutine_threadsafe(controller.send_output(f"🎉 结果：{response}\n", "output"), loop)
            # TTS播报
            if controller.tts_enabled and len(response) > 5:
                try:
                    asyncio.run_coroutine_threadsafe(
                        controller.send_output("🔊 正在播报回复...\n", "output"), loop)
                    controller.task_manager.tts_manager.speak_text_intelligently(response)
                except Exception as e:
                    logger.warning("TTS播报失败: %s", str(e))

        return response if success else f"❌ 多模态分析失败: {response}"
    except Exception as e:
        return f"❌ 多模态处理失败: {str(e)}"
