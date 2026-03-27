#!/usr/bin/env python3
"""
连接管理模块

支持USB和无线调试两种方式，兼容 Android (ADB) 和 HarmonyOS (HDC) 设备。
提供设备检测、连接管理和配置持久化功能。

Example:
    >>> manager = ConnectionManager()
    >>> config = manager.load_connection_config()
    >>> success, device_id, message = manager.connect_to_device(config)
"""

from __future__ import annotations

import subprocess
import json
import re
import shlex
from pathlib import Path
from typing import Any, Final

from yuntai.core.config import (
    CONNECTION_CONFIG_FILE,
    DEFAULT_DEVICE_TYPE,
    DEVICE_TYPE_HARMONY,
    DEVICE_DETECT_TIMEOUT,
    DEVICE_CONNECT_TIMEOUT,
    MAX_DEVICE_ID_LENGTH,
    DEFAULT_WIRELESS_PORT,
)


def sanitize_device_id(device_id: str) -> str:
    """
    清理和验证设备ID
    
    移除设备ID中的非法字符，防止命令注入攻击。
    
    Args:
        device_id: 原始设备ID字符串
    
    Returns:
        清理后的安全设备ID
    
    Raises:
        ValueError: 如果设备ID为空或包含非法字符
    """
    if not device_id or not device_id.strip():
        raise ValueError("设备ID不能为空")
    
    device_id = device_id.strip()
    
    if len(device_id) > MAX_DEVICE_ID_LENGTH:
        raise ValueError(f"设备ID长度超过限制 ({MAX_DEVICE_ID_LENGTH})")
    
    safe_pattern = re.compile(r'^[a-zA-Z0-9.:_-]+$')
    if not safe_pattern.match(device_id):
        raise ValueError(f"设备ID包含非法字符: {device_id}")
    
    return device_id


def sanitize_ip_address(ip: str) -> str:
    """
    清理和验证IP地址
    
    验证IP地址格式，防止命令注入攻击。
    
    Args:
        ip: 原始IP地址字符串
    
    Returns:
        清理后的安全IP地址
    
    Raises:
        ValueError: 如果IP地址格式无效
    """
    if not ip or not ip.strip():
        raise ValueError("IP地址不能为空")
    
    ip = ip.strip()
    
    ip_pattern = re.compile(
        r'^(\d{1,3}\.){3}\d{1,3}(:\d{1,5})?$|'
        r'^\[?[a-zA-Z0-9:]+\]?(:\d{1,5})?$'
    )
    if not ip_pattern.match(ip):
        raise ValueError(f"IP地址格式无效: {ip}")
    
    return ip


def build_safe_command(base_cmd: list[str], *args: str) -> list[str]:
    """
    构建安全的命令列表
    
    确保所有命令参数都经过验证，防止命令注入。
    
    Args:
        base_cmd: 基础命令列表
        *args: 命令参数
    
    Returns:
        安全的命令列表
    """
    safe_cmd = list(base_cmd)
    for arg in args:
        if arg:
            safe_cmd.append(str(arg))
    return safe_cmd


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
            config_file.write_text(
                json.dumps(config, ensure_ascii=False, indent=2), 
                encoding='utf-8'
            )
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
            cmd = build_safe_command(["adb", "devices"])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DEVICE_DETECT_TIMEOUT,
                encoding="utf-8",
                errors="ignore"
            )

            lines = result.stdout.strip().split("\n")
            for line in lines[1:]:
                if line.strip() and "device" in line:
                    parts = line.split("\t")
                    if len(parts) >= 1:
                        device_id = parts[0].strip()
                        try:
                            safe_id = sanitize_device_id(device_id)
                            devices.append(safe_id)
                        except ValueError:
                            print(f"⚠️  跳过无效设备ID: {device_id}")

            return devices
        except subprocess.TimeoutExpired:
            print("⚠️  获取Android设备列表超时")
            return []
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
            cmd = build_safe_command(["hdc", "list", "targets"])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DEVICE_DETECT_TIMEOUT,
                encoding="utf-8",
                errors="ignore"
            )

            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    try:
                        safe_id = sanitize_device_id(line.strip())
                        devices.append(safe_id)
                    except ValueError:
                        print(f"⚠️  跳过无效设备ID: {line.strip()}")

            return devices
        except subprocess.TimeoutExpired:
            print("⚠️  获取HarmonyOS设备列表超时")
            return []
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

        try:
            safe_device_id = sanitize_device_id(device_id)
        except ValueError as e:
            return False, "", f"设备ID无效: {str(e)}"

        if device_type == DEVICE_TYPE_HARMONY:
            return self._connect_harmony_device(safe_device_id, connection_type, config)
        else:
            return self._connect_android_device(safe_device_id, connection_type, config)

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
                return False, "", f"未找到USB设备: {device_id}"
        else:
            wireless_ip = config.get("wireless_ip", "")
            wireless_port = config.get("wireless_port", "5555")
            
            try:
                safe_ip = sanitize_ip_address(wireless_ip)
            except ValueError as e:
                return False, "", f"IP地址无效: {str(e)}"
            
            if ":" in safe_ip:
                device_addr = safe_ip
            else:
                safe_port = str(int(wireless_port))
                device_addr = f"{safe_ip}:{safe_port}"

            try:
                cmd = build_safe_command(["adb", "connect", device_addr])
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=DEVICE_CONNECT_TIMEOUT,
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
            except subprocess.TimeoutExpired:
                return False, "", "连接超时"
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
            
            try:
                safe_ip = sanitize_ip_address(wireless_ip)
            except ValueError as e:
                return False, "", f"IP地址无效: {str(e)}"
            
            if ":" in device_id:
                address = device_id
            else:
                safe_port = str(int(wireless_port))
                address = f"{safe_ip}:{safe_port}"

            try:
                cmd = build_safe_command(["hdc", "tconn", address])
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=DEVICE_CONNECT_TIMEOUT,
                    encoding="utf-8",
                    errors="ignore"
                )
                stdout = result.stdout.strip()
                if result.returncode == 0:
                    return True, address, f"已连接到HarmonyOS设备: {address}"
                else:
                    return False, "", f"HDC连接失败: {stdout}"
            except subprocess.TimeoutExpired:
                return False, "", "连接超时"
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
            safe_addr = sanitize_device_id(device_addr)
        except ValueError as e:
            return False, f"设备地址无效: {str(e)}"
        
        try:
            cmd = build_safe_command(["adb", "connect", safe_addr])
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DEVICE_CONNECT_TIMEOUT,
                encoding="utf-8",
                errors="ignore"
            )
            stdout = result.stdout.strip()
            if result.returncode == 0 and "connected to" in stdout.lower():
                return True, f"成功连接到 {safe_addr}"
            elif "already connected" in stdout.lower():
                return True, f"{safe_addr} 已连接"
            else:
                return False, f"连接失败：{stdout}"
        except subprocess.TimeoutExpired:
            return False, "连接超时"
        except Exception as e:
            return False, f"未知错误：{str(e)}"
