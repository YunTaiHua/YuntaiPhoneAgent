"""
device_handler.py - 设备管理处理
"""

import asyncio
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..controller import WebController


async def handle_connect_device(websocket, data: dict, controller: "WebController"):
    """处理设备连接"""
    device_type = data.get("device_type", "android")
    connection_type = data.get("connection_type", "wireless")

    def connect_thread():
        try:
            # 构建配置字典，与yuntai目录逻辑一致
            config = {
                "device_type": device_type,
                "connection_type": connection_type,
                "wireless_ip": "",
                "wireless_port": "5555",
                "usb_device_id": "",
                "device_type_display": "Android (ADB)" if device_type == "android" else "HarmonyOS (HDC)"
            }

            if connection_type == "usb":
                device_id = data.get("device_id", "")
                config["usb_device_id"] = device_id
            else:
                ip = data.get("ip", "")
                port = data.get("port", "5555")
                # 与yuntai目录逻辑一致：wireless_ip不包含端口，端口单独存储
                config["wireless_ip"] = ip
                config["wireless_port"] = port

            # 使用TaskManager的connect_device方法
            success, device_id, message = controller.task_manager.connect_device(config)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if success:
                    loop.run_until_complete(controller.send_toast(f"已连接: {device_id}", "success"))
                    loop.run_until_complete(controller.send_state_update({
                        "is_connected": True,
                        "device_id": device_id,
                        "device_type": device_type
                    }))
                else:
                    loop.run_until_complete(controller.send_toast(f"连接失败: {message}", "error"))
            finally:
                loop.close()
        except Exception as e:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(controller.send_toast(f"连接错误: {str(e)}", "error"))
            finally:
                loop.close()

    threading.Thread(target=connect_thread, daemon=True).start()


async def handle_disconnect_device(websocket, controller: "WebController"):
    """处理设备断开"""
    try:
        controller.task_manager.disconnect_device()
        await controller.send_output("✅ 设备已断开\n", "output")
        await controller.send_toast("设备已断开", "info")
        await controller.send_state_update({"is_connected": False, "device_id": ""})
    except Exception as e:
        await controller.send_toast(f"断开失败: {str(e)}", "error")


async def handle_refresh_devices(websocket, controller: "WebController"):
    """处理刷新设备列表"""
    devices = controller.get_available_devices()
    await controller.send_personal_message({
        "type": "devices_update",
        "devices": devices
    }, websocket)
    await controller.send_toast(f"找到 {len(devices)} 个设备", "info")


async def handle_detect_devices(websocket, data: dict, controller: "WebController"):
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
