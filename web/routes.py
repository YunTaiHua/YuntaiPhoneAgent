"""
routes.py - FastAPI路由定义
完整版本 - 支持所有Web端功能
"""

import os
import asyncio
import threading
import datetime
import traceback
import json
from typing import List, Dict, Any

from fastapi import WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from yuntai.core.config import PROJECT_ROOT, SHORTCUTS, CONVERSATION_HISTORY_FILE, TEMP_DIR, TTS_OUTPUT_DIR

from .controller import WebController
from .ws_manager import ConnectionManager

# 获取web模块所在目录
WEB_DIR = os.path.dirname(os.path.abspath(__file__))

# TTS音频文件目录（使用config中的定义）
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)

# 生成的图像和视频目录
GENERATED_DIR = os.path.join(PROJECT_ROOT, "temp", "generated")
os.makedirs(GENERATED_DIR, exist_ok=True)


def setup_routes(app, controller: WebController, ws_manager: ConnectionManager):
    """设置所有路由"""
    
    # ==================== 静态文件 ====================
    static_dir = os.path.join(WEB_DIR, "static")
    os.makedirs(static_dir, exist_ok=True)
    
    # ==================== 页面路由 ====================
    
    @app.get("/", response_class=HTMLResponse)
    async def index():
        """返回主页面"""
        html_file = os.path.join(WEB_DIR, "index.html")
        if os.path.exists(html_file):
            with open(html_file, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content=f"<h1>请创建 {html_file} 文件</h1>")
    
    # ==================== API路由 ====================
    
    @app.get("/api/state")
    async def get_state():
        """获取当前状态"""
        return JSONResponse(content=controller.get_state())
    
    @app.get("/api/tts/models")
    async def get_tts_models():
        """获取TTS模型列表"""
        return JSONResponse(content=controller.get_tts_models())
    
    @app.get("/api/tts/audio/{filename}")
    async def get_audio_file(filename: str):
        """获取音频文件"""
        from urllib.parse import unquote
        filename = unquote(filename)
        filepath = os.path.join(TTS_OUTPUT_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="音频文件不存在")
        return FileResponse(filepath, media_type="audio/wav")

    @app.get("/api/images/{filename}")
    async def get_image_file(filename: str):
        """获取图像文件"""
        from urllib.parse import unquote
        filename = unquote(filename)
        # 图像可能在多个目录
        possible_paths = [
            os.path.join(TEMP_DIR, "images", filename),  # MediaGenerator保存的位置
            os.path.join(GENERATED_DIR, filename),
            os.path.join(PROJECT_ROOT, "temp", "images", filename),
            os.path.join(PROJECT_ROOT, "temp", "generated", filename),
        ]
        for filepath in possible_paths:
            if os.path.exists(filepath):
                return FileResponse(filepath, media_type="image/png")
        raise HTTPException(status_code=404, detail="图像文件不存在")

    @app.get("/api/videos/{filename}")
    async def get_video_file(filename: str):
        """获取视频文件"""
        from urllib.parse import unquote
        filename = unquote(filename)
        # 视频可能在多个目录
        possible_paths = [
            os.path.join(TEMP_DIR, "videos", filename),  # MediaGenerator保存的位置
            os.path.join(GENERATED_DIR, filename),
            os.path.join(PROJECT_ROOT, "temp", "videos", filename),
            os.path.join(PROJECT_ROOT, "temp", "generated", filename),
        ]
        for filepath in possible_paths:
            if os.path.exists(filepath):
                return FileResponse(filepath, media_type="video/mp4")
        raise HTTPException(status_code=404, detail="视频文件不存在")

    @app.get("/api/tts/audio_history")
    async def get_audio_history():
        """获取历史音频列表"""
        return JSONResponse(content=controller.get_audio_history())
    
    @app.get("/api/shortcuts")
    async def get_shortcuts():
        """获取快捷键配置"""
        return JSONResponse(content=SHORTCUTS)
    
    @app.get("/api/history")
    async def get_history():
        """获取历史记录"""
        return JSONResponse(content=controller.get_history())
    
    @app.delete("/api/history")
    async def clear_history():
        """清空历史记录"""
        return JSONResponse(content=controller.clear_history())
    
    @app.get("/api/devices")
    async def get_devices():
        """获取设备列表"""
        return JSONResponse(content=controller.get_available_devices())
    
    @app.get("/api/generated/{filename}")
    async def get_generated_file(filename: str):
        """获取生成的图像或视频文件"""
        filepath = os.path.join(GENERATED_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 根据文件扩展名确定媒体类型
        ext = os.path.splitext(filename)[1].lower()
        media_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.mp4': 'video/mp4',
            '.webm': 'video/webm'
        }
        media_type = media_types.get(ext, 'application/octet-stream')
        return FileResponse(filepath, media_type=media_type)
    
    # ==================== 文件上传 ====================
    
    @app.post("/api/upload")
    async def upload_file(file: UploadFile = File(...)):
        """上传文件"""
        try:
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor()
            
            temp_dir = os.path.join(PROJECT_ROOT, "temp", "uploads")
            os.makedirs(temp_dir, exist_ok=True)
            
            file_path = os.path.join(temp_dir, file.filename)
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            if not processor.is_file_supported(file_path):
                os.remove(file_path)
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"不支持的文件类型: {file.filename}"}
                )
            
            controller.attached_files.append(file_path)
            
            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "attached_files": [os.path.basename(f) for f in controller.attached_files]
            })
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
    
    @app.delete("/api/upload/{filename}")
    async def remove_file(filename: str):
        """移除上传的文件"""
        try:
            temp_dir = os.path.join(PROJECT_ROOT, "temp", "uploads")
            file_path = os.path.join(temp_dir, filename)
            
            if file_path in controller.attached_files:
                controller.attached_files.remove(file_path)
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            return JSONResponse(content={
                "success": True,
                "attached_files": [os.path.basename(f) for f in controller.attached_files]
            })
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
    
    @app.delete("/api/upload")
    async def clear_files():
        """清空所有上传的文件"""
        try:
            controller.attached_files.clear()
            return JSONResponse(content={"success": True, "attached_files": []})
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "message": str(e)})
    
    # ==================== WebSocket路由 ====================
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket连接处理"""
        await ws_manager.connect(websocket)
        
        try:
            # 发送初始状态
            await controller.send_personal_message({
                "type": "init",
                "data": controller.get_state(),
                "tts_models": controller.get_tts_models()
            }, websocket)
            
            # 异步预加载TTS
            controller.preload_tts_async()
            
            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")
                
                if msg_type == "command":
                    await _handle_command(websocket, data, controller)
                elif msg_type == "terminate":
                    await _handle_terminate(websocket, controller)
                elif msg_type == "clear_output":
                    await controller.send_output("", "clear_output")
                elif msg_type == "toggle_theme":
                    controller.is_dark_theme = not controller.is_dark_theme
                    await controller.send_state_update({"is_dark_theme": controller.is_dark_theme})
                elif msg_type == "tts_synth":
                    await _handle_tts_synth(websocket, data, controller)
                elif msg_type == "tts_select_model":
                    await _handle_tts_select_model(websocket, data, controller)
                elif msg_type == "tts_stop":
                    try:
                        controller.task_manager.tts_manager.stop_current_audio_playback()
                    except:
                        pass
                    await controller.send_toast("已停止播放", "info")
                elif msg_type == "tts_load_models":
                    await _handle_tts_load_models(websocket, controller)
                elif msg_type == "tts_speak":
                    await _handle_tts_speak(websocket, data, controller)
                elif msg_type == "connect_device":
                    await _handle_connect_device(websocket, data, controller)
                elif msg_type == "disconnect_device":
                    await _handle_disconnect_device(websocket, controller)
                elif msg_type == "refresh_devices":
                    await _handle_refresh_devices(websocket, controller)
                elif msg_type == "shortcut":
                    await _handle_shortcut(websocket, data, controller)
                elif msg_type == "simulate_enter":
                    try:
                        from yuntai.core.agent_executor import AgentExecutor
                        AgentExecutor.user_confirm()
                        await controller.send_output("[用户已确认]\n", "output")
                    except Exception as e:
                        await controller.send_output(f"发送确认信号失败: {e}\n", "output")
                elif msg_type == "get_page_data":
                    await _handle_get_page_data(websocket, data.get("page"), controller)
                elif msg_type == "delete_audio":
                    await _handle_delete_audio(websocket, data, controller)
                elif msg_type == "clear_history":
                    controller.clear_history()
                    await controller.send_toast("历史记录已清空", "success")
                    await controller.ws_manager.broadcast({
                        "type": "history_cleared"
                    })
                elif msg_type == "generate_image":
                    await _handle_generate_image(websocket, data, controller)
                elif msg_type == "generate_video":
                    await _handle_generate_video(websocket, data, controller)
                elif msg_type == "start_scrcpy":
                    await _handle_start_scrcpy(websocket, controller)
                elif msg_type == "detect_devices":
                    await _handle_detect_devices(websocket, data, controller)
                elif msg_type == "system_check":
                    await _handle_system_check(websocket, controller)
                elif msg_type == "get_file_management":
                    await _handle_file_management(websocket, controller)
                elif msg_type == "tts_settings":
                    await _handle_tts_settings(websocket, data, controller)
        
        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)
        except Exception as e:
            print(f"WebSocket错误: {e}")
            traceback.print_exc()
            await ws_manager.disconnect(websocket)


# ==================== 消息处理函数 ====================

async def _handle_command(websocket, data: dict, controller: WebController):
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
                result = _handle_multimodal_chat(command, controller.attached_files, controller, loop)
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
                            result = f"✅ 持续回复模式已启动"
                            result_text = result
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


def _handle_multimodal_chat(text: str, file_paths: list, controller: WebController, loop) -> str:
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


async def _handle_tts_speak(websocket, data: dict, controller: WebController):
    """处理TTS语音播报（从控制中心）"""
    text = data.get("text", "").strip()
    if not text:
        await controller.send_toast("没有可播报的内容", "warning")
        return
    
    # 检查是否已选择参考音频和文本
    tts = controller.task_manager.tts_manager
    ref_audio = tts.get_current_model("audio")
    ref_text = tts.get_current_model("text")
    
    if not ref_audio or not ref_text:
        await controller.send_toast("请先选择参考音频和文本", "warning")
        return
    
    def speak_thread():
        try:
            controller.task_manager.tts_manager.speak_text_intelligently(text)
        except Exception as e:
            print(f"TTS播报失败: {e}")
    
    threading.Thread(target=speak_thread, daemon=True).start()
    await controller.send_toast("正在播报...", "info")


async def _handle_terminate(websocket, controller: WebController):
    """处理终止操作"""
    if not controller.is_executing and not controller.is_continuous_mode:
        await controller.send_toast("没有正在执行的操作", "info")
        return
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await controller.send_output(f"\n{'═' * 9} [{timestamp} 操作终止] {'═' * 9}\n", "output")
    await controller.send_output("🛑 正在发送终止信号...\n", "output")
    
    if controller._current_reply_chain:
        controller._current_reply_chain.stop()
    
    try:
        if controller.task_chain:
            controller.task_chain.stop_continuous_reply()
    except:
        pass
    
    controller.terminate_flag.set()
    controller.is_continuous_mode = False
    controller.is_executing = False
    
    await controller.send_state_update({
        "is_executing": False,
        "is_continuous_mode": False,
        "execute_button_enabled": True,
        "terminate_button_enabled": False
    })
    
    await controller.send_toast("已发送终止信号", "warning")


async def _handle_tts_synth(websocket, data: dict, controller: WebController):
    """处理TTS合成"""
    text = data.get("text", "").strip()
    if not text:
        await controller.send_toast("请输入要合成的文本", "warning")
        return
    
    # 检查是否已选择参考音频和文本
    tts = controller.task_manager.tts_manager
    ref_audio = tts.get_current_model("audio")
    ref_text = tts.get_current_model("text")
    
    if not ref_audio or not ref_text:
        await controller.send_toast("请先选择参考音频和文本", "warning")
        return
    
    def synth_thread():
        try:
            tts = controller.task_manager.tts_manager
            # 使用正确的参数调用synthesize_text
            success, output_path = tts.synthesize_text(
                text=text,
                ref_audio_path=ref_audio,
                ref_text_path=ref_text,
                auto_play=False
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if success and output_path:
                    # 获取文件名
                    filename = os.path.basename(output_path)
                    
                    # 发送TTS日志输出
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "tts_log",
                        "message": f"✅ 语音合成完成: {filename}\n"
                    }))
                    
                    # 构建正确的音频URL
                    audio_url = f"/api/tts/audio/{filename}"
                    
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "tts_synth_complete",
                        "audio_path": audio_url,
                        "audio_history": controller.get_audio_history()
                    }))
                else:
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "tts_log",
                        "message": "❌ 语音合成失败\n"
                    }))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.ws_manager.broadcast({
                    "type": "tts_log",
                    "message": f"❌ 合成错误: {str(e)}\n"
                }))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.ws_manager.broadcast({
                    "type": "tts_log",
                    "message": f"❌ 合成错误: {str(e)}\n"
                }))
            finally:
                loop.close()
    
    threading.Thread(target=synth_thread, daemon=True).start()


async def _handle_tts_select_model(websocket, data: dict, controller: WebController):
    """处理TTS模型选择"""
    model_type = data.get("model_type")
    model_name = data.get("model_name")
    
    if not model_type or not model_name:
        await controller.send_toast("参数错误", "error")
        return
    
    try:
        tts = controller.task_manager.tts_manager
        success = tts.set_current_model(model_type, model_name)
        if success:
            await controller.send_toast(f"已选择: {model_name}", "success")
            await controller.ws_manager.broadcast({
                "type": "tts_models_update",
                "data": controller.get_tts_models()
            })
        else:
            await controller.send_toast(f"选择失败: 模型不存在", "error")
    except Exception as e:
        await controller.send_toast(f"选择失败: {str(e)}", "error")


async def _handle_tts_load_models(websocket, controller: WebController):
    """处理加载TTS模型"""
    await controller.send_tts_loading("正在加载TTS模型...", True)
    
    def load_thread():
        try:
            success = controller.task_manager.preload_tts_modules()
            controller.tts_enabled = success
            controller._tts_loaded = True
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if success:
                    loop.run_until_complete(controller.send_toast("TTS模型加载成功", "success"))
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "tts_models_update",
                        "data": controller.get_tts_models()
                    }))
                else:
                    loop.run_until_complete(controller.send_toast("TTS模型加载失败", "error"))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_toast(f"加载错误: {str(e)}", "error"))
            finally:
                loop.close()
        finally:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_tts_loading("", False))
            finally:
                loop.close()
    
    threading.Thread(target=load_thread, daemon=True).start()


async def _handle_refresh_devices(websocket, controller: WebController):
    """处理刷新设备列表"""
    devices = controller.get_available_devices()
    await controller.send_personal_message({
        "type": "devices_update",
        "devices": devices
    }, websocket)
    await controller.send_toast(f"找到 {len(devices)} 个设备", "info")


async def _handle_connect_device(websocket, data: dict, controller: WebController):
    """处理设备连接"""
    device_type = data.get("device_type", "android")
    connection_type = data.get("connection_type", "wireless")
    
    await controller.send_output("正在连接设备...\n", "output")
    
    def connect_thread():
        try:
            # 构建配置字典
            config = {
                "device_type": device_type,
                "connection_type": connection_type
            }
            
            if connection_type == "usb":
                device_id = data.get("device_id", "")
                config["usb_device_id"] = device_id
            else:
                ip = data.get("ip", "")
                port = data.get("port", "5555")
                # 检查IP是否已经包含端口（格式为 ip:port）
                if ":" in ip:
                    # IP已经包含端口，直接使用
                    config["wireless_ip"] = ip
                else:
                    # IP不包含端口，添加端口
                    config["wireless_ip"] = f"{ip}:{port}" if ip else ""
            
            # 使用TaskManager的connect_device方法
            success, device_id, message = controller.task_manager.connect_device(config)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if success:
                    loop.run_until_complete(controller.send_output(f"✅ 设备连接成功: {device_id}\n", "output"))
                    loop.run_until_complete(controller.send_toast(f"已连接: {device_id}", "success"))
                    loop.run_until_complete(controller.send_state_update({
                        "is_connected": True,
                        "device_id": device_id,
                        "device_type": device_type
                    }))
                else:
                    loop.run_until_complete(controller.send_output(f"❌ 设备连接失败: {message}\n", "output"))
                    loop.run_until_complete(controller.send_toast(f"连接失败: {message}", "error"))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_output(f"❌ 连接错误: {str(e)}\n", "output"))
                loop.run_until_complete(controller.send_toast(f"连接错误: {str(e)}", "error"))
            finally:
                loop.close()
    
    threading.Thread(target=connect_thread, daemon=True).start()


async def _handle_disconnect_device(websocket, controller: WebController):
    """处理设备断开"""
    try:
        controller.task_manager.disconnect_device()
        await controller.send_output("✅ 设备已断开\n", "output")
        await controller.send_toast("设备已断开", "info")
        await controller.send_state_update({"is_connected": False, "device_id": ""})
    except Exception as e:
        await controller.send_toast(f"断开失败: {str(e)}", "error")


async def _handle_shortcut(websocket, data: dict, controller: WebController):
    """处理快捷键"""
    key = data.get("key")
    if key in SHORTCUTS:
        command = SHORTCUTS[key]
        await _handle_command(websocket, {"command": command}, controller)


async def _handle_delete_audio(websocket, data: dict, controller: WebController):
    """处理删除音频"""
    filename = data.get("filename")
    if filename:
        try:
            filepath = os.path.join(TTS_OUTPUT_DIR, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            await controller.send_toast(f"已删除: {filename}", "success")
            await controller.ws_manager.broadcast({
                "type": "audio_deleted",
                "audio_history": controller.get_audio_history()
            })
        except Exception as e:
            await controller.send_toast(f"删除失败: {str(e)}", "error")


async def _handle_get_page_data(websocket, page: str, controller: WebController):
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


async def _handle_generate_image(websocket, data: dict, controller: WebController):
    """处理图像生成"""
    prompt = data.get("prompt", "").strip()
    size = data.get("size", "1280x1280")
    quality = data.get("quality", "standard")
    
    if not prompt:
        await controller.send_toast("请输入图像描述", "warning")
        return
    
    await controller.send_toast("正在生成图像...", "info")
    
    def generate_thread():
        try:
            from yuntai.processors.media_generator import MediaGenerator
            import time
            
            generator = MediaGenerator()
            
            # 发送日志
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(controller.ws_manager.broadcast({
                "type": "image_log",
                "message": "🔄 正在生成图像...\n"
            }))
            loop.close()
            
            # 使用正确的参数调用generate_image（size是字符串，不是width/height）
            result = generator.generate_image(
                prompt=prompt,
                size=size,
                quality=quality
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if result and result.get("success"):
                    # 从结果中获取图像URL
                    image_data = result.get("data", {})
                    image_url = image_data.get("data", [{}])[0].get("url", "") if image_data else ""
                    
                    if image_url:
                        # 下载图像到本地
                        filename = f"cogview_{int(time.time())}.png"
                        try:
                            image_path = generator.download_image(image_url, filename.replace('.png', ''))

                            # 构建可访问的URL
                            image_filename = os.path.basename(image_path) if image_path else filename
                            image_url_for_web = f"/api/images/{image_filename}"

                            loop.run_until_complete(controller.ws_manager.broadcast({
                                "type": "image_log",
                                "message": f"✅ 图像生成成功！\n📁 保存路径: {image_path}\n📐 图像尺寸: {size}\n✨ 生成质量: {quality}\n"
                            }))

                            loop.run_until_complete(controller.ws_manager.broadcast({
                                "type": "image_generated",
                                "image_path": image_url_for_web
                            }))

                            loop.run_until_complete(controller.send_toast("图像生成成功", "success"))
                        except Exception as download_error:
                            loop.run_until_complete(controller.ws_manager.broadcast({
                                "type": "image_log",
                                "message": f"❌ 图像下载失败: {download_error}\n"
                            }))
                            loop.run_until_complete(controller.send_toast("图像下载失败", "error"))
                    else:
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "image_log",
                            "message": "❌ 图像生成失败：未获取到图像URL\n"
                        }))
                        loop.run_until_complete(controller.send_toast("图像生成失败：未获取到图像URL", "error"))
                else:
                    error_msg = result.get("message", "未知错误") if result else "生成失败"
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "image_log",
                        "message": f"❌ 图像生成失败: {error_msg}\n"
                    }))
                    loop.run_until_complete(controller.send_toast(f"图像生成失败: {error_msg}", "error"))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.ws_manager.broadcast({
                    "type": "image_log",
                    "message": f"❌ 生成错误: {str(e)}\n"
                }))
                loop.run_until_complete(controller.send_toast(f"生成错误: {str(e)}", "error"))
            finally:
                loop.close()
    
    threading.Thread(target=generate_thread, daemon=True).start()


async def _handle_generate_video(websocket, data: dict, controller: WebController):
    """处理视频生成"""
    prompt = data.get("prompt", "").strip()
    image_urls = data.get("image_urls", [])
    size = data.get("size", "1920x1080")
    fps = int(data.get("fps", "30"))
    quality = data.get("quality", "quality")
    with_audio = data.get("with_audio", True)
    
    if not prompt:
        await controller.send_toast("请输入视频描述", "warning")
        return
    
    await controller.send_toast("正在生成视频...", "info")
    
    def generate_thread():
        try:
            from yuntai.processors.media_generator import MediaGenerator
            import time
            
            generator = MediaGenerator()
            
            # 发送日志
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(controller.ws_manager.broadcast({
                "type": "video_log",
                "message": "🔄 正在提交视频生成任务...\n"
            }))
            loop.close()
            
            # 使用正确的参数调用generate_video
            result = generator.generate_video(
                prompt=prompt,
                image_urls=image_urls if image_urls else None,
                size=size,
                fps=fps,
                quality=quality,
                with_audio=with_audio
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if result and result.get("success"):
                    task_id = result.get("task_id")
                    task_status = result.get("task_status", "UNKNOWN")
                    
                    if task_status == "FAIL":
                        error_msg = result.get('message', '未知错误')
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"❌ 视频生成立即失败\n错误信息: {error_msg}\n"
                        }))
                        loop.run_until_complete(controller.send_toast(f"视频生成失败: {error_msg[:30]}", "error"))
                    else:
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"✅ 视频生成任务已提交！\n📐 视频尺寸: {size}\n⏳ 请耐心等待结果...\n"
                        }))
                        loop.run_until_complete(controller.send_toast("视频生成任务已提交", "success"))
                        
                        # 开始轮询检查结果
                        if task_id:
                            start_video_result_polling(controller, task_id, len(image_urls))
                else:
                    error_msg = result.get("message", "未知错误") if result else "生成失败"
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "video_log",
                        "message": f"❌ 视频生成失败: {error_msg}\n"
                    }))
                    loop.run_until_complete(controller.send_toast(f"视频生成失败: {error_msg}", "error"))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.ws_manager.broadcast({
                    "type": "video_log",
                    "message": f"❌ 生成错误: {str(e)}\n"
                }))
                loop.run_until_complete(controller.send_toast(f"生成错误: {str(e)}", "error"))
            finally:
                loop.close()
    
    threading.Thread(target=generate_thread, daemon=True).start()


def start_video_result_polling(controller, task_id: str, image_count: int = 0):
    """开始轮询检查视频生成结果"""
    import time
    
    def polling_thread():
        try:
            from yuntai.processors.media_generator import MediaGenerator
            generator = MediaGenerator()
            
            def polling_callback(event_type, attempt, task_id, status, interval):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    if event_type == "START":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": "🎬 视频生成任务已提交\n" + "-" * 50 + "\n"
                        }))
                    elif event_type == "WAIT":
                        wait_text = f"⏳ 等待检查...\n" if attempt > 1 else f"⏰ 首次检查在{interval}秒后开始\n"
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": wait_text
                        }))
                    elif event_type == "CHECK":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"📊 第{attempt}次检查: 任务ID={task_id}, 状态={status}\n"
                        }))
                    elif event_type == "SUCCESS":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"🎉 第{attempt}次检查成功！\n" + "-" * 50 + "\n"
                        }))
                    elif event_type == "FAIL":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"❌ 第{attempt}次检查失败: {status}\n" + "-" * 50 + "\n"
                        }))
                    elif event_type == "TIMEOUT":
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"⚠️ 达到最大尝试次数，停止轮询\n" + "-" * 50 + "\n"
                        }))
                finally:
                    loop.close()

            result = generator.wait_for_video_completion(
                task_id,
                image_count=image_count,
                interval=10,
                max_attempts=100,
                callback=polling_callback
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if result["success"] and result["status"] == "SUCCESS":
                    cover_url = result.get("cover_url")
                    video_url = result.get("video_url")

                    filename = f"cogvideox_{int(time.time())}"
                    download_result = generator.download_video(video_url, cover_url, filename)

                    if download_result["success"]:
                        video_path = download_result["video_path"]
                        cover_path = download_result.get("cover_path")

                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"\n✅ 视频生成完成！\n📁 视频保存路径: {video_path}\n💾 视频大小: {download_result.get('video_size', 0):.1f} MB\n"
                        }))

                        # 构建正确的视频URL
                        video_filename = os.path.basename(video_path)
                        video_url = f"/api/videos/{video_filename}"

                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_generated",
                            "video_path": video_url
                        }))

                        loop.run_until_complete(controller.send_toast("视频生成完成", "success"))
                    else:
                        loop.run_until_complete(controller.ws_manager.broadcast({
                            "type": "video_log",
                            "message": f"\n❌ 视频下载失败: {download_result['message']}\n"
                        }))

                elif result.get("status") == "FAIL":
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "video_log",
                        "message": f"\n❌ 视频生成失败\n错误信息: {result.get('message', '未知错误')}\n"
                    }))

                else:
                    loop.run_until_complete(controller.ws_manager.broadcast({
                        "type": "video_log",
                        "message": f"\n⚠️ 视频生成超时\n"
                    }))
            finally:
                loop.close()

        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.ws_manager.broadcast({
                    "type": "video_log",
                    "message": f"\n❌ 轮询检查出错: {str(e)}\n"
                }))
            finally:
                loop.close()

    threading.Thread(target=polling_thread, daemon=True).start()


async def _handle_start_scrcpy(websocket, controller: WebController):
    """处理启动手机投屏"""
    try:
        if not controller.task_manager.is_connected:
            await controller.send_toast("请先连接设备", "warning")
            return
        
        import subprocess
        scrcpy_path = controller.scrcpy_path
        
        if scrcpy_path and os.path.exists(scrcpy_path):
            subprocess.Popen([scrcpy_path], shell=True)
        else:
            # 尝试使用系统scrcpy
            subprocess.Popen(["scrcpy"], shell=True)
        
        await controller.ws_manager.broadcast({
            "type": "scrcpy_started"
        })
    except Exception as e:
        await controller.send_toast(f"启动投屏失败: {str(e)}", "error")


async def _handle_detect_devices(websocket, data: dict, controller: WebController):
    """处理设备检测请求 - 弹窗显示结果"""
    device_type = data.get("device_type", "android")
    
    def detect_thread():
        try:
            devices = controller.task_manager.detect_devices(device_type)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_personal_message({
                    "type": "devices_detected",
                    "devices": devices,
                    "device_type": device_type
                }, websocket))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_personal_message({
                    "type": "devices_detected",
                    "devices": [],
                    "device_type": device_type,
                    "error": str(e)
                }, websocket))
            finally:
                loop.close()
    
    threading.Thread(target=detect_thread, daemon=True).start()


async def _handle_system_check(websocket, controller: WebController):
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
            except:
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
            except:
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


async def _handle_file_management(websocket, controller: WebController):
    """处理文件管理请求"""
    try:
        from yuntai.core.config import (
            CONVERSATION_HISTORY_FILE, RECORD_LOGS_DIR,
            FOREVER_MEMORY_FILE, CONNECTION_CONFIG_FILE
        )
        
        result_text = f"""文件管理:

