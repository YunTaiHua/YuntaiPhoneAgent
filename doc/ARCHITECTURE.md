# YuntaiPhoneAgent 技术架构文档

## 1. 系统概述

### 1.1 项目定位

YuntaiPhoneAgent 是一个智能移动助手项目，支持 GUI 和 Web 两种入口，使用 LangChain 和 LangGraph 构建 AI Agent 系统，实现了手机操作、智能聊天、消息回复等功能。

### 1.2 核心功能
- **自由聊天**: 与 AI 助手进行自然语言对话
- **手机操作**: 通过 ADB/HDC 控行手机自动化操作
- **消息回复**: 自动提取聊天记录并生成回复
- **多模态处理**: 支持文本、图片、视频、文档等多种输入
- **语音合成**: TTS 语音播报功能

### 1.3 技术栈
- **语言**: Python 3.10+
- **GUI 框架**: PyQt6
- **Web 框架**: FastAPI + Uvicorn
- **AI 框架**: LangChain + LangGraph
- **模型服务**: 智谱 AI (GLM-4.6v-flash, autoglm-phone)
- **设备控制**: ADB (Android) / HDC (HarmonyOS)

- **语音合成**: GPT-SoVITS

---

## 2. 项目结构

```
YuntaiPhoneAgent/
├── main.py              # GUI 入口
├── main_web.py          # Web 入口
├── phone_agent/          # 手机操作核心库（不修改）
│   ├── actions/         # 操作处理
│   ├── adb/             # ADB 连接
│   ├── config/           # 配置
│   ├── hdc/             # HDC 连接
│   ├── model/            # 模型封装
│   └── xctest/           # iOS 支持
├── yuntai/
│   ├── agents/          # Agent 模块
│   │   ├── base_agent.py        # Agent 基类
│   │   ├── chat_agent.py        # 聊天 Agent
│   │   ├── judgement_agent.py   # 任务判断 Agent
│   │   └── phone_agent.py        # 手机操作 Agent
│   ├── callbacks/        # LangChain Callbacks
│   │   ├── callback_manager.py  # 回调管理器
│   │   ├── logging_handler.py   # 日志处理器
│   │   ├── memory_handler.py    # 记忆处理器
│   │   └── streaming_handler.py # 流式处理器
│   ├── chains/           # LangChain Chains
│   │   ├── reply_chain.py      # 回复处理链
│   │   └── task_chain.py       # 任务处理链
│   ├── core/             # 核心模块
│   │   ├── agent_executor.py   # Agent 执行器
│   │   ├── config.py           # 配置管理
│   │   ├── main_app.py         # 主应用
│   │   └── utils.py            # 工具函数
│   ├── graphs/           # LangGraph 工作流
│   │   ├── nodes/              # 工作流节点
│   │   │   ├── check_new.py    # 检查新消息
│   │   │   ├── control.py       # 流程控制
│   │   │   ├── extract.py      # 提取记录
│   │   │   ├── memory.py       # 更新记忆
│   │   │   ├── ownership.py    # 消息归属
│   │   │   ├── parse.py        # 解析消息
│   │   │   ├── reply.py        # 生成回复
│   │   │   └── send.py         # 发送消息
│   │   ├── reply_graph.py      # 回复工作流
│   │   └── state.py             # 状态定义
│   ├── gui/              # GUI 组件
│   │   ├── gui_controller.py  # GUI 控制器
│   │   ├── gui_view.py         # GUI 视图
│   │   ├── output_capture.py   # 输出捕获
│   │   └── styles.py           # 样式定义
│   ├── handlers/         # 事件处理器
│   ├── managers/         # 管理器
│   │   ├── tts_audio.py       # TTS 音频
│   │   ├── tts_database.py    # TTS 数据库
│   │   ├── tts_engine.py      # TTS 引擎
│   │   └── tts_text.py        # TTS 文本
│   ├── memory/          # 记忆管理
│   ├── models/           # 模型封装
│   ├── processors/        # 处理器
│   ├── prompts/          # 提示词
│   │   ├── __init__.py           # 模块导出
│   │   ├── agent_executor_prompt.py  # Agent 执行器提示词
│   │   ├── chat_prompt.py         # 聊天提示词
│   │   ├── judgement_prompt.py    # 任务判断提示词
│   │   ├── parse_prompt.py       # 消息解析提示词
│   │   ├── phone_prompt.py       # 手机操作提示词
│   │   └── reply_prompt.py       # 回复生成提示词
│   ├── services/         # 服务层
│   │   ├── connection_manager.py  # 连接管理
│   │   ├── file_manager.py       # 文件管理
│   │   └── task_manager.py       # 任务管理
│   ├── tools/            # 工具函数
│   │   ├── chat_tools.py        # 聊天工具
│   │   ├── message_tools.py     # 消息工具
│   │   ├── phone_tools.py       # 手机工具
│   │   └── time_tool.py         # 时间工具
│   └── views/            # 视图层
├── web/                # Web 模块
│   ├── core/
│   │   ├── handlers/         # 请求处理器
│   │   ├── controller.py      # Web 控制器
│   │   ├── output_capture.py  # 输出捕获
│   │   ├── routes.py           # 路由定义
│   │   └── ws_manager.py       # WebSocket 管理
│   └── static/              # 静态资源
└── doc/                # 文档目录
    ├── PLAN.md            # 重构计划
    ├── CHANGELOG.md       # 更新日志
    └── ARCHITECTURE.md    # 技术架构（本文件）
```

