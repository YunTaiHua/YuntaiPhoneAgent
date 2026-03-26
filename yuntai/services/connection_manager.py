#!/usr/bin/env python3
"""
连接管理模块

支持USB和无线调试两种方式，兼容 Android (ADB) 和 HarmonyOS (HDC) 设备。

Example:
    >>> manager = ConnectionManager()
    >>> config = manager.load_connection_config()
    >>> success, device_id, message = manager.connect_to_device(config)
"""

import subprocess
import json
from pathlib import Path

from yuntai.core.config import (
    CONNECTION_CONFIG_FILE,
    DEFAULT_DEVICE_TYPE,
    DEVICE_TYPE_HARMONY,
)


class ConnectionManager:
    """
    连接管理器
    
    负责设备连接管理，支持 USB 和无线两种连接方式，
    兼容 Android (ADB) 和 HarmonyOS (HDC) 设备。
    
    Attributes:
        device_type: 设备类型 (android/harmony)
    
    Example:
        >>> manager = ConnectionManager()
        >>> devices = manager.get_available_devices()
        >>> success, device_id, msg = manager.connect_to_device(config)
    """
    
    def __init__(self, device_type: str = DEFAULT_DEVICE_TYPE) -> None:
        """
        初始化连接管理器
        
        Args:
            device_type: 设备类型，可选值为 'android' 或 'harmony'
        """
        self.device_type: str = device_type

    def set_device_type(self, device_type: str) -> None:
        """
        设置设备类型
        
        Args:
            device_type: 设备类型 (android/harmony)
        """
        self.device_type = device_type

    def load_connection_config(self) -> dict[str, str]:
        """
        加载连接配置
        
        从配置文件加载连接配置，如果文件不存在则返回默认配置。
        
        Returns:
            连接配置字典，包含以下字段:
            - connection_type: 连接类型 (usb/wireless)
            - wireless_ip: 无线连接 IP 地址
            - wireless_port: 无线连接端口
            - usb_device_id: USB 设备 ID
            - device_type: 设备类型
            - device_type_display: 设备类型显示名称
        """
        default_config: dict[str, str] = {
            "connection_type": "wireless",
            "wireless_ip": "",
            "wireless_port": "5555",
            "usb_device_id": "",
            "device_type": DEFAULT_DEVICE_TYPE,
            "device_type_display": "Android (ADB)"
        }

        try:
            config_file = Path(CONNECTION_CONFIG_FILE)
            if config_file.exists():
                config = json.loads(config_file.read_text(encoding='utf-8'))
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except Exception as e:
            print(f"⚠️  读取连接配置失败: {e}")

        return default_config

    def save_connection_config(self, config: dict[str, str]) -> None:
        """
        保存连接配置
        
        Args:
            config: 连接配置字典
        """
        try:
            config_file = Path(CONNECTION_CONFIG_FILE)
            config_file.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"⚠️  保存连接配置失败: {e}")

    def get_available_devices(self) -> list[str]:
        """
        获取可用的设备列表
        
        根据当前设备类型，返回可用的设备 ID 列表。
        
        Returns:
            设备 ID 列表
        """
        if self.device_type == DEVICE_TYPE_HARMONY:
            return self._get_harmony_devices()
        return self._get_android_devices()

    def _get_android_devices(self) -> list[str]:
        """
        获取 Android 设备列表 (ADB)
        
        Returns:
            Android 设备 ID 列表
        """
        devices: list[str] = []
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

    def _get_harmony_devices(self) -> list[str]:
        """
        获取 HarmonyOS 设备列表 (HDC)
        
        Returns:
            HarmonyOS 设备 ID 列表
        """
        devices: list[str] = []
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

    def connect_to_device(self, config: dict[str, str]) -> tuple[bool, str, str]:
        """
        连接到设备
        
        根据配置连接到 Android 或 HarmonyOS 设备。
        
        Args:
            config: 连接配置字典
        
        Returns:
            元组 (是否成功, 设备ID, 消息)
        
        Example:
            >>> success, device_id, msg = manager.connect_to_device({
            ...     "connection_type": "wireless",
            ...     "wireless_ip": "192.168.1.100",
            ...     "wireless_port": "5555"
            ... })
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

    def _connect_android_device(
        self,
        device_id: str,
        connection_type: str,
        config: dict[str, str]
    ) -> tuple[bool, str, str]:
        """
        连接 Android 设备 (ADB)
        
        Args:
            device_id: 设备 ID
            connection_type: 连接类型 (usb/wireless)
            config: 连接配置
        
        Returns:
            元组 (是否成功, 设备ID, 消息)
        """
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
            if ":" in wireless_ip:
                device_addr = wireless_ip
            else:
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

    def _connect_harmony_device(
        self,
        device_id: str,
        connection_type: str,
        config: dict[str, str]
    ) -> tuple[bool, str, str]:
        """
        连接 HarmonyOS 设备 (HDC)
        
        Args:
            device_id: 设备 ID
            connection_type: 连接类型 (usb/wireless)
            config: 连接配置
        
        Returns:
            元组 (是否成功, 设备ID, 消息)
        """
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
        """
        Windows ADB 连接（兼容旧代码）
        
        Args:
            device_addr: 设备地址 (IP:端口 或 设备ID)
        
        Returns:
            元组 (是否成功, 消息)
        """
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