历史记录文件: {CONVERSATION_HISTORY_FILE}
日志目录: {RECORD_LOGS_DIR}/
永久记忆文件: {FOREVER_MEMORY_FILE}
连接配置文件: {CONNECTION_CONFIG_FILE}

TTS相关目录:
• GPT模型目录: {controller.task_manager.tts_manager.default_tts_config.get('gpt_model_dir', 'N/A')}
• SoVITS模型目录: {controller.task_manager.tts_manager.default_tts_config.get('sovits_model_dir', 'N/A')}
• 参考音频目录: {controller.task_manager.tts_manager.default_tts_config.get('ref_audio_root', 'N/A')}
• TTS输出目录: {controller.task_manager.tts_manager.default_tts_config.get('output_path', 'N/A')}

文件状态:
• 历史记录文件: {'存在' if os.path.exists(CONVERSATION_HISTORY_FILE) else '不存在'}
• 日志目录: {'存在' if os.path.exists(RECORD_LOGS_DIR) else '不存在'}
• 永久记忆文件: {'存在' if os.path.exists(FOREVER_MEMORY_FILE) else '不存在'}
• 连接配置文件: {'存在' if os.path.exists(CONNECTION_CONFIG_FILE) else '不存在'}
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


async def _handle_tts_settings(websocket, data: dict, controller: WebController):
    """处理TTS设置请求"""
    try:
        enabled = data.get("enabled", False)
        gpt = data.get("gpt", "")
        sovits = data.get("sovits", "")
        audio = data.get("audio", "")
        
        controller.tts_enabled = enabled
        
        tts = controller.task_manager.tts_manager
        if gpt:
            tts.set_current_model("gpt", gpt)
        if sovits:
            tts.set_current_model("sovits", sovits)
        if audio:
            tts.set_current_model("audio", audio)
            # 自动匹配参考文本
            txt_filename = os.path.splitext(audio)[0] + '.txt'
            if txt_filename in tts.tts_files_database.get("text", {}):
                tts.set_current_model("text", txt_filename)
        
        # 更新状态
        await controller.send_state_update({
            "tts_enabled": enabled
        })
        await controller.ws_manager.broadcast({
            "type": "tts_models_update",
            "data": controller.get_tts_models()
        })
        
    except Exception as e:
        await controller.send_toast(f"TTS设置失败: {str(e)}", "error")
