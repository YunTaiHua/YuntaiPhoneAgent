"""
GUI 应用入口模块
================

本模块是 Phone Agent GUI 版本的入口点，提供基于 PyQt6 的桌面界面。

主要功能：
    - 预加载 onnxruntime 解决 DLL 冲突问题
    - 切换工作目录到 GPT-SoVITS
    - 创建并运行 PyQt6 应用
    - 处理应用启动异常

使用示例：
    >>> # 直接运行启动 GUI 应用
    >>> python main.py

注意事项：
    - 需要先配置 .env 文件中的环境变量
    - onnxruntime 需要在 PyQt6 之前导入以避免 DLL 冲突
    - 应用会自动切换到 GPT-SoVITS 目录以支持 TTS 功能
"""

# ========================================
# 【1. 全局依赖导入区】
# ========================================
import atexit
import logging
import os
import sys
import warnings
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 过滤冗余警告
warnings.filterwarnings('ignore')

# 关键修复：在导入PyQt6之前先导入onnxruntime，避免DLL初始化失败
# 这是由于PyQt6和onnxruntime的动态链接库加载顺序问题
try:
    import onnxruntime
    print("✅ onnxruntime 预加载成功")
    logger.debug("onnxruntime 预加载成功")
except ImportError:
    print("⚠️ onnxruntime 未安装，TTS功能将不可用")
    logger.warning("onnxruntime 未安装，TTS功能将不可用")
except Exception as e:
    print(f"⚠️ onnxruntime 预加载失败: {e}")
    logger.warning("onnxruntime 预加载失败: %s", str(e))

# PyQt6 导入
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# 重构模块
from yuntai.core.main_app import MainApp

# 使用统一配置
from yuntai.core.config import GPT_SOVITS_ROOT


# ========================================
# 【2. 主函数入口区】
# ========================================
def main() -> None:
    """
    主函数入口
    
    执行以下操作：
        1. 保存原始工作目录
        2. 切换到 GPT-SoVITS 目录（如果配置了）
        3. 创建并运行 PyQt6 应用
        4. 退出时恢复原始目录
    
    注意：
        - 应用启动失败时会记录错误日志并打印堆栈跟踪
        - 工作目录切换是为了支持 TTS 语音合成功能
    """
    try:
        # 保存原始工作目录
        original_cwd = Path.cwd()
        logger.debug("原始工作目录: %s", original_cwd)

        # 使用统一配置的 GPT-SoVITS 目录
        gpt_sovits_dir = GPT_SOVITS_ROOT
        if gpt_sovits_dir and Path(gpt_sovits_dir).exists():
            os.chdir(str(gpt_sovits_dir))
            logger.debug("切换到工作目录: %s", gpt_sovits_dir)

        # 创建并运行应用
        app = MainApp()
        sys.exit(app.run())

    except Exception as e:
        logger.exception("应用启动失败: %s", str(e))
        print(f"❌ 应用启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