---

## 3. LangChain 架构

### 3.1 Chains (链)

| Chain | 文件 | 功能 |
|-------|------|------|
| TaskChain | chains/task_chain.py | 任务处理链，整合判断→分发→执行流程 |
| ReplyChain | chains/reply_chain.py | 回复处理链，使用 LangGraph 工作流 |

#### TaskChain 流程
```
用户输入
    ↓
JudgementAgent.judge() → 判断任务类型
    ↓
┌─────────────────────────────────────────┐
│ free_chat → ChatAgent.chat()            │
│ basic_operation → PhoneAgent.open_app() │
│ single_reply → ReplyChain.single_reply()│
│ continuous_reply → ReplyGraph.run()     │
│ complex_operation → PhoneAgent.execute()│
└─────────────────────────────────────────┘
```

#### ReplyChain 流程
```
单次回复:
PhoneAgent.extract_chat_records() → ChatAgent.chat() → PhoneAgent.send_message()

持续回复:
ReplyGraph.run() → LangGraph 工作流
```

### 3.2 Agents (智能体)

| Agent | 文件 | 功能 |
|-------|------|------|
| BaseAgent | agents/base_agent.py | Agent 基类，定义抽象接口 |
| ChatAgent | agents/chat_agent.py | 自由聊天，支持流式输出和记忆管理 |
| JudgementAgent | agents/judgement_agent.py | 任务判断，识别用户意图并分类 |
| PhoneAgent | agents/phone_agent.py | 手机操作，执行 ADB/HDC 命令 |

### 3.3 Callbacks (回调)

| Callback | 文件 | 功能 |
|----------|------|------|
| StreamingCallbackHandler | callbacks/streaming_handler.py | 流式输出，支持打字机效果 |
| QtStreamingCallbackHandler | callbacks/streaming_handler.py | Qt 信号流式输出 |
| AsyncStreamingCallbackHandler | callbacks/streaming_handler.py | 异步流式输出 |
| LoggingCallbackHandler | callbacks/logging_handler.py | 日志记录 |
| PerformanceCallbackHandler | callbacks/logging_handler.py | 性能监控 |
| MemoryCallbackHandler | callbacks/memory_handler.py | 记忆管理 |
| SessionMemoryCallbackHandler | callbacks/memory_handler.py | 会话记忆 |
| FileBasedMemoryCallbackHandler | callbacks/memory_handler.py | 文件记忆 |
| CallbackManager | callbacks/callback_manager.py | 回调管理器，统一管理所有回调 |

---

## 4. LangGraph 架构

### 4.1 Graphs (图)

| Graph | 文件 | 功能 |
|-------|------|------|
| ReplyGraph | graphs/reply_graph.py | 持续回复工作流 |

### 4.2 State (状态)

```python
class ReplyState(TypedDict):
    # 基本信息
    app_name: str
    chat_object: str
    device_id: str
    
    # 循环控制
    cycle_count: int
    max_cycles: int
    should_continue: bool
    terminate_flag: bool
    
    # 消息解析
    extracted_records: str
    parse_success: bool
    parsed_messages: list[dict[str, str]]
    
    # 消息记录
    other_messages: Annotated[list[str], merge_lists]
    my_messages: Annotated[list[str], merge_lists]
    
    # 回复生成
    generated_reply: str
    send_success: bool
    ...
```

