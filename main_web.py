"""
Web 应用入口模块
================

本模块是 Phone Agent Web 版本的入口点，提供基于 FastAPI 的 Web 界面。

主要功能：
    - 创建 FastAPI 应用实例
    - 配置 CORS 中间件（安全配置）
    - 初始化 WebSocket 管理器和控制器
    - 设置路由和静态文件服务
    - 启动 Web 服务器

使用示例：
    >>> # 直接运行启动 Web 服务
    >>> python main_web.py
    
    >>> # 或使用 uvicorn 启动
    >>> uvicorn main_web:app --host 0.0.0.0 --port 8000

注意事项：
    - 需要先配置 .env 文件中的环境变量
    - CORS 配置可通过环境变量 ALLOWED_ORIGINS 自定义
    - 默认监听 0.0.0.0:8000，支持局域网访问
"""
import logging
import os
import socket
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 预加载 onnxruntime (解决DLL冲突问题)
try:
    import onnxruntime
    onnxruntime.get_available_providers()
    logger.debug("onnxruntime 预加载成功")
except ImportError:
    logger.warning("onnxruntime 未安装，TTS功能将不可用")
except Exception as e:
    logger.warning("onnxruntime 预加载失败: %s", str(e))

# 切换到 GPT-SoVITS 目录
from yuntai.core.config import GPT_SOVITS_ROOT, PROJECT_ROOT, SCRCPY_PATH, APP_VERSION
if GPT_SOVITS_ROOT and Path(GPT_SOVITS_ROOT).exists():
    os.chdir(str(GPT_SOVITS_ROOT))
    logger.debug("切换到 GPT-SoVITS 目录: %s", GPT_SOVITS_ROOT)

# FastAPI 相关
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导入Web模块
from web.core import setup_routes, WebController, ConnectionManager


# ==================== 创建FastAPI应用 ====================

app = FastAPI(
    title="Phone Agent Web",
    description="智能移动助手 Web版本",
    version=APP_VERSION
)

# CORS 安全配置
# 从环境变量读取允许的来源，默认为本地开发环境
# 生产环境应设置 ALLOWED_ORIGINS 环境变量，多个来源用逗号分隔
# 示例: ALLOWED_ORIGINS=http://localhost:8000,http://192.168.1.100:8000
_allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000")
ALLOWED_ORIGINS = [origin.strip() for origin in _allowed_origins_str.split(",") if origin.strip()]

# 如果环境变量为空或仅包含通配符，则使用安全默认值
if not ALLOWED_ORIGINS or ALLOWED_ORIGINS == ["*"]:
    ALLOWED_ORIGINS = ["http://localhost:8000"]
    logger.warning("CORS 配置使用默认值，生产环境请设置 ALLOWED_ORIGINS 环境变量")

# 添加CORS中间件 - 安全配置：禁用allow_credentials防止CSRF风险
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

logger.debug("CORS 中间件已配置，允许的来源: %s", ALLOWED_ORIGINS)

# 创建WebSocket管理器
ws_manager = ConnectionManager()

# 创建Web控制器
controller = WebController(ws_manager)

# 设置路由
setup_routes(app, controller, ws_manager)

# 挂载静态文件 - 使用web模块所在目录
from web.core.routes import WEB_DIR
static_dir = Path(WEB_DIR) / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ==================== 主函数 ====================

def get_local_ip() -> str | None:
    """
    获取本机局域网IP地址
    
    通过创建 UDP 连接获取本机在局域网中的 IP 地址。
    此方法不需要实际发送数据，仅用于获取本地 IP。
    
    Returns:
        str | None: 本机局域网 IP 地址，获取失败返回 None
    
    使用示例：
        >>> ip = get_local_ip()
        >>> if ip:
        ...     print(f"局域网IP: {ip}")
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        logger.warning("获取本机IP失败: %s", str(e))
        return None


def main() -> None:
    """
    主函数入口
    
    执行以下操作：
        1. 打印启动信息
        2. 验证配置文件
        3. 创建必要的目录
        4. 启动 Web 服务器
    
    注意：
        - 如果配置验证失败，程序将退出并返回错误码 1
        - 服务器默认监听 0.0.0.0:8000
    """
    print("=" * 60)
    print(f"  Phone Agent Web v{APP_VERSION}")
    print("  智能移动助手 - Web版本")
    print("=" * 60)
    
    from yuntai.core.config import validate_config, print_config_summary
    
    if not validate_config():
        print("❌ 配置验证失败，请检查 .env 文件")
        logger.error("配置验证失败，程序退出")
        sys.exit(1)
    
    print_config_summary()
    
    web_dir = Path(PROJECT_ROOT) / "web"
    web_dir.mkdir(parents=True, exist_ok=True)
    (web_dir / "static").mkdir(parents=True, exist_ok=True)
    logger.debug("Web 目录已创建: %s", web_dir)
    
    local_ip = get_local_ip()
    
    print("\n🚀 启动Web服务器...")
    print(f"📍 本地访问: http://localhost:8000")
    if local_ip:
        print(f"📍 局域网访问: http://{local_ip}:8000")
    print("📍 按 Ctrl+C 停止服务器\n")
    
    logger.debug("Web 服务器启动中...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
