# YuntaiPhoneAgent

Version: 1.3.4

**[English Version](README_en.md)**

## Phone Agent 智能版 v1.3.4 代码分析

### 📊 项目概述

**项目名称**: YuntaiPhoneAgent
**版本**: v1.3.4

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
├── yuntai/                    # 核心模块
│   ├── core/                  # 核心基础设施
│   │   ├── __init__.py
│   │   ├── config.py          # 配置管理
│   │   ├── main_app.py        # 主应用程序
│   │   ├── utils.py           # 工具函数
│   │   └── agent_executor.py  # Agent执行器
│   ├── processors/            # 各类处理器
│   │   ├── __init__.py
│   │   ├── audio_processor.py      # 音频处理(Whisper)
│   │   ├── multimodal_processor.py # 多模态处理器
│   │   └── media_generator.py      # 图像/视频生成
│   ├── services/              # 服务层
│   │   ├── __init__.py
│   │   ├── connection_manager.py   # 连接管理
│   │   ├── file_manager.py         # 文件管理
│   │   └── task_manager.py         # 任务管理
│   ├── gui/                   # GUI层
│   │   ├── __init__.py
│   │   ├── gui_controller.py  # GUI控制器
│   │   ├── gui_view.py        # GUI视图
│   │   ├── output_capture.py  # 输出捕获
│   │   └── styles.py          # 样式定义
│   ├── handlers/              # GUI事件处理器
│   │   ├── __init__.py
│   │   ├── connection_handler.py
│   │   ├── dynamic_handler.py
│   │   ├── system_handler.py
│   │   └── tts_handler.py
│   ├── managers/              # TTS管理模块
│   │   ├── __init__.py
│   │   ├── tts_audio.py
│   │   ├── tts_database.py
│   │   ├── tts_engine.py
│   │   ├── tts_text.py
│   │   └── gpt_sovits_custom/ # 自定义GPT-SoVITS模块
│   │       ├── __init__.py
│   │       ├── inference_webui.py
│   │       ├── t2s_model.py
│   │       └── t2s_lightning_module.py
│   ├── views/                 # GUI视图组件
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── dashboard.py
│   │   ├── dynamic.py
│   │   ├── history.py
│   │   ├── pages.py
│   │   ├── settings.py
│   │   ├── theme.py
│   │   └── tts.py
│   ├── agents/                # LangChain Agent模块
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── chat_agent.py
│   │   ├── judgement_agent.py
│   │   └── phone_agent.py
│   ├── chains/                # LangChain Chain模块
│   │   ├── __init__.py
│   │   ├── task_chain.py
│   │   └── reply_chain.py
│   ├── graphs/                # LangGraph 工作流模块
│   │   ├── __init__.py
│   │   ├── state.py           # 状态定义
│   │   ├── reply_graph.py     # 持续回复工作流
│   │   └── nodes/             # 工作流节点
│   │       ├── __init__.py
│   │       ├── extract.py     # 提取聊天记录
│   │       ├── parse.py       # 解析消息
│   │       ├── ownership.py   # 消息归属判断
│   │       ├── check_new.py   # 检查新消息
│   │       ├── reply.py       # 生成回复
│   │       ├── send.py        # 发送消息
│   │       ├── memory.py      # 更新记忆
│   │       └── control.py     # 流程控制
│   ├── models/                # 模型初始化模块
│   │   ├── __init__.py
│   │   └── zhipu_model.py
│   ├── prompts/               # 提示词模块
│   │   ├── __init__.py
│   │   ├── agent_executor_prompt.py
│   │   ├── chat_prompt.py
│   │   ├── judgement_prompt.py
│   │   ├── phone_prompt.py
│   │   └── reply_prompt.py
│   ├── tools/                 # 工具模块
│   │   ├── __init__.py
│   │   ├── chat_tools.py
│   │   ├── message_tools.py
│   │   ├── phone_tools.py
│   │   └── time_tool.py
│   ├── memory/                # 记忆模块
│   │   ├── __init__.py
│   │   └── conversation_memory.py
│   ├── callbacks/             # LangChain Callbacks 模块
│   │   ├── __init__.py
│   │   ├── streaming_handler.py   # 流式输出处理器
│   │   ├── logging_handler.py     # 日志记录处理器
│   │   ├── memory_handler.py      # 记忆管理处理器
│   │   └── callback_manager.py    # 回调管理器
│   └── __init__.py
├── phone_agent/               # 外部PhoneAgent模块
│   ├── agent.py
│   └── model/
│       └── client.py
├── forever.txt               # 永久记忆文件
├── main.py                   # 主入口
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