### 4.3 Nodes (节点)

| Node | 文件 | 输入 | 输出 | 功能 |
|------|------|------|------|------|
| extract_records | nodes/extract.py | app_name, chat_object, device_id | extracted_records | 提取聊天记录 |
| parse_messages | nodes/parse.py | extracted_records | parsed_messages | 解析消息结构 |
| determine_ownership | nodes/ownership.py | parsed_messages | current_other_messages, current_my_messages | 判断消息归属 |
| check_new_message | nodes/check_new.py | current_other_messages | is_new_message, latest_message | 检查是否有新消息 |
| generate_reply | nodes/reply.py | latest_message | generated_reply | 生成回复内容 |
| send_message | nodes/send.py | generated_reply | send_success | 发送消息 |
| update_memory | nodes/memory.py | send_success | last_sent_reply | 更新记忆和日志 |
| do_wait | nodes/control.py | wait_seconds | - | 等待指定时间 |
| check_continue | nodes/control.py | cycle_count | should_continue | 检查是否继续循环 |

### 4.4 工作流图

```
                    ┌─────────────────────────────────────────────────────────────┐
                    │                                                                 │
                    ▼                                                                 │
              [extract] → [parse] → [ownership] → [check_new]                              │
                                                          │                              │
                                              ┌───────────┴───────────┐                  │
                                              │                           │                  │
                                              ▼                           ▼                  │
                                          [reply]                     [wait]              │
                                              │                           │                  │
                                              │                           │                  │
                                              ▼                           │                  │
                                          [send]                         │                  │
                                              │                           │                  │
                                              ▼                           │                  │
                                        [memory]                         │                  │
                                              │                           │                  │
                                              └───────────┬───────────────┘                  │
                                                          │                                  │
                                                          ▼                                  │
                                                    [check_continue] ◄────────────────────┘
                                                          │
                                              ┌───────────┴───────────┐
                                              │                           │
                                              ▼                           ▼
                                        [continue]                   [END]
                                              │
                                              └──→ [extract] (循环)
```

---

## 5. 程序运行流程

### 5.1 GUI 启动流程

```
main.py
    │
    ▼
MainApp.__init__()
    ├── validate_config()        # 验证配置
    ├── print_config_summary()  # 打印配置摘要
    ├── QApplication()           # 创建 Qt 应用
    ├── GUIController()          # 创建 GUI 控制器
    │   ├── FileManager()        # 文件管理器
    │   ├── TTSManager()         # TTS 管理器
    │   ├── TaskChain()          # 任务处理链
    │   └── ReplyChain()         # 回复处理链
    └── view.show()              # 显示主窗口
```

### 5.2 Web 启动流程

```
main_web.py
    │
    ▼
FastAPI app
    ├── CORSMiddleware        # 跨域中间件
    ├── ConnectionManager()    # WebSocket 管理器
    ├── WebController()        # Web 控制器
    └── uvicorn.run()          # 启动服务器
        ├── localhost:8000      # 本地访问
        └── {local_ip}:8000     # 局域网访问
```

### 5.3 任务处理流程

```
用户输入
    │
    ▼
TaskChain.process()
    │
    ├── 检查快捷键
    │   └── 单字母 → 打开对应 APP
    │
    ▼
JudgementAgent.judge()
    │
    ├── 分析用户意图
    ├── 提取关键信息
    └── 返回任务类型
    │
    ▼
任务分发
    │
    ├── free_chat
    │   └── ChatAgent.chat()
    │       ├── 加载记忆
    │       ├── 构建提示词
    │       └── 流式输出
    │
    ├── basic_operation
    │   └── PhoneAgent.open_app()
    │
    ├── single_reply
    │   └── ReplyChain.single_reply()
    │       ├── 提取聊天记录
    │       ├── 解析消息
    │       ├── 生成回复
    │       └── 发送消息
    │
    ├── continuous_reply
    │   └── ReplyGraph.run()
    │       └── LangGraph 工作流循环
    │
    └── complex_operation
        └── PhoneAgent.execute()
```

### 5.4 持续回复流程

