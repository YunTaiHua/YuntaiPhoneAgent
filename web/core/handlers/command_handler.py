"""
command_handler.py - 命令执行处理
"""

import os
import asyncio
import threading
import datetime
import traceback
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..controller import WebController


async def handle_command(websocket, data: dict, controller: "WebController"):
    """处理命令执行"""
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

    def run_command():
        result_text = ""
        # 启动输出捕获
        controller.output_capture.start_capture(loop)
        try:
            if has_attachments:
                result = handle_multimodal_chat(command, controller.attached_files, controller, loop)
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
                                # 在持续回复线程中启动输出捕获
                                controller.output_capture.start_capture(loop)
                                try:
                                    # 直接调用continuous_reply而不是start_continuous_reply_async
                                    # 因为start_continuous_reply_async会创建新线程导致外层线程提前结束
                                    controller.task_chain.reply_chain.continuous_reply(
                                        app_name, chat_object, max_cycles=100
                                    )
                                except Exception as e:
                                    print(f"❌ 持续回复错误: {str(e)}")
                                finally:
                                    # 持续回复结束后停止输出捕获
                                    controller.output_capture.stop_capture()
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
            # 输出结果或错误（在停止输出捕获之前）
            if result_text:
                if result_text.startswith("❌"):
                    print(result_text)
                else:
                    print(f"🎉 结果：{result_text}")

            # 如果不是持续回复模式，停止输出捕获
            if not controller.is_continuous_mode:
                controller.output_capture.stop_capture()

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
    """处理多模态聊天"""
    try:
        valid_files = [f for f in file_paths if os.path.exists(f)]
        if not valid_files:
            return "没有有效的文件"

        from yuntai.processors.multimodal_processor import MultimodalProcessor
        processor = MultimodalProcessor()

        asyncio.run_coroutine_threadsafe(
            controller.send_output("🖼️ 正在处理多模态内容...\n", "output"), loop)

        success, response, _ = processor.process_with_files(
            text=text, file_paths=valid_files, history=[],
            temperature=0.7, max_tokens=2000
        )

        if success:
            # TTS播报
            if controller.tts_enabled and len(response) > 5:
                try:
                    asyncio.run_coroutine_threadsafe(
                        controller.send_output("🔊 正在播报回复...\n", "output"), loop)
                    controller.task_manager.tts_manager.speak_text_intelligently(response)
                except Exception as e:
                    print(f"TTS播报失败: {e}")

        return "" if success else f"❌ 多模态分析失败: {response}"
    except Exception as e:
        return f"❌ 多模态处理失败: {str(e)}"
