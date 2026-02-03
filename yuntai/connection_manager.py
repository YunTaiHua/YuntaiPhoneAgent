#!/usr/bin/env python3
"""
连接管理模块 - 支持USB和无线调试两种方式
仅支持Android (ADB) 设备
"""
import subprocess
import json
import os
from typing import List, Tuple, Dict, Optional

from yuntai.config import (
    CONNECTION_CONFIG_FILE,
    DEFAULT_DEVICE_TYPE,
    DEVICE_TYPE_HARMONY
)


class ConnectionManager:
    def __init__(self, device_type: str = DEFAULT_DEVICE_TYPE):
        """
        初始化连接管理器

        Args:
            device_type: 设备类型 (android)
        """
        self.device_type = device_type

    def set_device_type(self, device_type: str):
        """设置设备类型"""
        self.device_type = device_type

    def load_connection_config(self) -> Dict[str, str]:
        """加载连接配置"""
        default_config = {
            "connection_type": "wireless",
            "wireless_ip": "",
            "wireless_port": "5555",
            "usb_device_id": "",
            "device_type": DEFAULT_DEVICE_TYPE,
            "device_type_display": "Android (ADB)"
        }

        try:
            if os.path.exists(CONNECTION_CONFIG_FILE):
                with open(CONNECTION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
        except Exception as e:
            print(f"⚠️  读取连接配置失败: {e}")

        return default_config

    def save_connection_config(self, config: Dict[str, str]):
        """保存连接配置"""
        try:
            with open(CONNECTION_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存连接配置失败: {e}")

    def get_available_devices(self) -> List[str]:
        """获取可用的设备列表（支持多平台）"""
        if self.device_type == DEVICE_TYPE_HARMONY:
            return self._get_harmony_devices()
        return self._get_android_devices()

    def _get_android_devices(self) -> List[str]:
        """获取Android设备列表 (ADB)"""
        devices = []
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="ignore"
            )

            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:
                if line.strip() and "device" in line:
                    device_id = line.split("\t")[0].strip()
                    devices.append(device_id)

            return devices
        except Exception as e:
            print(f"⚠️  获取Android设备列表失败: {e}")
            return []

    def _get_harmony_devices(self) -> List[str]:
        """获取HarmonyOS设备列表 (HDC)"""
        devices = []
        try:
            result = subprocess.run(
                ["hdc", "list", "targets"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="ignore"
            )

            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    devices.append(line.strip())

            return devices
        except Exception as e:
            print(f"⚠️  获取HarmonyOS设备列表失败: {e}")
            return []

    def connect_to_device(self, config: Dict[str, str]) -> Tuple[bool, str, str]:
        """
        连接到设备（支持Android和HarmonyOS）

        Returns: (是否成功, 设备ID, 消息)
        """
        device_type = config.get("device_type", self.device_type)
        connection_type = config.get("connection_type", "wireless")
        device_id = config.get("usb_device_id", "") or config.get("wireless_ip", "")

        if not device_id:
            return False, "", "未配置设备ID"

        if device_type == DEVICE_TYPE_HARMONY:
            return self._connect_harmony_device(device_id, connection_type, config)
        else:
            return self._connect_android_device(device_id, connection_type, config)

    def _connect_android_device(self, device_id: str, connection_type: str, config: Dict[str, str]) -> Tuple[bool, str, str]:
        """连接Android设备 (ADB)"""
        if connection_type == "usb":
            devices = self._get_android_devices()
            if device_id in devices:
                return True, device_id, f"USB设备已连接: {device_id}"
            else:
                try:
                    result = subprocess.run(
                        ["adb", "connect", device_id],
                        capture_output=True,
                        text=True,
                        timeout=15,
                        encoding="utf-8",
                        errors="ignore"
                    )
                    if result.returncode == 0:
                        return True, device_id, f"已连接到USB设备: {device_id}"
                    else:
                        return False, "", f"无法连接到USB设备 {device_id}: {result.stderr}"
                except Exception as e:
                    return False, "", f"USB连接失败: {str(e)}"
        else:
            wireless_ip = config.get("wireless_ip", "")
            wireless_port = config.get("wireless_port", "5555")
            device_addr = f"{wireless_ip}:{wireless_port}"

            try:
                result = subprocess.run(
                    ["adb", "connect", device_addr],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    encoding="utf-8",
                    errors="ignore"
                )
                stdout = result.stdout.strip()
                if result.returncode == 0 and "connected to" in stdout.lower():
                    return True, device_addr, f"已连接到无线设备: {device_addr}"
                elif "already connected" in stdout.lower():
                    return True, device_addr, f"✅ 无线设备已连接: {device_addr}"
                else:
                    return False, "", f"无线连接失败: {stdout}"
            except Exception as e:
                return False, "", f"连接失败: {str(e)}"

    def _connect_harmony_device(self, device_id: str, connection_type: str, config: Dict[str, str]) -> Tuple[bool, str, str]:
        """连接HarmonyOS设备 (HDC)"""
        if connection_type == "usb":
            devices = self._get_harmony_devices()
            if device_id in devices:
                return True, device_id, f"HDC USB设备已连接: {device_id}"
            else:
                return False, "", f"未找到USB设备: {device_id}"
        else:
            wireless_ip = config.get("wireless_ip", "")
            wireless_port = config.get("wireless_port", "5555")
            if ":" in device_id:
                address = device_id
            else:
                address = f"{device_id}:{wireless_port}"

            try:
                result = subprocess.run(
                    ["hdc", "tconn", address],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    encoding="utf-8",
                    errors="ignore"
                )
                stdout = result.stdout.strip()
                if result.returncode == 0:
                    return True, address, f"已连接到HarmonyOS设备: {address}"
                else:
                    return False, "", f"HDC连接失败: {stdout}"
            except Exception as e:
                return False, "", f"连接失败: {str(e)}"

    def adb_connect_windows(self, device_addr: str) -> tuple[bool, str]:
        """Windows ADB连接（兼容旧代码）"""
        try:
            result = subprocess.run(
                ["adb", "connect", device_addr],
                capture_output=True,
                text=True,
                timeout=15,
                encoding="utf-8",
                errors="ignore"
            )
            stdout = result.stdout.strip()
            if result.returncode == 0 and "connected to" in stdout.lower():
                return True, f"成功连接到 {device_addr}"
            elif "already connected" in stdout.lower():
                return True, f"{device_addr} 已连接"
            else:
                return False, f"连接失败：{stdout}"
        except Exception as e:
            return False, f"未知错误：{str(e)}"