```
ReplyGraph.run()
    │
    ▼
初始化状态
    │
    ▼
循环开始
    │
    ├── extract_records        # 提取聊天记录
    │   └── PhoneAgent.extract_chat_records()
    │
    ├── parse_messages          # 解析消息
    │   └── 使用 AI 提取结构化数据
    │
    ├── determine_ownership     # 判断归属
    │   └── 根据头像位置和颜色判断
    │
    ├── check_new_message       # 检查新消息
    │   └── 与已知消息对比
    │
    ├── [有新消息?]
    │   ├── Yes → generate_reply  # 生成回复
    │   │           └── send_message      # 发送消息
    │   │                   └── update_memory  # 更新记忆
    │   │
    │   └── No → do_wait           # 等待
    │
    ├── check_continue          # 检查是否继续
    │   ├── 继续循环 → 返回 extract_records
    │   └── 终止 → END
    │
    └── [循环结束]
```

---

## 6. 模型配置

| 用途 | 模型 | 配置变量 | 说明 |
|------|------|---------|------|
| 手机操作 | autoglm-phone | ZHIPU_MODEL | 专用手机操作模型 |
| 聊天 | glm-4.6v-flash | ZHIPU_CHAT_MODEL | 多模态聊天模型 |
| 任务判断 | glm-4.6v-flash | ZHIPU_JUDGEMENT_MODEL | 任务分类模型 |
| 多模态 | glm-4.6v-flash | ZHIPU_MULTIMODAL_MODEL | 多模态处理 |
| 图像生成 | cogview-3-flash | ZHIPU_IMAGE_MODEL | 文生图 |
| 视频生成 | cogvideox-flash | ZHIPU_VIDEO_MODEL | 文生视频/图生视频 |

---

## 7. 服务模块

### 7.1 ConnectionManager
- 设备连接管理 (USB/无线)
- 支持 Android (ADB) 和 HarmonyOS (HDC)
- 连接配置持久化

### 7.2 FileManager
- 文件系统初始化
- 对话历史管理 (JSON 格式)
- 永久记忆管理 (forever.txt)
- 聊天记录日志

### 7.3 TTSManager
- TTS 模块加载 (GPT-SoVITS)
- 语音合成 (文本转语音)
- 音频播放管理
- 分段合成优化

---

## 8. 配置管理

### 8.1 环境变量 (.env)
```env
ZHIPU_API_KEY=your_api_key
GPT_SOVITS_ROOT=/path/to/gpt-sovits
SCRCPY_PATH=/path/to/scrcpy
FFMPEG_PATH=/path/to/ffmpeg
FOREVER_MEMORY_FILE=/path/to/forever.txt
PHONE_AGENT_DEVICE_TYPE=android
```

### 8.2 配置模块 (yuntai/core/config.py)
- 路径配置: 统一使用 pathlib
- 模型配置: API 密钥和模型名称
- 功能配置: TTS 参数、快捷键映射
- 验证函数: 配置有效性检查

---

## 9. 提示词管理

### 9.1 提示词文件结构
```
prompts/
├── __init__.py              # 模块导出
├── agent_executor_prompt.py  # Agent 执行器提示词
├── chat_prompt.py            # 聊天提示词
├── judgement_prompt.py       # 任务判断提示词
├── parse_prompt.py           # 消息解析提示词
├── phone_prompt.py           # 手机操作提示词
└── reply_prompt.py           # 回复生成提示词
```

### 9.2 提示词使用原则
1. 所有提示词集中在 `prompts` 目录
2. 使用常量定义，便于维护和修改
3. 支持格式化参数 (使用 `{param}` 语法)
4. 保持风格一致 (Google 风格文档字符串)

---

## 10. 扩展指南

### 10.1 添加新的 Agent
1. 在 `agents/` 目录创建新文件
2. 继承 `BaseAgent` 类
3. 实现 `invoke` 方法
4. 在 `agents/__init__.py` 中导出

### 10.2 添加新的 Chain
1. 在 `chains/` 目录创建新文件
2. 使用 LangChain 的 Chain 模式
3. 在 `chains/__init__.py` 中导出

### 10.3 添加新的 Graph Node
1. 在 `graphs/nodes/` 目录创建新文件
2. 定义节点函数，接收和返回状态字典
3. 在 `graphs/nodes/__init__.py` 中导出
4. 在对应的 Graph 中添加节点和边

---

*文档创建时间: 2026-03-26*
