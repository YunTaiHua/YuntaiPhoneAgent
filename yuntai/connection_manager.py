#!/usr/bin/env python3
"""
连接管理模块 - 支持USB和无线调试两种方式
"""
import subprocess
import json
import os
from typing import List, Tuple, Dict

from yuntai.config import Color, CONNECTION_CONFIG_FILE


class ConnectionManager:
    def __init__(self):
        pass

    def load_connection_config(self) -> Dict[str, str]:
        """加载连接配置"""
        default_config = {
            "connection_type": "wireless",  # wireless 或 usb
            "wireless_ip": "",
            "wireless_port": "5555",
            "usb_device_id": ""
        }

        try:
            if os.path.exists(CONNECTION_CONFIG_FILE):
                with open(CONNECTION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并配置，确保所有字段都存在
                    for key in default_config:
                        if key not in config:
                            config[key] = default_config[key]
                    return config
        except Exception as e:
            print(f"{Color.GOLD}⚠️  读取连接配置失败: {e}{Color.RESET}")

        return default_config

    def save_connection_config(self, config: Dict[str, str]):
        """保存连接配置"""
        try:
            with open(CONNECTION_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"{Color.GOLD}⚠️  保存连接配置失败: {e}{Color.RESET}")

    def get_available_devices(self) -> List[str]:
        """获取可用的ADB设备列表"""
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
            for line in lines[1:]:  # 跳过第一行标题
                if line.strip() and "device" in line:
                    device_id = line.split("\t")[0].strip()
                    devices.append(device_id)

            return devices
        except Exception as e:
            print(f"{Color.GOLD}⚠️  获取设备列表失败: {e}{Color.RESET}")
            return []

    def interactive_setup_connection(self) -> Dict[str, str]:
        """交互式设置连接方式"""
        print(f"\n{Color.GOLD}📱 手机连接设置{Color.RESET}")
        print(f"{Color.GOLD}════════════════════════════════════════{Color.RESET}")

        # 加载现有配置
        config = self.load_connection_config()

        # 选择连接方式
        print(f"\n{Color.GOLD}请选择连接方式:{Color.RESET}")
        print(f"{Color.GOLD}1. USB调试（通过USB数据线连接）{Color.RESET}")
        print(f"{Color.GOLD}2. 无线调试（通过Wi-Fi连接）{Color.RESET}")

        while True:
            choice = input(f"{Color.GOLD}请选择 (1/2): {Color.RESET}").strip()
            if choice == "1":
                config["connection_type"] = "usb"
                break
            elif choice == "2":
                config["connection_type"] = "wireless"
                break
            else:
                print(f"{Color.GOLD}⚠️  请输入1或2{Color.RESET}")

        # USB连接设置
        if config["connection_type"] == "usb":
            print(f"\n{Color.GOLD}🔌 USB调试设置:{Color.RESET}")

            # 检查USB设备
            devices = self.get_available_devices()
            usb_devices = [d for d in devices if ":" not in d]  # USB设备通常没有冒号

            if usb_devices:
                print(f"{Color.GREEN}✅ 检测到以下USB设备:{Color.RESET}")
                for i, device in enumerate(usb_devices, 1):
                    print(f"{Color.GREEN}  {i}. {device}{Color.RESET}")

                if len(usb_devices) == 1:
                    config["usb_device_id"] = usb_devices[0]
                    print(f"{Color.GREEN}✅ 已自动选择设备: {config['usb_device_id']}{Color.RESET}")
                else:
                    print(f"\n{Color.GOLD}请选择要连接的设备:{Color.RESET}")
                    for i, device in enumerate(usb_devices, 1):
                        print(f"{Color.GOLD}  {i}. {device}{Color.RESET}")

                    while True:
                        try:
                            choice = int(input(f"{Color.GOLD}请选择 (1-{len(usb_devices)}): {Color.RESET}").strip())
                            if 1 <= choice <= len(usb_devices):
                                config["usb_device_id"] = usb_devices[choice - 1]
                                break
                            else:
                                print(f"{Color.GOLD}⚠️  请输入有效的数字{Color.RESET}")
                        except ValueError:
                            print(f"{Color.GOLD}⚠️  请输入数字{Color.RESET}")
            else:
                print(f"{Color.GOLD}⚠️  未检测到USB设备{Color.RESET}")
                print(f"{Color.GOLD}请确保:{Color.RESET}")
                print(f"{Color.GOLD}  1. 手机已通过USB连接到电脑{Color.RESET}")
                print(f"{Color.GOLD}  2. 手机已开启USB调试模式{Color.RESET}")
                print(f"{Color.GOLD}  3. 已授权电脑进行调试{Color.RESET}")
                print(f"\n{Color.GOLD}按回车键重新检测，或输入任意字符手动输入设备ID:{Color.RESET}")

                if input().strip() == "":
                    devices = self.get_available_devices()
                    usb_devices = [d for d in devices if ":" not in d]
                    if usb_devices:
                        config["usb_device_id"] = usb_devices[0]
                    else:
                        config["usb_device_id"] = input(f"{Color.GOLD}请输入设备ID: {Color.RESET}").strip()
                else:
                    config["usb_device_id"] = input(f"{Color.GOLD}请输入设备ID: {Color.RESET}").strip()

        # 无线连接设置
        else:
            print(f"\n{Color.GOLD}📶 无线调试设置:{Color.RESET}")

            # 检查现有配置
            if config.get("wireless_ip"):
                print(f"{Color.GOLD}当前配置的IP地址: {config['wireless_ip']}{Color.RESET}")
                use_existing = input(f"{Color.GOLD}是否使用此IP？(y/n): {Color.RESET}").strip().lower()
                if use_existing != 'y':
                    config["wireless_ip"] = ""

            if not config.get("wireless_ip"):
                # 检查已连接的无线设备
                devices = self.get_available_devices()
                wireless_devices = [d for d in devices if ":" in d]  # 无线设备通常包含冒号和端口

                if wireless_devices:
                    print(f"{Color.GREEN}✅ 检测到以下无线设备:{Color.RESET}")
                    for i, device in enumerate(wireless_devices, 1):
                        print(f"{Color.GREEN}  {i}. {device}{Color.RESET}")

                    choice = input(f"{Color.GOLD}是否连接这些设备？(y/n): {Color.RESET}").strip().lower()
                    if choice == 'y':
                        if len(wireless_devices) == 1:
                            device_parts = wireless_devices[0].split(":")
                            config["wireless_ip"] = device_parts[0]
                            if len(device_parts) > 1:
                                config["wireless_port"] = device_parts[1]
                        else:
                            print(f"\n{Color.GOLD}请选择要连接的设备:{Color.RESET}")
                            for i, device in enumerate(wireless_devices, 1):
                                print(f"{Color.GOLD}  {i}. {device}{Color.RESET}")

                            while True:
                                try:
                                    choice = int(
                                        input(f"{Color.GOLD}请选择 (1-{len(wireless_devices)}): {Color.RESET}").strip())
                                    if 1 <= choice <= len(wireless_devices):
                                        device_parts = wireless_devices[choice - 1].split(":")
                                        config["wireless_ip"] = device_parts[0]
                                        if len(device_parts) > 1:
                                            config["wireless_port"] = device_parts[1]
                                        break
                                    else:
                                        print(f"{Color.GOLD}⚠️  请输入有效的数字{Color.RESET}")
                                except ValueError:
                                    print(f"{Color.GOLD}⚠️  请输入数字{Color.RESET}")

                if not config.get("wireless_ip"):
                    # 手动输入IP地址
                    print(f"\n{Color.GOLD}请手动输入手机IP地址:{Color.RESET}")
                    print(f"{Color.GOLD}格式: IP地址或IP:端口 (例如: 192.168.1.100 或 192.168.1.100:5555){Color.RESET}")

                    while True:
                        ip_input = input(f"{Color.GOLD}请输入: {Color.RESET}").strip()
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
                            print(f"{Color.GOLD}⚠️  IP地址不能为空{Color.RESET}")

        # 保存配置
        self.save_connection_config(config)
        return config

    def connect_to_device(self, config: Dict[str, str]) -> Tuple[bool, str, str]:
        """
        连接到设备
        返回: (是否成功, 设备ID, 消息)
        """
        connection_type = config.get("connection_type", "wireless")

        if connection_type == "usb":
            # USB连接
            device_id = config.get("usb_device_id", "")

            if not device_id:
                return False, "", "未配置USB设备ID"

            # 检查设备是否已连接
            devices = self.get_available_devices()
            usb_devices = [d for d in devices if ":" not in d]

            if device_id in usb_devices:
                return True, device_id, f"✅ USB设备已连接: {device_id}"
            else:
                # 尝试重新连接
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
            # 无线连接
            wireless_ip = config.get("wireless_ip", "")
            wireless_port = config.get("wireless_port", "5555")

            if not wireless_ip:
                return False, "", "未配置无线IP地址"

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
                stderr = result.stderr.strip()

                if result.returncode == 0 and "connected to" in stdout.lower():
                    return True, device_addr, f"已连接到无线设备: {device_addr}"
                elif "already connected" in stdout.lower():
                    return True, device_addr, f"✅ 无线设备已连接: {device_addr}"
                elif stderr:
                    return False, "", f"无线连接失败: {stderr}"
                else:
                    return False, "", f"无线连接失败: {stdout}"
            except subprocess.TimeoutExpired:
                return False, "", "无线连接超时"
            except FileNotFoundError:
                return False, "", "未找到ADB命令"
            except Exception as e:
                return False, "", f"无线连接未知错误: {str(e)}"

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
            stderr = result.stderr.strip()
            if result.returncode == 0 and "connected to" in stdout.lower():
                return True, f"成功连接到 {device_addr}"
            elif "already connected" in stdout.lower():
                return True, f"{device_addr} 已连接"
            elif stderr:
                return False, f"连接失败：{stderr}"
            else:
                return False, f"连接失败：{stdout}"
        except subprocess.TimeoutExpired:
            return False, "连接超时"
        except FileNotFoundError:
            return False, "未找到ADB命令"
        except Exception as e:
            return False, f"未知错误：{str(e)}"