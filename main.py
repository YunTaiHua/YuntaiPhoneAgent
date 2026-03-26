"""
Phone Agent - 智能版 v1.3.5

更新日志详见: doc/CHANGELOG.md
技术架构详见: doc/ARCHITECTURE.md
"""

# ========================================
# 【1. 全局依赖导入区】
# ========================================
import sys
import os
import atexit
import warnings
import logging
from pathlib import Path
from typing import NoReturn

# 关键修复：在导入PyQt6之前先导入onnxruntime，避免DLL初始化失败
# 这是由于PyQt6和onnxruntime的动态链接库加载顺序问题
try:
    import onnxruntime
    print("✅ onnxruntime 预加载成功")
except ImportError:
    print("⚠️ onnxruntime 未安装，TTS功能将不可用")
except Exception as e:
    print(f"⚠️ onnxruntime 预加载失败: {e}")

# PyQt6 导入
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 过滤冗余警告
warnings.filterwarnings('ignore')

# 重构模块
from yuntai.core.main_app import MainApp

# 使用统一配置
from yuntai.core.config import GPT_SOVITS_ROOT


# ========================================
# 【2. 主函数入口区】
# ========================================
def main():
    """主函数：切换工作目录→初始化应用→启动主循环→退出时恢复目录"""
    try:
        # 保存原始工作目录
        original_cwd = Path.cwd()

        # 使用统一配置的 GPT-SoVITS 目录
        gpt_sovits_dir = GPT_SOVITS_ROOT
        if gpt_sovits_dir and Path(gpt_sovits_dir).exists():
            os.chdir(str(gpt_sovits_dir))
            #print(f"📂 切换到工作目录: {gpt_sovits_dir}")

        # 创建并运行应用
        app = MainApp()
        sys.exit(app.run())

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
