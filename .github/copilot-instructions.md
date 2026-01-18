# Open-AutoGLM Phone Agent - AI Coding Assistant Instructions

## Project Overview
This is a multimodal phone automation framework that uses AutoGLM (a vision-language model) to understand Android screens and execute automated operations via ADB. The system provides both CLI and GUI interfaces for controlling Android devices through natural language commands.

## Architecture & Key Components

### Core Modules Structure
- **`yun/`**: Modern modular architecture (post v3.0)
  - `main_app.py`: Main application coordinator
  - `agent_core.py`: Core business logic for task processing and replies
  - `gui_controller.py`: GUI event handling and state management
  - `task_manager.py`: Task execution orchestration
  - `config.py`: Centralized configuration management

- **`yuntai/`**: Legacy phone agent core (pre v3.0)
  - `task_recognizer.py`: AI-powered task type classification
  - `reply_manager.py`: Message extraction and reply generation
  - `agent_executor.py`: ADB command execution
  - `connection_manager.py`: Device connection handling

### Task Recognition System
The system classifies user inputs into 5 task types using GLM-4:
1. **`free_chat`**: Pure conversation (e.g., "你好", "谢谢")
2. **`basic_operation`**: Simple app launching (e.g., "打开微信")
3. **`single_reply`**: One-time messaging without content (e.g., "给张三发消息")
4. **`continuous_reply`**: Auto-reply mode (contains "auto" keyword)
5. **`complex_operation`**: Complex tasks with specific content (e.g., "给张三发消息：你好呀")

## Critical Developer Workflows

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Configure ADB (essential for device control)
adb devices  # Verify connection
adb shell ime enable com.android.adbkeyboard/.AdbIME  # Enable keyboard
```

### Configuration Management
- **Paths**: Update `yun/config.py` with actual paths:
  - `GPT_SOVITS_ROOT`: Path to GPT-SoVITS installation
  - `SCRCPY_PATH`: Path to scrcpy executable
  - `ZHIPU_API_KEY`: Your API key for AutoGLM

- **External Dependencies**:
  - GPT-SoVITS for TTS functionality
  - scrcpy for screen mirroring
  - ADB Keyboard APK installed on device

### Running the Application
```bash
# From project root
python 智能助手3.1.8.py
```

## Project-Specific Patterns & Conventions

### Message Processing Logic
- **Avatar Position Detection**: Left avatar = incoming message, Right avatar = outgoing message
- **Color-Based Filtering**: Different bubble colors indicate message types
- **Similarity Checking**: Uses LCS algorithm to prevent duplicate message processing
- **Termination Handling**: Thread-safe termination flags for continuous operations

### ADB Command Patterns
```python
# Screen capture and analysis
adb exec-out screencap -p > screen.png
adb shell input tap X Y  # Touch coordinates
adb shell input text "message"  # Text input via ADB Keyboard
adb shell input keyevent 4  # Back button
```

### Configuration Access Pattern
```python
from yun.config import (
    PROJECT_ROOT, SCRCPY_PATH, GPT_SOVITS_ROOT,
    ZHIPU_API_KEY, ZHIPU_MODEL
)
```

### Error Handling Conventions
- Retry mechanisms with `MAX_RETRY_TIMES = 3`
- Graceful degradation when TTS/GPT-SoVITS unavailable
- Connection validation before operations

## Integration Points

### AutoGLM API Integration
- Uses OpenAI-compatible API format
- Multimodal input: screen images + text instructions
- Structured JSON responses for action planning

### GPT-SoVITS TTS Integration
- Directory switching required: `os.chdir(GPT_SOVITS_ROOT)`
- Model paths: `GPT_weights_v2Pro/`, `SoVITS_weights_v2Pro/`
- Reference audio from `参考音频/` directory

### Scrcpy Screen Mirroring
- External process management for screen streaming
- Window positioning and sizing handled by GUI controller

## Key Files for Understanding Architecture

- **`yun/main_app.py`**: Application lifecycle and component coordination
- **`yun/agent_core.py`**: Core task processing logic
- **`yuntai/task_recognizer.py`**: Task classification implementation
- **`yuntai/reply_manager.py`**: Message extraction algorithms
- **`yun/config.py`**: All configuration parameters and paths

## Common Development Tasks

### Adding New Task Types
1. Update `TASK_RECOGNITION_PROMPT` in `task_recognizer.py`
2. Add handling logic in `agent_core.py`
3. Update GUI controller if needed

### Modifying ADB Commands
- Test commands manually first: `adb shell input tap X Y`
- Use coordinate-based interactions over text selectors
- Always include keyboard dismissal: `input keyevent 4`

### Extending GUI Components
- Use `customtkinter` for consistent theming
- Follow MVC pattern: View (`gui_view.py`) ← Controller (`gui_controller.py`) → Model (`agent_core.py`)
- Thread operations for non-blocking UI updates

## Debugging Tips

### ADB Connection Issues
```bash
adb kill-server && adb start-server  # Restart ADB daemon
adb devices  # Check device list
adb shell getprop ro.product.model  # Verify device connection
```

### Screen Analysis Problems
- Verify screen capture: `adb exec-out screencap -p > test.png`
- Check image dimensions and quality
- Test AutoGLM API connectivity separately

### Message Extraction Issues
- Use `adb shell dumpsys window` to inspect UI hierarchy
- Test regex patterns on sample screen text
- Verify avatar position detection logic

Remember: This system requires physical Android device connection and proper ADB setup. Always test ADB commands manually before integrating into automation flows.