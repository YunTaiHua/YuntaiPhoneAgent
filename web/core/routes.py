"""
routes.py - FastAPI路由定义
重构版本 - 按功能模块拆分处理器
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Coroutine

from fastapi import WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi import FastAPI

logger = logging.getLogger(__name__)

from yuntai.core.config import (
    PROJECT_ROOT, SHORTCUTS, CONVERSATION_HISTORY_FILE, TEMP_DIR,
    TTS_OUTPUT_DIR, CONNECTION_CONFIG_FILE, APP_VERSION
)

from .controller import WebController
from .ws_manager import ConnectionManager

from .handlers import (
    handle_command, handle_tts_speak, handle_tts_synth, handle_tts_select_model,
    handle_tts_load_models, handle_tts_settings, handle_connect_device,
    handle_disconnect_device, handle_refresh_devices, handle_detect_devices,
    handle_generate_image, handle_generate_video, handle_terminate,
    handle_start_scrcpy, handle_system_check, handle_file_management,
    handle_get_page_data, handle_delete_audio, handle_delete_all_audio, handle_shortcut
)

WEB_DIR = Path(__file__).resolve().parent.parent

Path(TTS_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


def setup_routes(
    app: FastAPI,
    controller: WebController,
    ws_manager: ConnectionManager
) -> None:
    """设置所有路由"""

    static_dir = WEB_DIR / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        """返回主页面"""
        html_file = WEB_DIR / "index.html"
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
        return HTMLResponse(content=f"<h1>请创建 {html_file} 文件</h1>")

    @app.get("/api/state")
    async def get_state() -> JSONResponse:
        """获取当前状态"""
        return JSONResponse(content=controller.get_state())

    @app.get("/api/tts/models")
    async def get_tts_models() -> JSONResponse:
        """获取TTS模型列表"""
        return JSONResponse(content=controller.get_tts_models())

    @app.get("/api/tts/audio/{filename}")
    async def get_audio_file(filename: str) -> FileResponse:
        """获取音频文件"""
        from urllib.parse import unquote
        filename = unquote(filename)
        filepath = Path(TTS_OUTPUT_DIR) / filename
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="音频文件不存在")
        return FileResponse(str(filepath), media_type="audio/wav")

    @app.get("/api/images/{filename}")
    async def get_image_file(filename: str) -> FileResponse:
        """获取图像文件"""
        from urllib.parse import unquote
        filename = unquote(filename)
        possible_paths = [
            Path(TEMP_DIR) / "images" / filename,
        ]
        for filepath in possible_paths:
            if filepath.exists():
                return FileResponse(str(filepath), media_type="image/png")
        raise HTTPException(status_code=404, detail="图像文件不存在")

    @app.get("/api/videos/{filename}")
    async def get_video_file(filename: str) -> FileResponse:
        """获取视频文件"""
        from urllib.parse import unquote
        filename = unquote(filename)
        possible_paths = [
            Path(TEMP_DIR) / "videos" / filename,
        ]
        for filepath in possible_paths:
            if filepath.exists():
                return FileResponse(str(filepath), media_type="video/mp4")
        raise HTTPException(status_code=404, detail="视频文件不存在")

    @app.get("/api/tts/audio_history")
    async def get_audio_history() -> JSONResponse:
        """获取历史音频列表"""
        return JSONResponse(content=controller.get_audio_history())

    @app.get("/api/shortcuts")
    async def get_shortcuts() -> JSONResponse:
        """获取快捷键配置"""
        return JSONResponse(content=SHORTCUTS)

    @app.get("/api/version")
    async def get_version() -> JSONResponse:
        """获取应用版本号"""
        return JSONResponse(content={"version": APP_VERSION})

    @app.get("/api/history")
    async def get_history() -> JSONResponse:
        """获取历史记录"""
        return JSONResponse(content=controller.get_history())

    @app.delete("/api/history")
    async def clear_history() -> JSONResponse:
        """清空历史记录"""
        return JSONResponse(content=controller.clear_history())

    @app.get("/api/devices")
    async def get_devices() -> JSONResponse:
        """获取设备列表"""
        return JSONResponse(content=controller.get_available_devices())

    @app.get("/api/connection_config")
    async def get_connection_config() -> JSONResponse:
        """获取连接配置"""
        try:
            config_file = Path(CONNECTION_CONFIG_FILE)
            if config_file.exists():
                config = json.loads(config_file.read_text(encoding="utf-8"))
                wireless_ip = config.get("wireless_ip", "")
                wireless_port = config.get("wireless_port", "5555")

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

    @app.post("/api/upload")
    async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
        """上传文件"""
        try:
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor()

            upload_dir = Path(TEMP_DIR) / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_path = upload_dir / (file.filename or "unknown")
            content = await file.read()
            file_path.write_bytes(content)

            if not processor.is_file_supported(str(file_path)):
                file_path.unlink()
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"不支持的文件类型: {file.filename}"}
                )

            controller.attached_files.append(str(file_path))

            return JSONResponse(content={
                "success": True,
                "filename": file.filename,
                "attached_files": [Path(f).name for f in controller.attached_files]
            })
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

    @app.delete("/api/upload/{filename}")
    async def remove_file(filename: str) -> JSONResponse:
        """移除上传的文件"""
        try:
            upload_dir = Path(TEMP_DIR) / "uploads"
            file_path = upload_dir / filename

            if str(file_path) in controller.attached_files:
                controller.attached_files.remove(str(file_path))

            if file_path.exists():
                file_path.unlink()

            return JSONResponse(content={
                "success": True,
                "attached_files": [Path(f).name for f in controller.attached_files]
            })
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

    @app.delete("/api/upload")
    async def clear_files() -> JSONResponse:
        """清空所有上传的文件"""
        try:
            controller.attached_files.clear()
            return JSONResponse(content={"success": True, "attached_files": []})
        except Exception as e:
            return JSONResponse(status_code=500, content={"success": False, "message": str(e)})

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        """WebSocket连接处理"""
        await ws_manager.connect(websocket)

        try:
            is_first_connection = ws_manager.is_first_connection()

            await controller.send_personal_message({
                "type": "init",
                "data": controller.get_state(),
                "tts_models": controller.get_tts_models(),
                "is_first_connection": is_first_connection
            }, websocket)

            controller.preload_tts_async(play_welcome_after_load=True)

            while True:
                data: dict[str, Any] = await websocket.receive_json()
                msg_type = data.get("type")

                if msg_type == "command":
                    await handle_command(websocket, data, controller)
                elif msg_type == "terminate":
                    await handle_terminate(websocket, controller)
                elif msg_type == "clear_output":
                    await controller.send_output("", "clear_output")
                elif msg_type == "toggle_theme":
                    controller.is_dark_theme = not controller.is_dark_theme
                    await controller.send_state_update({"is_dark_theme": controller.is_dark_theme})

                elif msg_type == "tts_synth":
                    await handle_tts_synth(websocket, data, controller)
                elif msg_type == "tts_select_model":
                    await handle_tts_select_model(websocket, data, controller)
                elif msg_type == "tts_stop":
                    try:
                        controller.task_manager.tts_manager.stop_current_audio_playback()
                    except AttributeError as e:
                        logger.debug(f"TTS管理器不可用: {e}")
                    except Exception as e:
                        logger.warning(f"停止TTS播放失败: {e}")
                    await controller.send_toast("已停止播放", "info")
                elif msg_type == "tts_load_models":
                    await handle_tts_load_models(websocket, controller)
                elif msg_type == "tts_speak":
                    await handle_tts_speak(websocket, data, controller)
                elif msg_type == "tts_settings":
                    await handle_tts_settings(websocket, data, controller)

                elif msg_type == "connect_device":
                    await handle_connect_device(websocket, data, controller)
                elif msg_type == "disconnect_device":
                    await handle_disconnect_device(websocket, controller)
                elif msg_type == "refresh_devices":
                    await handle_refresh_devices(websocket, controller)
                elif msg_type == "detect_devices":
                    await handle_detect_devices(websocket, data, controller)

                elif msg_type == "shortcut":
                    await handle_shortcut(websocket, data, controller)
                elif msg_type == "simulate_enter":
                    try:
                        from yuntai.core.agent_executor import AgentExecutor
                        AgentExecutor.user_confirm()
                        await controller.send_output("[用户已确认]\n", "output")
                    except Exception as e:
                        await controller.send_output(f"发送确认信号失败: {e}\n", "output")

                elif msg_type == "get_page_data":
                    await handle_get_page_data(websocket, data.get("page"), controller)

                elif msg_type == "delete_audio":
                    await handle_delete_audio(websocket, data, controller)
                elif msg_type == "delete_all_audio":
                    await handle_delete_all_audio(websocket, controller)

                elif msg_type == "clear_history":
                    controller.clear_history()
                    await controller.send_toast("历史记录已清空", "success")
                    await controller.ws_manager.broadcast({
                        "type": "history_cleared"
                    })

                elif msg_type == "generate_image":
                    await handle_generate_image(websocket, data, controller)
                elif msg_type == "generate_video":
                    await handle_generate_video(websocket, data, controller)

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
