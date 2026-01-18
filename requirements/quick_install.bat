@echo off
REM ==================== Windows快速安装脚本 ====================
echo 正在安装 Phone Agent 依赖...
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.9
    pause
    exit /b 1
)

echo ✅ 找到Python
echo.

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip
echo.

REM 安装核心依赖
echo 安装核心依赖...
pip install customtkinter==5.2.2
pip install zhipuai==2.0.0
pip install requests==2.31.0
echo.

REM 安装音频依赖
echo 安装音频依赖...
pip install pyaudio==0.2.13
pip install soundfile==0.12.1
pip install wave
echo.

REM 安装ADB工具
echo 安装ADB工具...
pip install adbutils==2.7.7
echo.

REM 安装数据处理
echo 安装数据处理...
pip install numpy==1.24.3
pip install Pillow==10.1.0
echo.

REM 可选：安装TTS依赖
echo 可选：安装TTS依赖（需要GPU）...
set /p install_tts="是否安装TTS依赖？(y/n): "
if /i "%install_tts%"=="y" (
    pip install torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu118
    pip install transformers==4.35.2
    pip install librosa==0.10.1
    echo ✅ TTS依赖安装完成
)

echo.
echo 🎉 所有依赖安装完成！
echo.
echo 运行以下命令启动程序：
echo python main.py
pause