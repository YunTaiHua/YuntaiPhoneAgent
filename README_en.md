Phone Agent Pro - Intelligent Multi-Modal Control Agent

Version: 1.2.6

## Phone Agent Intelligent Edition v1.2.6 Code Analysis

### 📊 Project Overview

**Project Name**: Phone Agent Intelligent Edition  
**Version**: v1.2.6 (759st iteration)

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
├── yuntai/  # Core modules
│   ├── __init__.py
│   ├── agent_core.py  # Agent core
│   ├── agent_executor.py  # Executor
│   ├── audio_processor.py  # Audio processing
│   ├── config.py  # Configuration
│   ├── connection_manager.py  # Connection management
│   ├── file_manager.py  # File management
│   ├── gui_controller.py  # GUI controller
│   ├── gui_view.py  # GUI view
│   ├── main_app.py  # Main app
│   ├── multimodal_other.py  # Multimodal other
│   ├── multimodal_processor.py  # Multimodal processor
│   ├── output_capture.py  # Output capture
│   ├── reply_manager.py  # Reply manager
│   ├── task_manager.py  # Task manager
│   ├── task_recognizer.py  # Task recognizer
│   └── utils.py  # Utilities
├── scripts/  # Scripts and sample messages
│   ├── check_deployment_cn.py
│   ├── check_deployment_en.py
│   ├── sample_messages.json
│   └── sample_messages_en.json
├── resources/  # Resource files (images, docs, etc.)
│   ├── logo.svg
│   ├── privacy_policy.txt
│   ├── privacy_policy_en.txt
│   ├── screenshot-20251209-181423.png
│   ├── screenshot-20251210-120416.png
│   ├── screenshot-20251210-120630.png
│   ├── setting.png
│   ├── wechat.jpeg
│   └── WECHAT.md
├── requirements/  # Dependencies and installation files
│   ├── dev_requirements.txt
│   ├── environment.yml
│   ├── install_guide.txt
│   ├── optional_requirements.txt
│   ├── quick_install.bat
│   ├── requirements.txt
│   ├── tts_requirements.txt
│   ├── version_check.py
│   └── windows_requirements.txt
├── phone_agent/  # Agent modules
│   ├── agent.py
│   └── model/
│       └── client.py
├── examples/  # Example code
│   ├── __init__.py
│   ├── basic_usage.py
│   └── demo_thinking.py
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE
├── README.md
├── __init__.py
├── forever.txt
├── main.py  # Main entry
├── requirements.txt
└── setup.py
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
GPT_SOVITS_ROOT = r"..."
SCRCPY_PATH = r"..."
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

## 🚀 Usage

### Prerequisites

#### 1. Python Environment
Python 3.10 or higher is required.

#### 2. ADB (Android Debug Bridge)
1. Download the official ADB [installation package](https://developer.android.com/tools/releases/platform-tools)
2. Extract and configure environment variables (add to PATH on Windows).

#### 3. Android Device Setup
- Android 7.0+ device or emulator
- Developer Mode and USB Debugging enabled
- Install ADB Keyboard APK

#### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### Running the Program

#### Command Line
```bash
# Interactive mode
python main.py --base-url <MODEL_API_URL> --model <MODEL_NAME>

# Execute specific task
python main.py --base-url <MODEL_API_URL> "Open Chrome browser"

# Use API key authentication
python main.py --apikey YOUR_API_KEY

# Specify device
python main.py --device-id 192.168.1.100:5555 --base-url <MODEL_API_URL> "Open TikTok"
```

#### Python API
```python
from phone_agent import PhoneAgent
from phone_agent.model import ModelConfig

# Configure model
model_config = ModelConfig(
    base_url="<MODEL_API_URL>",
    model_name="<MODEL_NAME>",
)

# Create Agent
agent = PhoneAgent(model_config=model_config)

# Execute task
result = agent.run("Open eBay and search for wireless earbuds")
print(result)
```

### Environment Variables
| Variable                  | Description               | Default                      |
|---------------------------|---------------------------|------------------------------|
| `PHONE_AGENT_BASE_URL`    | Model API URL             | `http://localhost:8000/v1`   |
| `PHONE_AGENT_MODEL`       | Model name                | `autoglm-phone-9b`           |
| `PHONE_AGENT_API_KEY`     | API key                   | `EMPTY`                      |
| `PHONE_AGENT_MAX_STEPS`   | Max steps per task        | `100`                        |
| `PHONE_AGENT_DEVICE_ID`   | ADB device ID             | (auto-detect)                |
| `PHONE_AGENT_LANG`        | Language (`cn`/`en`)      | `cn`                         |

### Troubleshooting
- Device not found: Check USB debugging and cable
- Cannot tap: Enable USB Debugging (Security Settings)
- Text input not working: Ensure ADB Keyboard is installed and enabled
