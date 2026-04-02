"""
routes.py - FastAPI路由定义
============================

重构版本 - 按功能模块拆分处理器。

负责定义所有HTTP和WebSocket路由，将请求分发到对应的处理器。

主要功能:
    - HTTP路由: 主页、状态查询、文件上传、历史记录等
    - WebSocket路由: 实时通信、命令执行、TTS处理等

路由分类:
    - 页面路由: / (主页)
    - 状态路由: /api/state, /api/version
    - TTS路由: /api/tts/models, /api/tts/audio, /api/tts/audio_history
    - 媒体路由: /api/images, /api/videos
    - 设备路由: /api/devices, /api/connection_config
    - 历史路由: /api/history
    - 文件路由: /api/upload
    - WebSocket: /ws

安全性:
    - 文件路径验证：防止路径遍历攻击
    - 文件类型验证：只允许特定类型的文件上传
    - 文件大小限制：防止大文件攻击

使用示例:
    >>> from fastapi import FastAPI
    >>> app = FastAPI()
    >>> setup_routes(app, controller, ws_manager)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from fastapi import WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi import FastAPI

logger = logging.getLogger(__name__)

from yuntai.core.config import (
    PROJECT_ROOT, SHORTCUTS, CONVERSATION_HISTORY_FILE, TEMP_DIR,
    TTS_OUTPUT_DIR, CONNECTION_CONFIG_FILE, APP_VERSION, MAX_FILE_SIZE
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


def _validate_filename(filename: str) -> str:
    """
    验证文件名安全性
    
    检查文件名是否包含路径遍历攻击字符，防止恶意访问系统文件。
    
    Args:
        filename: 待验证的文件名
    
    Returns:
        str: 验证后的安全文件名
    
    Raises:
        HTTPException: 当文件名包含危险字符时抛出 400 错误
    
    使用示例：
        >>> safe_name = _validate_filename("audio.wav")
        >>> # 如果文件名包含 ".." 或 "/" 会抛出异常
    """
    filename = unquote(filename)
    
    if not filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    
    if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
        logger.warning("检测到危险的文件名: %s", filename)
        raise HTTPException(status_code=400, detail="无效的文件名")
    
    if any(sep in filename for sep in ["/", "\\"]):
        logger.warning("文件名包含路径分隔符: %s", filename)
        raise HTTPException(status_code=400, detail="文件名不能包含路径")
    
    return filename


def _validate_file_path(base_dir: Path, filename: str) -> Path:
    """
    验证文件路径安全性
    
    确保文件路径在指定的基础目录内，防止路径遍历攻击。
    
    Args:
        base_dir: 基础目录路径
        filename: 文件名
    
    Returns:
        Path: 验证后的安全文件路径
    
    Raises:
        HTTPException: 当路径不在基础目录内时抛出 403 错误
    
    使用示例：
        >>> filepath = _validate_file_path(Path("/data/audio"), "test.wav")
    """
    safe_filename = _validate_filename(filename)
    filepath = (base_dir / safe_filename).resolve()
    base_dir_resolved = base_dir.resolve()
    
    if not str(filepath).startswith(str(base_dir_resolved)):
        logger.warning("路径遍历攻击检测: %s", filepath)
        raise HTTPException(status_code=403, detail="禁止访问该路径")
    
    return filepath


def setup_routes(
    app: FastAPI,
    controller: WebController,
    ws_manager: ConnectionManager
) -> None:
    """
    设置所有路由
    
    为FastAPI应用注册所有HTTP路由和WebSocket路由。
    
    Args:
        app: FastAPI应用实例
        controller: Web控制器实例
        ws_manager: WebSocket连接管理器实例
    """
    # 静态文件目录
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
        """
        获取音频文件
        
        Args:
            filename: 音频文件名
        
        Returns:
            FileResponse: 音频文件响应
        
        Raises:
            HTTPException: 文件不存在或路径不安全时抛出异常
        """
        try:
            filepath = _validate_file_path(Path(TTS_OUTPUT_DIR), filename)
            if not filepath.exists():
                raise HTTPException(status_code=404, detail="音频文件不存在")
            return FileResponse(str(filepath), media_type="audio/wav")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("获取音频文件失败: %s", str(e))
            raise HTTPException(status_code=500, detail="服务器内部错误")

    @app.get("/api/images/{filename}")
    async def get_image_file(filename: str) -> FileResponse:
        """
        获取图像文件
        
        Args:
            filename: 图像文件名
        
        Returns:
            FileResponse: 图像文件响应
        
        Raises:
            HTTPException: 文件不存在或路径不安全时抛出异常
        """
        try:
            images_dir = Path(TEMP_DIR) / "images"
            filepath = _validate_file_path(images_dir, filename)
            if not filepath.exists():
                raise HTTPException(status_code=404, detail="图像文件不存在")
            return FileResponse(str(filepath), media_type="image/png")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("获取图像文件失败: %s", str(e))
            raise HTTPException(status_code=500, detail="服务器内部错误")

    @app.get("/api/videos/{filename}")
    async def get_video_file(filename: str) -> FileResponse:
        """
        获取视频文件
        
        Args:
            filename: 视频文件名
        
        Returns:
            FileResponse: 视频文件响应
        
        Raises:
            HTTPException: 文件不存在或路径不安全时抛出异常
        """
        try:
            videos_dir = Path(TEMP_DIR) / "videos"
            filepath = _validate_file_path(videos_dir, filename)
            if not filepath.exists():
                raise HTTPException(status_code=404, detail="视频文件不存在")
            return FileResponse(str(filepath), media_type="video/mp4")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("获取视频文件失败: %s", str(e))
            raise HTTPException(status_code=500, detail="服务器内部错误")

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
            logger.warning("读取连接配置失败: %s", str(e))
        return JSONResponse(content={})

    @app.post("/api/upload")
    async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
        """
        上传文件
        
        支持的文件类型包括图像、视频、音频和文档文件。
        文件大小限制由 MAX_FILE_SIZE 配置决定。
        
        Args:
            file: 上传的文件对象
        
        Returns:
            JSONResponse: 包含上传结果的 JSON 响应
        
        Raises:
            HTTPException: 文件类型不支持或大小超限时抛出异常
        """
        try:
            from yuntai.processors.multimodal_processor import MultimodalProcessor
            processor = MultimodalProcessor()
            
            filename = file.filename or "unknown"
            safe_filename = _validate_filename(filename)
            
            content = await file.read()
            file_size = len(content)
            
            if file_size > MAX_FILE_SIZE:
                logger.warning("上传文件过大: %s (%.2fMB > %.2fMB)", 
                             safe_filename, file_size / 1024 / 1024, MAX_FILE_SIZE / 1024 / 1024)
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"文件大小超过限制 ({MAX_FILE_SIZE // 1024 // 1024}MB)"}
                )
            
            upload_dir = Path(TEMP_DIR) / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = upload_dir / safe_filename
            file_path.write_bytes(content)
            
            if not processor.is_file_supported(str(file_path)):
                file_path.unlink()
                logger.warning("不支持的文件类型: %s", safe_filename)
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"不支持的文件类型: {safe_filename}"}
                )
            
            controller.attached_files.append(str(file_path))
            logger.info("文件上传成功: %s", safe_filename)
            
            return JSONResponse(content={
                "success": True,
                "filename": safe_filename,
                "attached_files": [Path(f).name for f in controller.attached_files]
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("文件上传失败: %s", str(e))
            return JSONResponse(status_code=500, content={"success": False, "message": "服务器内部错误"})

    @app.delete("/api/upload/{filename}")
    async def remove_file(filename: str) -> JSONResponse:
        """
        移除上传的文件
        
        Args:
            filename: 要移除的文件名
        
        Returns:
            JSONResponse: 包含操作结果的 JSON 响应
        """
        try:
            upload_dir = Path(TEMP_DIR) / "uploads"
            file_path = _validate_file_path(upload_dir, filename)
            
            if str(file_path) in controller.attached_files:
                controller.attached_files.remove(str(file_path))
            
            if file_path.exists():
                file_path.unlink()
                logger.info("文件已删除: %s", filename)
            
            return JSONResponse(content={
                "success": True,
                "attached_files": [Path(f).name for f in controller.attached_files]
            })
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("删除文件失败: %s", str(e))
            return JSONResponse(status_code=500, content={"success": False, "message": "服务器内部错误"})

    @app.delete("/api/upload")
    async def clear_files() -> JSONResponse:
        """清空所有上传的文件"""
        try:
            controller.attached_files.clear()
            logger.info("已清空所有上传文件")
            return JSONResponse(content={"success": True, "attached_files": []})
        except Exception as e:
            logger.exception("清空文件列表失败: %s", str(e))
            return JSONResponse(status_code=500, content={"success": False, "message": "服务器内部错误"})

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
                        logger.debug("TTS管理器不可用: %s", str(e))
                    except Exception as e:
                        logger.warning("停止TTS播放失败: %s", str(e))
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
            logger.info("WebSocket 连接正常断开")
            await ws_manager.disconnect(websocket)
        except Exception as e:
            logger.exception("WebSocket 错误: %s", str(e))
            await ws_manager.disconnect(websocket)
