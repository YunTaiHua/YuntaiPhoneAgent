#!/usr/bin/env python3
"""
工具函数模块
"""
import sys
import shutil
import subprocess
import openai
from typing import Tuple

from yuntai.config import Color


class Utils:
    def __init__(self):
        pass

    def enable_windows_color(self):
        if sys.platform == "win32":
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except:
                pass

    def check_system_requirements(self) -> bool:
        print(f"{Color.GOLD}🔍 检查系统要求...{Color.RESET}")
        all_passed = True

        print(f"{Color.GOLD}1. 检查ADB安装...{Color.RESET}", end=" ")
        if shutil.which("adb") is None:
            print("❌ 失败")
            all_passed = False
        else:
            try:
                result = subprocess.run(
                    ["adb", "version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    encoding="utf-8",
                    errors="ignore"
                )
                if result.returncode == 0:
                    print("")
                else:
                    print("❌ 失败")
                    all_passed = False
            except Exception:
                print("❌ 失败")
                all_passed = False

        return all_passed

    def check_model_api(self, base_url: str, model_name: str, api_key: str = "EMPTY") -> bool:
        print(f"{Color.GOLD}🔍 检查模型API...{Color.RESET}")
        try:
            client = openai.OpenAI(base_url=base_url, api_key=api_key, timeout=30.0)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                temperature=0.0,
                stream=False,
            )
            if response.choices and len(response.choices) > 0:
                #print("✅ 正常")
                return True
            else:
                print("❌ 失败")
                return False
        except Exception as e:
            print(f"❌ 失败: {e}")
            return False