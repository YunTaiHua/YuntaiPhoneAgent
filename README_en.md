# YuntaiPhoneAgent

Version: 1.3.2

**[中文版本](README.md)**

## YuntaiPhoneAgent v1.3.2 Code Analysis

### 📊 Project Overview

**Project Name**: YuntaiPhoneAgent 
**Version**: v1.3.2

### 🏗️ Architecture Design

#### Core AI System Architecture
```
┌─────────────────────────────────────────┐
│         Dual AI Collaboration System    │
├─────────────────────────────────────────┤
│  GLM-4.6v-flash    autoglm-phone        │
│  (Decision Layer)   (Execution Layer)   │
└─────────────────────────────────────────┘
         ↓                   ↓
    ┌──────────────────────────────────────┐
    │     Dual AI Assist System            │
    ├──────────────────────────────────────┤
    │  cogview-3-flash  cogvideox-flash    │
    │  (Image Gen)        (Video Gen)      │
    └──────────────────────────────────────┘
```

#### Directory Structure
```
YuntaiPhoneAgent/
├── yuntai/                    # Core Module
│   ├── core/                  # Core Infrastructure
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration Management
│   │   ├── main_app.py        # Main Application
│   │   ├── utils.py           # Utility Functions
│   │   └── agent_executor.py  # Agent Executor
│   ├── processors/            # Processors
│   │   ├── __init__.py
│   │   ├── audio_processor.py      # Audio Processing (Whisper)
│   │   ├── multimodal_processor.py # Multimodal Processor
│   │   └── multimodal_other.py     # Image/Video Generation
│   ├── services/              # Service Layer
│   │   ├── __init__.py
│   │   ├── connection_manager.py   # Connection Management
│   │   ├── file_manager.py         # File Management
│   │   └── task_manager.py         # Task Management
│   ├── gui/                   # GUI Layer
│   │   ├── __init__.py
│   │   ├── gui_controller.py  # GUI Controller
│   │   ├── gui_view.py        # GUI View
│   │   ├── output_capture.py  # Output Capture
│   │   └── styles.py          # Styles
│   ├── handlers/              # GUI Event Handlers
│   │   ├── __init__.py
│   │   ├── connection_handler.py
│   │   ├── dynamic_handler.py
│   │   ├── system_handler.py
│   │   └── tts_handler.py
│   ├── managers/              # TTS Management Module
│   │   ├── __init__.py
│   │   ├── tts_audio.py
│   │   ├── tts_database.py
│   │   ├── tts_engine.py
│   │   └── tts_text.py
│   ├── views/                 # GUI View Components
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── dashboard.py
│   │   ├── dynamic.py
│   │   ├── history.py
│   │   ├── pages.py
│   │   ├── settings.py
│   │   ├── theme.py
│   │   └── tts.py
│   ├── agents/                # LangChain Agent Module
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── chat_agent.py
│   │   ├── judgement_agent.py
│   │   └── phone_agent.py
│   ├── chains/                # LangChain Chain Module
│   │   ├── __init__.py
│   │   ├── task_chain.py
│   │   └── reply_chain.py
│   ├── graphs/                # LangGraph Workflow Module
│   │   ├── __init__.py
│   │   ├── state.py           # State Definition
│   │   ├── reply_graph.py     # Continuous Reply Workflow
│   │   └── nodes/             # Workflow Nodes
│   │       ├── __init__.py
│   │       ├── extract.py     # Extract Chat Records
│   │       ├── parse.py       # Parse Messages
│   │       ├── ownership.py   # Message Ownership
│   │       ├── check_new.py   # Check New Messages
│   │       ├── reply.py       # Generate Reply
│   │       ├── send.py        # Send Message
│   │       ├── memory.py      # Update Memory
│   │       └── control.py     # Flow Control
│   ├── models/                # Model Initialization Module
│   │   ├── __init__.py
│   │   └── zhipu_model.py
│   ├── prompts/               # Prompts Module
│   │   ├── __init__.py
│   │   ├── agent_executor_prompt.py
│   │   ├── chat_prompt.py
│   │   ├── judgement_prompt.py
│   │   ├── phone_prompt.py
│   │   └── reply_prompt.py
│   ├── tools/                 # Tools Module
│   │   ├── __init__.py
│   │   ├── chat_tools.py
│   │   ├── message_tools.py
│   │   ├── phone_tools.py
│   │   └── time_tool.py
│   ├── memory/                # Memory Module
│   │   ├── __init__.py
│   │   └── conversation_memory.py
│   └── __init__.py
├── phone_agent/               # External PhoneAgent Module
│   ├── agent.py
│   └── model/
│       └── client.py
├── __init__.py
├── forever.txt               # Permanent Memory File
├── main.py                   # Main Entry
├── requirements.txt
└── setup.py
```

### 🎯 Core Function Modules

#### 1. Intelligent Task Recognition (task_recognizer.py)
- Automatically judge task types (free chat, phone operation, single/continuous reply, complex operation)
- Support hotkeys to quickly launch applications (WeChat, QQ, Douyin, etc.)

#### 2. Phone Automation (phone_agent/agent.py)
- Use VLM to understand screen content and make operation decisions
- Support multiple operations: click, input, swipe, long press, double click, back, Home
- Coordinate system: (0,0) top-left → (999,999) bottom-right

