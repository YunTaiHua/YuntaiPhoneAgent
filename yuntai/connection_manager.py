#!/usr/bin/env python3
"""
连接管理模块 - 支持USB和无线调试两种方式
支持Android (ADB)、鸿蒙 (HDC) 和 iOS 设备
"""
import subprocess
import json
import os
from typing import List, Tuple, Dict, Optional

from yuntai.config import (
    CONNECTION_CONFIG_FILE,
    DEVICE_TYPE_ANDROID,
    DEVICE_TYPE_HARMONY,
    DEVICE_TYPE_IOS,
    DEFAULT_DEVICE_TYPE,
    IOS_WDA_URL
)


class ConnectionManager:
    def __init__(self, device_type: str = DEFAULT_DEVICE_TYPE):
        """
        初始化连接管理器

        Args:
            device_type: 设备类型 (android/harmony/ios)
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
            "device_type": DEFAULT_DEVICE_TYPE
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
        """获取可用的设备列表（根据设备类型自动选择工具）"""
        devices = []

        if self.device_type == DEVICE_TYPE_IOS:
            devices = self._get_ios_devices()
        elif self.device_type == DEVICE_TYPE_HARMONY:
            devices = self._get_harmony_devices()
        else:
            devices = self._get_android_devices()

        return devices

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
        """获取鸿蒙设备列表 (HDC)"""
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

            lines = result.stdout.strip().split("\n")
            for line in lines:
                if line.strip():
                    devices.append(line.strip())

            return devices
        except FileNotFoundError:
            print("⚠️  HDC工具未找到，请确保已安装HarmonyOS SDK")
            return []
        except Exception as e:
            print(f"⚠️  获取鸿蒙设备列表失败: {e}")
            return []

    def _get_ios_devices(self) -> List[str]:
        """获取iOS设备列表 (libimobiledevice)"""
        devices = []
        try:
            result = subprocess.run(
                ["idevice_id", "-ln"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="ignore"
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    if line.strip():
                        devices.append(line.strip())

            return devices
        except FileNotFoundError:
            print("⚠️  libimobiledevice未找到，请确保已安装iOS开发工具")
            return []
        except Exception as e:
            print(f"⚠️  获取iOS设备列表失败: {e}")
            return []

    def connect_to_device(self, config: Dict[str, str]) -> Tuple[bool, str, str]:
        """
        连接到设备（根据设备类型自动选择连接方式）

        Returns: (是否成功, 设备ID, 消息)
        """
        connection_type = config.get("connection_type", "wireless")
        device_id = config.get("usb_device_id", "") or config.get("wireless_ip", "")

        if not device_id:
            return False, "", "未配置设备ID"

        if self.device_type == DEVICE_TYPE_IOS:
            return self._connect_ios_device(device_id, config)
        elif self.device_type == DEVICE_TYPE_HARMONY:
            return self._connect_harmony_device(device_id, connection_type, config)
        else:
            return self._connect_android_device(device_id, connection_type, config)

    def _connect_android_device(self, device_id: str, connection_type: str, config: Dict[str, str]) -> Tuple[bool, str, str]:
        """连接Android设备 (ADB)"""
        if connection_type == "usb":
            devices = self._get_android_devices()
            if device_id in devices:
                return True, device_id, f"✅ USB设备已连接: {device_id}"
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
        """连接鸿蒙设备 (HDC)"""
        try:
            if connection_type == "usb":
                result = subprocess.run(
                    ["hdc", "connect", device_id],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    encoding="utf-8",
                    errors="ignore"
                )
            else:
                wireless_ip = config.get("wireless_ip", "")
                wireless_port = config.get("wireless_port", "5555")
                device_addr = f"{wireless_ip}:{wireless_port}"
                result = subprocess.run(
                    ["hdc", "connect", device_addr],
                    capture_output=True,
                    text=True,
                    timeout=15,
                    encoding="utf-8",
                    errors="ignore"
                )

            stdout = result.stdout.strip()
            if result.returncode == 0 and ("success" in stdout.lower() or "connected" in stdout.lower()):
                return True, device_id, f"✅ 鸿蒙设备已连接: {device_id}"
            else:
                return False, "", f"连接失败: {stdout}"
        except FileNotFoundError:
            return False, "", "HDC工具未找到"
        except Exception as e:
            return False, "", f"连接失败: {str(e)}"

    def _connect_ios_device(self, device_id: str, config: Dict[str, str]) -> Tuple[bool, str, str]:
        """连接iOS设备 - iOS使用WebDriverAgent，无需传统连接"""
        devices = self._get_ios_devices()

        if device_id in devices:
            return True, device_id, f"✅ iOS设备已识别: {device_id}"
        elif not devices:
            return False, "", "未检测到iOS设备，请确保设备已连接并信任此电脑"
        else:
            return True, devices[0], f"✅ 已选择iOS设备: {devices[0]}"

    def check_wda_status(self, wda_url: str = IOS_WDA_URL) -> Tuple[bool, dict]:
        """
        检查WebDriverAgent状态（iOS专用）

        Returns: (是否就绪, 状态信息)
        """
        try:
            import requests
            response = requests.get(f"{wda_url}/status", timeout=5)
            if response.status_code == 200:
                return True, response.json()
            return False, {}
        except Exception as e:
            return False, {}

    def interactive_setup_connection(self) -> Dict[str, str]:
        """交互式设置连接方式"""
        print(f"\n📱 手机连接设置")
        print(f"════════════════════════════════════════")

        config = self.load_connection_config()

        print(f"\n请选择设备类型:")
        print(f"1. Android (ADB)")
        print(f"2. 鸿蒙 (HDC)")
        print(f"3. iOS")

        while True:
            choice = input(f"请选择 (1/2/3): ").strip()
            if choice == "1":
                config["device_type"] = DEVICE_TYPE_ANDROID
                self.device_type = DEVICE_TYPE_ANDROID
                break
            elif choice == "2":
                config["device_type"] = DEVICE_TYPE_HARMONY
                self.device_type = DEVICE_TYPE_HARMONY
                break
            elif choice == "3":
                config["device_type"] = DEVICE_TYPE_IOS
                self.device_type = DEVICE_TYPE_IOS
                break
            else:
                print(f"⚠️  请输入1、2或3")

        if config["device_type"] == DEVICE_TYPE_IOS:
            print(f"\n🍎 iOS设备设置:")
            print(f"iOS设备使用WebDriverAgent (WDA) 进行控制")
            print(f"请确保:")
            print(f"  1. Xcode已安装且WebDriverAgent已配置")
            print(f"  2. 设备已连接并信任此电脑")
            print(f"  3. WDA正在运行 (默认: {IOS_WDA_URL})")
            config["wda_url"] = IOS_WDA_URL
            self.save_connection_config(config)
            return config

        print(f"\n请选择连接方式:")
        print(f"1. USB调试（通过USB数据线连接）")
        print(f"2. 无线调试（通过Wi-Fi连接）")

        while True:
            choice = input(f"请选择 (1/2): ").strip()
            if choice == "1":
                config["connection_type"] = "usb"
                break
            elif choice == "2":
                config["connection_type"] = "wireless"
                break
            else:
                print(f"⚠️  请输入1或2")

        if config["connection_type"] == "usb":
            print(f"\n🔌 USB调试设置:")
            devices = self.get_available_devices()

            if devices:
                print(f"✅ 检测到以下设备:")
                for i, device in enumerate(devices, 1):
                    print(f"  {i}. {device}")

                if len(devices) == 1:
                    config["usb_device_id"] = devices[0]
                    print(f"✅ 已自动选择设备: {config['usb_device_id']}")
                else:
                    print(f"\n请选择要连接的设备:")
                    for i, device in enumerate(devices, 1):
                        print(f"  {i}. {device}")

                    while True:
                        try:
                            choice = int(input(f"请选择 (1-{len(devices)}): ").strip())
                            if 1 <= choice <= len(devices):
                                config["usb_device_id"] = devices[choice - 1]
                                break
                            else:
                                print(f"⚠️  请输入有效的数字")
                        except ValueError:
                            print(f"⚠️  请输入数字")
            else:
                print(f"⚠️  未检测到设备")
                config["usb_device_id"] = input(f"请输入设备ID: ").strip()

        else:
            print(f"\n📶 无线调试设置:")
            if config.get("wireless_ip"):
                print(f"当前配置的IP地址: {config['wireless_ip']}")
                use_existing = input(f"是否使用此IP？(y/n): ").strip().lower()
                if use_existing != 'y':
                    config["wireless_ip"] = ""

            if not config.get("wireless_ip"):
                devices = self.get_available_devices()
                wireless_devices = [d for d in devices if ":" in d]

                if wireless_devices:
                    print(f"✅ 检测到以下无线设备:")
                    for i, device in enumerate(wireless_devices, 1):
                        print(f"  {i}. {device}")

                if not config.get("wireless_ip"):
                    print(f"\n请手动输入设备IP地址:")
                    print(f"格式: IP地址或IP:端口 (例如: 192.168.1.100 或 192.168.1.100:5555)")

                    while True:
                        ip_input = input(f"请输入: ").strip()
                        if ip_input:
                            if ":" in ip_input:
                                ip_parts = ip_input.split(":")
                                config["wireless_ip"] = ip_parts[0]
                                if len(ip_parts) > 1:
                                    config["wireless_port"] = ip_parts[1]
                            else:
                                config["wireless_ip"] = ip_input
                            break
                        else:
                            print(f"⚠️  IP地址不能为空")

        self.save_connection_config(config)
        return config

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