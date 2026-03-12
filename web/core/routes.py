"""
routes.py - FastAPI路由定义
重构版本 - 按功能模块拆分处理器
"""

import os
import json
from fastapi import WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from yuntai.core.config import (
    PROJECT_ROOT, SHORTCUTS, CONVERSATION_HISTORY_FILE, TEMP_DIR,
    TTS_OUTPUT_DIR, CONNECTION_CONFIG_FILE
)

from .controller import WebController
from .ws_manager import ConnectionManager

# 导入拆分后的处理器
from .handlers import (
    handle_command, handle_tts_speak, handle_tts_synth, handle_tts_select_model,
    handle_tts_load_models, handle_tts_settings, handle_connect_device,
    handle_disconnect_device, handle_refresh_devices, handle_detect_devices,
    handle_generate_image, handle_generate_video, handle_terminate,
    handle_start_scrcpy, handle_system_check, handle_file_management,
    handle_get_page_data, handle_delete_audio, handle_delete_all_audio, handle_shortcut
)

# 获取web模块所在目录（core的父目录）
WEB_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# TTS音频文件目录（使用config中的定义）
os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)


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

    @app.get("/api/connection_config")
    async def get_connection_config():
        """获取连接配置"""
        try:
            if os.path.exists(CONNECTION_CONFIG_FILE):
                with open(CONNECTION_CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    # 提取IP和端口，与yuntai目录逻辑一致
                    wireless_ip = config.get("wireless_ip", "")
                    wireless_port = config.get("wireless_port", "5555")

                    # 如果wireless_ip包含端口，则分离
                    if ":" in wireless_ip:
                        ip, port = wireless_ip.split(":", 1)
                    else:
                        ip = wireless_ip
                        port = wireless_port

                    return JSONResponse(content={
                        "ip": ip,
                        "port": port,
                        "connection_type": config.get("connection_type", "wireless"),
                        "device_type": config.get("device_type", "android")
                    })
        except Exception as e:
            print(f"读取连接配置失败: {e}")
        return JSONResponse(content={})

    # ==================== 文件上传 ====================

    @app.post("/api/upload")
    async def upload_file(file: UploadFile = File(...)):
        """上传文件"""
        try:
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor()

            # 使用TEMP_DIR下的uploads目录
            upload_dir = os.path.join(TEMP_DIR, "uploads")
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, file.filename)
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
            upload_dir = os.path.join(TEMP_DIR, "uploads")
            file_path = os.path.join(upload_dir, filename)

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

            # 异步预加载TTS，并在加载成功后播放欢迎语音
            controller.preload_tts_async(play_welcome_after_load=True)

            while True:
                data = await websocket.receive_json()
                msg_type = data.get("type")

                # 命令处理
                if msg_type == "command":
                    await handle_command(websocket, data, controller)
                elif msg_type == "terminate":
                    await handle_terminate(websocket, controller)
                elif msg_type == "clear_output":
                    await controller.send_output("", "clear_output")
                elif msg_type == "toggle_theme":
                    controller.is_dark_theme = not controller.is_dark_theme
                    await controller.send_state_update({"is_dark_theme": controller.is_dark_theme})

                # TTS处理
                elif msg_type == "tts_synth":
                    await handle_tts_synth(websocket, data, controller)
                elif msg_type == "tts_select_model":
                    await handle_tts_select_model(websocket, data, controller)
                elif msg_type == "tts_stop":
                    try:
                        controller.task_manager.tts_manager.stop_current_audio_playback()
                    except:
                        pass
                    await controller.send_toast("已停止播放", "info")
                elif msg_type == "tts_load_models":
                    await handle_tts_load_models(websocket, controller)
                elif msg_type == "tts_speak":
                    await handle_tts_speak(websocket, data, controller)
                elif msg_type == "tts_settings":
                    await handle_tts_settings(websocket, data, controller)

                # 设备处理
                elif msg_type == "connect_device":
                    await handle_connect_device(websocket, data, controller)
                elif msg_type == "disconnect_device":
                    await handle_disconnect_device(websocket, controller)
                elif msg_type == "refresh_devices":
                    await handle_refresh_devices(websocket, controller)
                elif msg_type == "detect_devices":
                    await handle_detect_devices(websocket, data, controller)

                # 快捷键和确认
                elif msg_type == "shortcut":
                    await handle_shortcut(websocket, data, controller)
                elif msg_type == "simulate_enter":
                    try:
                        from yuntai.core.agent_executor import AgentExecutor
                        AgentExecutor.user_confirm()
                        await controller.send_output("[用户已确认]\n", "output")
                    except Exception as e:
                        await controller.send_output(f"发送确认信号失败: {e}\n", "output")

                # 页面数据
                elif msg_type == "get_page_data":
                    await handle_get_page_data(websocket, data.get("page"), controller)

                # 音频管理
                elif msg_type == "delete_audio":
                    await handle_delete_audio(websocket, data, controller)
                elif msg_type == "delete_all_audio":
                    await handle_delete_all_audio(websocket, controller)

                # 历史记录
                elif msg_type == "clear_history":
                    controller.clear_history()
                    await controller.send_toast("历史记录已清空", "success")
                    await controller.ws_manager.broadcast({
                        "type": "history_cleared"
                    })

                # 媒体生成
                elif msg_type == "generate_image":
                    await handle_generate_image(websocket, data, controller)
                elif msg_type == "generate_video":
                    await handle_generate_video(websocket, data, controller)

                # 系统功能
                elif msg_type == "start_scrcpy":
                    await handle_start_scrcpy(websocket, data, controller)
                elif msg_type == "system_check":
                    await handle_system_check(websocket, controller)
                elif msg_type == "get_file_management":
                    await handle_file_management(websocket, controller)

        except WebSocketDisconnect:
            await ws_manager.disconnect(websocket)
        except Exception as e:
            print(f"WebSocket错误: {e}")
            import traceback
            traceback.print_exc()
            await ws_manager.disconnect(websocket)
