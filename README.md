Phone Agent Pro - Intelligent Multi-Modal Control Agent

Version: 1.2.9

**[English Version](README_en.md)**

## Phone Agent 智能版 v1.2.9 代码分析

### 📊 项目概述

**项目名称**: Phone Agent 智能版  
**版本**: v1.2.9（第1002次迭代）

### 🏗️ 架构设计

#### 核心AI系统架构
```
┌─────────────────────────────────────────┐
│         双AI协作系统                     │
├─────────────────────────────────────────┤
│  GLM-4.6v-flash    autoglm-phone        │
│  (决策层)           (执行层)             │
└─────────────────────────────────────────┘
         ↓                   ↓
    ┌──────────────────────────────────────┐
    │     双AI辅助系统                      │
    ├──────────────────────────────────────┤
    │  cogview-3-flash  cogvideox-flash    │
    │  (文生图)           (视频生成)       │
    └──────────────────────────────────────┘
```

#### 目录结构
```
YuntaiPhoneAgent/
├── yuntai/  # 核心模块
│   ├── handlers/ #存放GUI控制器（gui_controller.py）所需的函数
│   │      ├──__init__.py
│   │      ├──connection_handler.py
│   │      ├──dynamic_handler.py
│   │      ├──system_handler.py
│   │      └──tts_handler.py
│   ├── managers/ #存放任务管理（task_manager.py）所需的函数
│   │      ├──__init__.py
│   │      ├──task_logic.py
│   │      ├──tts_audio.py
│   │      ├──tts_database.py
│   │      ├──tts_engine.py
│   │      └──tts_text.py
│   ├──views/ #存放GUI视图（gui_view.py）所需的函数
│   │      ├──__init__.py
│   │      ├──connection.py
│   │      ├──dashboard.py
│   │      ├──dynamic.py
│   │      ├──history.py
│   │      ├──pages.py
│   │      ├──settings.py
│   │      ├──theme.py
│   │      └──tts.py
│   ├── __init__.py
│   ├── agent_core.py  # 代理核心
│   ├── agent_executor.py  # 执行器
│   ├── audio_processor.py  # 音频处理
│   ├── config.py  # 配置
│   ├── connection_manager.py  # 连接管理
│   ├── file_manager.py  # 文件管理
│   ├── gui_controller.py  # GUI控制器
│   ├── gui_view.py  # GUI视图
│   ├── main_app.py  # 主应用
│   ├── multimodal_other.py  # 多模态其他
│   ├── multimodal_processor.py  # 多模态处理器
│   ├── output_capture.py  # 输出捕获
│   ├── reply_manager.py  # 回复管理
│   ├── task_manager.py  # 任务管理
│   ├── task_recognizer.py  # 任务识别
│   └── utils.py  # 工具函数
├── phone_agent/  # 代理模块
│   ├── agent.py
│   └── model/
│       └── client.py
├── __init__.py
├── forever.txt  #可以自主创建，把绝对路径填入.env
├── main.py  # 主入口
├── requirements.txt
└── setup.py
```

### 🎯 核心功能模块

#### 1. 智能任务识别 (task_recognizer.py)
- 自动判断任务类型（自由聊天、手机操作、单次/持续回复、复杂操作）
- 支持快捷键快速启动应用（微信、QQ、抖音等）

#### 2. 手机自动化 (phone_agent/agent.py)
- 使用 VLM 理解屏幕内容并决策操作
- 支持多种操作：点击、输入、滑动、长按、双击、返回、Home
- 坐标系统：(0,0)左上角 → (999,999)右下角

#### 3. 持续回复管理 (agent_core.py)
- 终止机制：支持中途停止持续回复
- 消息归属判断：基于头像位置（左→对方，右→我方）和气泡颜色
- 相似度比对：使用最长公共子序列算法避免重复回复
- 循环检测：每轮检查新消息，最多30轮

#### 4. TTS语音合成 (task_manager.py)
- 集成 GPT-SoVITS 模型
- 支持分段合成（最大500字符/段）
- 并行合成提升效率
- 需要参考音频目录

#### 5. 多模态处理
- GLM-4.6v-flash：文本、视频、图片、文件分析
- cogview-3-flash：文生图
- cogvideox-flash：文生视频、图生视频、首尾帧生视频
- 文件上传：支持10MB，多种格式