#### 3. Continuous Reply Management (graphs/reply_graph.py)
- Use LangGraph to orchestrate workflow, centralized state management
- Node-based design: Extract→Parse→Ownership→Check New→Reply→Send→Update Memory
- Termination mechanism: support stopping continuous reply midway, global termination signal detection
- Message attribution judgment: based on avatar position (left→other, right→me) and bubble color
- Similarity comparison: avoid duplicate replies
- Loop detection: check new messages each round, maximum 30 rounds, configurable recursion limit

#### 4. TTS Voice Synthesis (task_manager.py)
- Integrate GPT-SoVITS model
- Support segment synthesis (max 500 characters/segment)
- Parallel synthesis for efficiency
- Requires reference audio directory

#### 5. Multimodal Processing
- GLM-4.6v-flash: text, video, image, file analysis
- cogview-3-flash: text to image
- cogvideox-flash: text to video, image to video, first-last frame to video
- File upload: support 10MB, multiple formats

#### 6. Phone Screen Casting
- Implemented using scrcpy
- Visualize operation process
- Support USB/wireless connection

### 🔧 Tech Stack

| Component | Technology |
|------|------|
| GUI | PyQt6 |
| AI Models | Zhipu AI GLM-4.6v-flash, autoglm-phone, cogview-3-flash, cogvideox-flash |
| Workflow | LangGraph + LangChain |
| TTS | GPT-SoVITS |
| Phone Control | ADB (Android) / HDC (HarmonyOS) + scrcpy |
| SDK | zhipuai, openai |
| Audio Processing | Whisper, PyAudio, soundfile |
| Image Processing | Pillow, torch |

### ⚙️ Key Configuration

```python
# .env,only ZHIPU_API_KEY is necessary
GPT_SOVITS_ROOT = r"GPT-SoVITS actual root directory"
SCRCPY_PATH = r"scrcpy actual root directory"
ZHIPU_API_KEY = "Replace with your API key"
FFMPEG_PATH = r"FFmpeg actual root directory" 
FOREVER_MEMORY_FILE = r"forever.txt（forever memory） actual root directory"
```

### 🔄 Dual AI Collaboration Flow

```
User Instruction
    ↓
GLM-4.6v-flash (Task Classification)
    ↓
┌───────────┬──────────┬──────────┬──────────┐
│Free Chat  │Phone Op  │Single R  │Continuous│Complex Op
└─────┬─────┴─────┬────┴────┬─────┴─────┬────
      ↓           ↓        ↓          ↓
   GLM-4.6v   autoglm   Extract→GLM   Loop Extract→GLM
   Response   Execute   →Reply→Send   →Judge New Msg
```

### 💡 Special Features

1. **Message Similarity Algorithm**: LCS algorithm to avoid duplicate replies
2. **Thread-Safe Design**: use locks to protect state in multi-threaded environment
3. **Modular Refactoring**: TTS, GUI, business logic separation
4. **Configuration Validation Mechanism**: automatically check path validity at startup
5. **Persistent Memory**: forever.txt manual maintenance, conversation_history.json automatic recording

### ⚠️ Configuration Requirements

1. GPT-SoVITS root directory needs manual creation of "参考音频" (Reference Audio) folder
2. AI models need to deploy environment according to Zhipu official documentation
3. transformers dependency conflicts can be ignored
4. openai package version needs attention to compatibility

### 📈 Version Evolution Highlights

- v1.0: Basic CLI version
- v1.1: Integrate TTS, GUI, screen casting
- v1.2: Upgrade GLM-4.6v-flash multimodal, introduce dual AI assist system
- v1.3: Refactor continuous reply flow with LangGraph, centralized state management, node-based design

This project demonstrates deep integration of AI Agent, multimodal, and automation technologies, making it a fully functional smartphone operation agent system.

## 🚀 Usage

### Environment Requirements

#### 1. Python Environment
Requires Python 3.10 or above.

#### 2. ADB (Android Debug Bridge)
1. Download official ADB [Installation Package](https://developer.android.com/tools/releases/platform-tools)
2. Extract and configure environment variables (Windows add to PATH).

#### 3. Android Device Configuration
- Android 7.0+ device or emulator
- Enable developer mode and USB debugging
- Install ADB Keyboard APK

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Program

#### Command Line
```bash
# After configuring .env, run the main program directly
python main.py 
```

### Environment Variables
| Variable                        | Description               | Default Value                        |
|---------------------------|------------------|----------------------------|
| `PHONE_AGENT_BASE_URL`    | Model API Address        | `http://localhost:8000/v1` |
| `PHONE_AGENT_MODEL`       | Model Name             | `autoglm-phone-9b`         |
| `PHONE_AGENT_API_KEY`     | API Key          | `EMPTY`                    |
| `PHONE_AGENT_MAX_STEPS`   | Max Steps Per Task         | `100`                      |
| `PHONE_AGENT_DEVICE_ID`   | ADB Device ID        | (Auto-detect)                     |
| `PHONE_AGENT_LANG`        | Language (`cn`/`en`)   | `cn`                       |

### FAQ
- Device not found: Check USB debugging and data cable
- Unable to click: Enable USB debugging (security settings)
- Text input not working: Ensure ADB Keyboard is installed and enabled
