# ==================== 版本检查脚本 ====================
# !/usr/bin/env python3
"""
依赖版本检查脚本
运行此脚本检查所有必需的包是否已安装
"""

import sys
import subprocess
import pkg_resources

REQUIRED_PACKAGES = {
    # 核心GUI
    'customtkinter': '5.2.2',

    # AI和API
    'zhipuai': '2.0.0',

    # 语音合成
    'torch': '2.1.0',
    'torchaudio': '2.1.0',

    # 音频处理
    'soundfile': '0.12.1',
    'pyaudio': '0.2.13',

    # 数据处理
    'numpy': '1.24.3',
    'Pillow': '10.1.0',

    # 手机控制
    'adbutils': '2.7.7',
}


def check_package(package, required_version):
    """检查单个包的安装情况"""
    try:
        installed_version = pkg_resources.get_distribution(package).version
        if pkg_resources.parse_version(installed_version) >= pkg_resources.parse_version(required_version):
            return True, installed_version
        else:
            return False, installed_version
    except pkg_resources.DistributionNotFound:
        return None, None


def main():
    print("🔍 检查依赖包安装情况...")
    print("=" * 50)

    all_ok = True
    results = []

    for package, required_version in REQUIRED_PACKAGES.items():
        is_ok, installed_version = check_package(package, required_version)

        if is_ok is None:
            status = "❌ 未安装"
            all_ok = False
        elif is_ok:
            status = "✅ 已安装"
        else:
            status = "⚠️  版本过低"
            all_ok = False

        results.append(f"{package:20} {required_version:10} → {installed_version or 'N/A':10} {status}")

    for result in results:
        print(result)

    print("=" * 50)

    if all_ok:
        print("🎉 所有依赖包检查通过！")
        return 0
    else:
        print("❌ 部分依赖包缺失或版本过低")
        print("请运行: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())