#### 6. 手机投屏
- 使用 scrcpy 实现
- 可视化操作过程
- 支持USB/无线连接

### 🔧 技术栈

| 组件 | 技术 |
|------|------|
| GUI | tkinter + customtkinter |
| AI模型 | 智谱AI GLM-4.6v-flash, autoglm-phone, cogview-3-flash, cogvideox-flash |
| TTS | GPT-SoVITS |
| 手机控制 | ADB + scrcpy |
| SDK | zhipuai, openai |

### ⚙️ 关键配置

```python
# yun/config.py:17-59
GPT_SOVITS_ROOT = r"GPT-SoVITS实际根目录"
SCRCPY_PATH = r"scrcpy实际根目录"
ZHIPU_API_KEY = "替换为你的API key"
MAX_CYCLE_TIMES = 30
WAIT_INTERVAL = 1 s
MAX_FILE_SIZE = 10 MB
```

### 🔄 双AI协作流程

```
用户指令
    ↓
GLM-4.6v-flash (任务分类)
    ↓
┌───────────┬──────────┬──────────┬──────────┐
│自由聊天   │手机操作   │单次回复   │持续回复   │复杂操作
└─────┬─────┴─────┬────┴────┬─────┴─────┬────
      ↓           ↓        ↓          ↓
  GLM-4.6v   autoglm   提取记录→GLM   循环提取→GLM
  直接响应   执行操作   →回复→发送     →判断新消息
```

### 💡 特色功能

1. **智能颜色输出**：金色(GLM-4)、绿色(phone_agent)、蓝色(结果)【GUI版本无颜色支持功能】
2. **消息相似度算法**：LCS算法避免重复回复
3. **线程安全设计**：多线程环境下使用锁保护状态
4. **模块化重构**：TTS、GUI、业务逻辑分离
5. **配置验证机制**：启动时自动检查路径有效性
6. **持久化记忆**：forever.txt手动维护，conversation_history.json自动记录

### ⚠️ 配置要求

1. GPT-SoVITS根目录需手动创建"参考音频"文件夹
2. AI模型需按智谱官方文档部署环境
3. transformers依赖冲突可忽略
4. openai包版本需注意兼容性

### 📈 版本演进亮点

- v1.0: 基础CLI版
- v1.1: 集成TTS、GUI、投屏
- v1.2: 升级GLM-4.6v-flash多模态、引入双AI辅助系统

 项目展现了AI Agent、多模态、自动化技术的深度整合，是一个功能完善的智能手机操作代理系统。

## 🚀 使用方法

### 环境要求

#### 1. Python 环境
需要 Python 3.10 及以上版本。

#### 2. ADB (Android Debug Bridge)
1. 下载官方 ADB [安装包](https://developer.android.com/tools/releases/platform-tools?hl=zh-cn)
2. 解压并配置环境变量（Windows 添加到 PATH）。

#### 3. 安卓设备配置
- Android 7.0+ 设备或模拟器
- 启用开发者模式和 USB 调试
- 安装 ADB Keyboard APK

#### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 运行程序

#### 命令行
```bash
#配置好.env后直接运行主程序
python main.py 
```

### 环境变量
| 变量                        | 描述               | 默认值                        |
|---------------------------|------------------|----------------------------|
| `PHONE_AGENT_BASE_URL`    | 模型 API 地址        | `http://localhost:8000/v1` |
| `PHONE_AGENT_MODEL`       | 模型名称             | `autoglm-phone-9b`         |
| `PHONE_AGENT_API_KEY`     | API Key          | `EMPTY`                    |
| `PHONE_AGENT_MAX_STEPS`   | 每个任务最大步数         | `100`                      |
| `PHONE_AGENT_DEVICE_ID`   | ADB 设备 ID        | (自动检测)                     |
| `PHONE_AGENT_LANG`        | 语言 (`cn`/`en`)   | `cn`                       |

### 常见问题
- 设备未找到：检查 USB 调试和数据线
- 无法点击：启用 USB 调试（安全设置）
- 文本输入不工作：确保 ADB Keyboard 已安装并启用
