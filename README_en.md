Phone Agent Pro - Intelligent Multi-Modal Control Agent

Version: 1.2.8

**[中文版本](README.md)**

## Phone Agent Pro v1.2.8 Code Analysis

### 📊 Project Overview

**Project Name**: Phone Agent Pro  
**Version**: v1.2.8 (932nd iteration)

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
├── yuntai/  # Core Module
│   ├── handlers/ # Functions for GUI controller (gui_controller.py)
│   │      ├──__init__.py
│   │      ├──connection_handler.py
│   │      ├──dynamic_handler.py
│   │      ├──system_handler.py
│   │      └──tts_handler.py
│   ├── managers/ # Functions for task management (task_manager.py)
│   │      ├──__init__.py
│   │      ├──task_logic.py
│   │      ├──tts_audio.py
│   │      ├──tts_database.py
│   │      ├──tts_engine.py
│   │      └──tts_text.py
│   ├──views/ # Functions for GUI view (gui_view.py)
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
│   ├── agent_core.py  # Agent Core
│   ├── agent_executor.py  # Executor
│   ├── audio_processor.py  # Audio Processing
│   ├── config.py  # Configuration
│   ├── connection_manager.py  # Connection Management
│   ├── file_manager.py  # File Management
│   ├── gui_controller.py  # GUI Controller
│   ├── gui_view.py  # GUI View
│   ├── main_app.py  # Main Application
│   ├── multimodal_other.py  # Multimodal Others
│   ├── multimodal_processor.py  # Multimodal Processor
│   ├── output_capture.py  # Output Capture
│   ├── reply_manager.py  # Reply Management
│   ├── task_manager.py  # Task Management
│   ├── task_recognizer.py  # Task Recognition
│   └── utils.py  # Utility Functions
├── phone_agent/  # Agent Module
│   ├── agent.py
│   └── model/
│       └── client.py
├── __init__.py
├── forever.txt  # Can be created manually, fill absolute path in .env
├── main.py  # Main Entry
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

#### 3. Continuous Reply Management (agent_core.py)
- Termination mechanism: support stopping continuous reply midway
- Message attribution judgment: based on avatar position (left→other, right→me) and bubble color
- Similarity comparison: use longest common subsequence algorithm to avoid duplicate replies
- Loop detection: check new messages each round, maximum 30 rounds

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
| GUI | tkinter + customtkinter |
| AI Models | Zhipu AI GLM-4.6v-flash, autoglm-phone, cogview-3-flash, cogvideox-flash |
| TTS | GPT-SoVITS |
| Phone Control | ADB + scrcpy |
| SDK | zhipuai, openai |

### ⚙️ Key Configuration

```python
# yun/config.py:17-59
GPT_SOVITS_ROOT = r"GPT-SoVITS actual root directory"
SCRCPY_PATH = r"scrcpy actual root directory"
ZHIPU_API_KEY = "Replace with your API key"
MAX_CYCLE_TIMES = 30
WAIT_INTERVAL = 1 s
MAX_FILE_SIZE = 10 MB
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

1. **Smart Color Output**: Gold(GLM-4), Green(phone_agent), Blue(result)【No color support in GUI version】
2. **Message Similarity Algorithm**: LCS algorithm to avoid duplicate replies
3. **Thread-Safe Design**: use locks to protect state in multi-threaded environment
4. **Modular Refactoring**: TTS, GUI, business logic separation
5. **Configuration Validation Mechanism**: automatically check path validity at startup
6. **Persistent Memory**: forever.txt manual maintenance, conversation_history.json automatic recording

### ⚠️ Configuration Requirements

1. GPT-SoVITS root directory needs manual creation of "参考音频" (Reference Audio) folder
2. AI models need to deploy environment according to Zhipu official documentation
3. transformers dependency conflicts can be ignored
4. openai package version needs attention to compatibility

### 📈 Version Evolution Highlights

- v1.0: Basic CLI version
- v1.1: Integrate TTS, GUI, screen casting
- v1.2: Upgrade GLM-4.6v-flash multimodal, introduce dual AI assist system

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