#### 3. 持续回复管理 (graphs/reply_graph.py)
- 使用 LangGraph 编排工作流，状态集中管理
- 节点化设计：提取→解析→归属判断→检查新消息→生成回复→发送→更新记忆
- 终止机制：支持中途停止持续回复，全局终止信号检测
- 消息归属判断：基于头像位置（左→对方，右→我方）和气泡颜色
- 相似度比对：避免重复回复
- 循环检测：每轮检查新消息，最多30轮，可配置递归限制

#### 4. TTS语音合成 (managers/)
- 集成 GPT-SoVITS 模型
- 支持分段合成（最大500字符/段）
- 并行合成提升效率
- 需要参考音频目录
- **自定义模块优化**：
  - 移除所有冗余print输出
  - 移除tqdm进度条
  - 使用环境变量配置路径
  - 降级机制确保稳定性

#### 5. 多模态处理
- GLM-4.6v-flash：文本、视频、图片、文件分析
- cogview-3-flash：文生图
- cogvideox-flash：文生视频、图生视频、首尾帧生视频
- 文件上传：支持10MB，多种格式

#### 6. 手机投屏
- 使用 scrcpy 实现
- 可视化操作过程
- 支持USB/无线连接

#### 7. LangChain Callbacks 系统 (callbacks/)
- **流式输出处理器** (StreamingCallbackHandler)
  - 实时捕获 LLM 生成的 token
  - 支持打字机效果输出到 GUI
  - Qt 信号机制实现线程安全更新
- **日志记录处理器** (LoggingCallbackHandler)
  - 自动记录所有 LLM 调用详情
  - 按日期分割日志文件 (`temp/log/langchain_callbacks_YYYY-MM-DD.log`)
  - 记录 Token 使用量、耗时、错误信息
  - 支持性能监控 (PerformanceCallbackHandler)
- **记忆管理处理器** (MemoryCallbackHandler)
  - 自动保存对话历史
  - 支持会话级和文件级记忆管理
- **回调管理器** (CallbackManager)
  - 统一管理所有回调处理器
  - 支持全局和局部回调注册
  - 自动去重防止重复调用
  - 简化回调配置流程

### 🔧 技术栈

| 组件 | 技术 |
|------|------|
| GUI | PyQt6 |
| AI模型 | 智谱AI GLM-4.6v-flash, autoglm-phone, cogview-3-flash, cogvideox-flash |
| 工作流 | LangGraph + LangChain |
| TTS | GPT-SoVITS |
| 手机控制 | ADB (Android) / HDC (HarmonyOS) + scrcpy |
| SDK | zhipuai, openai |
| 音频处理 | Whisper, PyAudio, soundfile |
| 图像处理 | Pillow, torch |

### ⚙️ 关键配置

```python
# .env,只有ZHIPU_API_KEY是必填的
GPT_SOVITS_ROOT = r"GPT-SoVITS实际根目录"
SCRCPY_PATH = r"scrcpy实际根目录"
ZHIPU_API_KEY = "替换为你的API key"
FFMPEG_PATH = r"FFmpeg实际根目录"
FOREVER_MEMORY_FILE = r"自定义记忆文件(forever.txt)路径"
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

1. **消息相似度算法**：LCS算法避免重复回复
2. **线程安全设计**：多线程环境下使用锁保护状态
3. **模块化重构**：TTS、GUI、业务逻辑分离
4. **配置验证机制**：启动时自动检查路径有效性
5. **持久化记忆**：forever.txt手动维护，conversation_history.json自动记录
6. **TTS输出优化**：自定义GPT-SoVITS模块，移除冗余输出，提升用户体验

### ⚠️ 配置要求

1. GPT-SoVITS根目录需手动创建"参考音频"文件夹
2. AI模型需按智谱官方文档部署环境
3. transformers依赖冲突可忽略
4. openai包版本需注意兼容性

### 📈 版本演进亮点

- v1.0: 基础CLI版
- v1.1: 集成TTS、GUI、投屏
- v1.2: 升级GLM-4.6v-flash多模态、引入双AI辅助系统
- v1.3: 使用 LangGraph 重构持续回复流程，状态集中管理，节点化设计

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
