"""
main_web.py - Web版本入口文件
提供与GUI版本完全一致的功能，通过浏览器访问
"""

import os
import sys

# 预加载 onnxruntime (解决DLL冲突问题)
import onnxruntime
onnxruntime.get_available_providers()

# 切换到 GPT-SoVITS 目录
from yuntai.core.config import GPT_SOVITS_ROOT, PROJECT_ROOT, SCRCPY_PATH, APP_VERSION
if os.path.exists(GPT_SOVITS_ROOT):
    os.chdir(GPT_SOVITS_ROOT)

# FastAPI 相关
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导入Web模块
from web.routes import setup_routes
from web.controller import WebController
from web.ws_manager import ConnectionManager


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
from web.routes import WEB_DIR
static_dir = os.path.join(WEB_DIR, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ==================== 主函数 ====================

def main():
    """主函数"""
    print("=" * 60)
    print(f"  Phone Agent Web v{APP_VERSION}")
    print("  智能移动助手 - Web版本")
    print("=" * 60)
    
    from yuntai.core.config import validate_config, print_config_summary
    
    # 验证配置
    if not validate_config():
        print("❌ 配置验证失败，请检查 .env 文件")
        sys.exit(1)
    
    print_config_summary()
    
    # 创建web目录
    web_dir = os.path.join(PROJECT_ROOT, "web")
    os.makedirs(web_dir, exist_ok=True)
    os.makedirs(os.path.join(web_dir, "static"), exist_ok=True)
    
    # 启动服务器
    print("\n🚀 启动Web服务器...")
    print(f"📍 访问地址: http://localhost:8000")
    print("📍 按 Ctrl+C 停止服务器\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
