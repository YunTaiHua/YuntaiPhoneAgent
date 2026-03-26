"""
Phone Agent - 智能版 v1.3.5 (Web入口)

更新日志详见: doc/CHANGELOG.md
技术架构详见: doc/ARCHITECTURE.md
"""

import os
import sys
import socket
from pathlib import Path

# 预加载 onnxruntime (解决DLL冲突问题)
import onnxruntime
onnxruntime.get_available_providers()

# 切换到 GPT-SoVITS 目录
from yuntai.core.config import GPT_SOVITS_ROOT, PROJECT_ROOT, SCRCPY_PATH, APP_VERSION
if GPT_SOVITS_ROOT and Path(GPT_SOVITS_ROOT).exists():
    os.chdir(str(GPT_SOVITS_ROOT))

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

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

def get_local_ip():
    """获取本机局域网IP地址"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return None


def main():
    """主函数"""
    print("=" * 60)
    print(f"  Phone Agent Web v{APP_VERSION}")
    print("  智能移动助手 - Web版本")
    print("=" * 60)
    
    from yuntai.core.config import validate_config, print_config_summary
    
    if not validate_config():
        print("❌ 配置验证失败，请检查 .env 文件")
        sys.exit(1)
    
    print_config_summary()
    
    web_dir = Path(PROJECT_ROOT) / "web"
    web_dir.mkdir(parents=True, exist_ok=True)
    (web_dir / "static").mkdir(parents=True, exist_ok=True)
    
    local_ip = get_local_ip()
    
    print("\n🚀 启动Web服务器...")
    print(f"📍 本地访问: http://localhost:8000")
    if local_ip:
        print(f"📍 局域网访问: http://{local_ip}:8000")
    print("📍 按 Ctrl+C 停止服务器\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
