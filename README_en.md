Phone Agent Pro - Intelligent Multi-Modal Control Agent

Version: 1.2.4

## Phone Agent Intelligent Edition v1.2.4 Code Analysis

### 📊 Project Overview

**Project Name**: Phone Agent Intelligent Edition  
**Version**: v1.2.4 (721st iteration)

### 🏗️ Architecture Design

#### Core AI System Architecture
```
┌─────────────────────────────────────────┐
│         Dual AI Collaboration System    │
├─────────────────────────────────────────┤
│  GLM-4.6v-flash    autoglm-phone        │
│  (Decision Layer)  (Execution Layer)    │
└─────────────────────────────────────────┘
         ↓                   ↓
    ┌──────────────────────────────────────┐
    │     Dual AI Assistant System          │
    ├──────────────────────────────────────┤
    │  cogview-3-flash  cogvideox-flash    │
    │  (Text-to-Image)  (Video Generation) │
    └──────────────────────────────────────┘
```

#### Directory Structure
```
YuntaiPhoneAgent/
├── phone_agent/        # Core phone operation agent
│   ├── agent.py        # PhoneAgent main class
│   ├── actions/        # Operation handlers
│   ├── adb/           # ADB connection and operations
│   ├── config/        # Configuration and prompts
│   └── model/         # AI model clients
├── yun/               # Refactored business logic module
│   ├── agent_core.py   # Intelligent agent core
│   ├── task_manager.py # Task scheduling management
│   ├── gui_controller.py # GUI controller
│   ├── gui_view.py     # GUI view
│   └── multimodal_*.py # Multimodal processing
├── yuntai/            # Original business logic
│   ├── agent_executor.py
│   ├── connection_manager.py
│   └── reply_manager.py
└── main.py            # Program entry point
```

### 🎯 Core Function Modules

#### 1. Intelligent Task Recognition (task_recognizer.py)
- Automatically determine task type (free chat, phone operation, single/continuous reply, complex operation)
- Support shortcut keys to quickly launch apps (WeChat, QQ, TikTok, etc.)

#### 2. Phone Automation (phone_agent/agent.py:43-256)
- Use VLM to understand screen content and decide operations
- Support various operations: tap, input, swipe, long press, double tap, back, home
- Coordinate system: (0,0) top-left → (999,999) bottom-right

#### 3. Continuous Reply Management (agent_core.py)
- Termination mechanism: Support stopping continuous reply midway
- Message attribution judgment: Based on avatar position (left→other party, right→me) and bubble color
- Similarity comparison: Use longest common subsequence algorithm to avoid duplicate replies
- Loop detection: Check for new messages each round, maximum 30 rounds

#### 4. TTS Speech Synthesis (task_manager.py:53-100)
- Integrate GPT-SoVITS model
- Support segmented synthesis (maximum 500 characters/segment)
- Parallel synthesis for efficiency
- Requires reference audio directory

#### 5. Multimodal Processing
- GLM-4.6v-flash: Text, video, image, file analysis
- cogview-3-flash: Text-to-image
- cogvideox-flash: Text-to-video, image-to-video, start/end frame to video
- File upload: Support 10MB, multiple formats

#### 6. Phone Screen Mirroring
- Implemented using scrcpy
- Visualize operation process
- Support USB/wireless connection

### 🔧 Technology Stack

| Component | Technology |
|-----------|------------|
| GUI | tkinter + customtkinter |
| AI Models | Zhipu AI GLM-4.6v-flash, autoglm-phone, cogview-3-flash, cogvideox-flash |
| TTS | GPT-SoVITS |
| Phone Control | ADB + scrcpy |
| SDK | zhipuai, openai |

### ⚙️ Key Configuration

```python
# yun/config.py:17-59
GPT_SOVITS_ROOT = r"E:\PyCode\GPT-SoVITS-main"
SCRCPY_PATH = r"E:\scrcpy\scrcpy-win64-v3.3.4\..."
ZHIPU_API_KEY = "Replace with your API key"
MAX_CYCLE_TIMES = 30
WAIT_INTERVAL = 1 s
MAX_FILE_SIZE = 10 MB
```

### 🔄 Dual AI Collaboration Process

```
User Instruction
    ↓
GLM-4.6v-flash (Task Classification)
    ↓
┌───────────┬──────────┬──────────┬──────────┐
│Free Chat   │Phone Op   │Single Reply│Cont Reply │Complex Op
└─────┬─────┴─────┬────┴────┬─────┴─────┬────
      ↓           ↓        ↓          ↓
  GLM-4.6v   autoglm   Extract Record→GLM   Loop Extract→GLM
  Direct Resp Execute Op   →Reply→Send     →Check New Msg
```

### 💡 Featured Functions

1. **Intelligent Color Output**: Gold (GLM-4), Green (phone_agent), Blue (result) [GUI version does not support color function]
2. **Message Similarity Algorithm**: LCS algorithm to avoid duplicate replies
3. **Thread-Safe Design**: Use locks to protect state in multi-threaded environment
4. **Modular Refactoring**: TTS, GUI, business logic separation
5. **Configuration Validation Mechanism**: Automatically check path validity at startup
6. **Persistent Memory**: forever.txt manual maintenance, conversation_history.json automatic recording

### ⚠️ Configuration Requirements

1. GPT-SoVITS root directory needs to manually create "Reference Audio" folder
2. AI models need to deploy environment according to Zhipu official documentation
3. transformers dependency conflicts can be ignored
4. openai package version needs to pay attention to compatibility

### 📈 Version Evolution Highlights

- v1.0: Basic CLI version
- v1.1: Integrated TTS, GUI, screen mirroring
- v1.2: Upgraded GLM-4.6v-flash multimodal, introduced dual AI assistant system

The project demonstrates the deep integration of AI Agent, multimodal, and automation technologies, and is a fully functional smartphone operation proxy system.
