# YuntaiPhoneAgent 测试说明文档

## 目录结构

```
tests/
├── conftest.py                    # 共享测试fixtures和配置
├── __init__.py                    # 测试包初始化
├── test_agents/                   # Agent模块测试
│   ├── test_base_agent.py
│   ├── test_chat_agent.py
│   ├── test_judgement_agent.py
│   └── test_phone_agent.py
├── test_chains/                   # Chain模块测试
│   ├── test_reply_chain.py
│   └── test_task_chain.py
├── test_core/                     # 核心模块测试
│   ├── test_agent_executor.py
│   ├── test_config.py
│   ├── test_main_app.py
│   └── test_utils.py
├── test_graphs/                   # LangGraph工作流测试
│   ├── test_reply_graph.py
│   ├── test_state.py
│   └── test_nodes/                # 工作流节点测试
│       ├── test_check_new.py
│       ├── test_control.py
│       ├── test_extract.py
│       ├── test_memory.py
│       ├── test_ownership.py
│       ├── test_parse.py
│       ├── test_reply.py
│       └── test_send.py
├── test_gui/                      # GUI模块测试
│   ├── test_styles.py             # 样式模块测试
│   ├── test_output_capture.py     # 输出捕获测试
│   ├── test_gui_view.py           # 视图组件测试
│   ├── test_gui_controller.py     # 控制器测试
│   ├── test_views.py              # 页面构建器测试
│   └── test_handlers.py           # 事件处理器测试
├── test_integration/              # 集成测试
│   └── test_task_flow.py
├── test_managers/                 # 管理器测试
│   ├── test_tts_audio.py
│   ├── test_tts_database.py
│   ├── test_tts_engine.py
│   └── test_tts_text.py
├── test_memory/                   # 记忆模块测试
│   └── test_conversation_memory.py
├── test_models/                   # 模型测试
│   └── test_zhipu_model.py
├── test_processors/               # 处理器测试
│   ├── test_audio_processor.py
│   └── test_multimodal_processor.py
├── test_prompts/                  # 提示词测试
│   └── test_prompts.py
├── test_services/                 # 服务层测试
│   ├── test_connection_manager.py
│   └── test_file_manager.py
└── test_tools/                    # 工具测试
    ├── test_chat_tools.py
    ├── test_message_tools.py
    ├── test_phone_tools.py
    └── test_time_tool.py
```

## 运行测试

### 基本命令

```bash
# 运行所有测试
pytest

# 运行指定目录的测试
pytest tests/test_gui/

# 运行指定文件
pytest tests/test_gui/test_styles.py

# 运行指定测试类
pytest tests/test_gui/test_styles.py::TestThemeColors

# 运行指定测试方法
pytest tests/test_gui/test_styles.py::TestThemeColors::test_primary_colors_exist
```

### 使用标记运行测试

```bash
# 运行单元测试
pytest -m unit

# 运行集成测试
pytest -m integration

# 运行GUI测试
pytest -m gui

# 运行慢速测试
pytest -m slow

# 排除慢速测试
pytest -m "not slow"
```

### 覆盖率报告

```bash
# 生成覆盖率报告（默认配置）
pytest

# 仅生成终端覆盖率报告
pytest --cov=yuntai --cov-report=term-missing

# 生成HTML覆盖率报告
pytest --cov=yuntai --cov-report=html

# 查看HTML报告
# 打开 htmlcov/index.html
```

### 详细输出

```bash
# 显示详细输出
pytest -v

# 显示更详细的输出（包括print语句）
pytest -v -s

# 显示测试用时最长的10个测试
pytest --durations=10
```

### 调试测试

```bash
# 在第一个失败时停止
pytest -x

# 在第N个失败时停止
pytest --maxfail=3

# 进入pdb调试器（失败时）
pytest --pdb

# 进入pdb调试器（开始时）
pytest --trace
```

## 测试配置说明

### pytest.ini 配置

```ini
[pytest]
testpaths = tests                          # 测试路径
python_files = test_*.py                   # 测试文件命名规则
python_classes = Test*                     # 测试类命名规则
python_functions = test_*                  # 测试函数命名规则
pythonpath = .                             # Python路径
addopts = -v --tb=short --cov=yuntai --cov-report=term-missing --cov-report=html --cov-fail-under=90
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
markers =
    unit: Unit tests (no external dependencies)
    integration: Integration tests
    slow: Slow running tests
    gui: GUI module tests
```

### 配置参数说明

| 参数 | 说明 |
|------|------|
| `--cov=yuntai` | 指定覆盖率测试范围为 yuntai 文件夹 |
| `--cov-report=term-missing` | 在终端显示缺失覆盖的行号 |
| `--cov-report=html` | 生成HTML格式的覆盖率报告 |
| `--cov-fail-under=90` | 覆盖率低于90%时测试失败 |
| `-v` | 详细输出模式 |
| `--tb=short` | 简短的回溯信息 |

## 编写测试规范

### 测试文件命名

- 文件名以 `test_` 开头
- 文件名应反映被测试的模块，如 `test_styles.py` 测试 `styles.py`

### 测试类命名

- 类名以 `Test` 开头
- 类名应反映被测试的类或功能，如 `TestThemeColors`

### 测试方法命名

- 方法名以 `test_` 开头
- 方法名应描述测试场景，如 `test_primary_colors_exist`

### 测试标记使用

```python
import pytest

@pytest.mark.unit
def test_simple_calculation():
    """单元测试示例"""
    assert 1 + 1 == 2

@pytest.mark.integration
def test_database_connection():
    """集成测试示例"""
    # 需要外部依赖的测试

@pytest.mark.slow
def test_long_running_process():
    """慢速测试示例"""
    # 执行时间较长的测试

@pytest.mark.gui
def test_gui_component():
    """GUI测试示例"""
    # GUI相关测试
```

### 使用 Fixtures

```python
import pytest

@pytest.fixture
def sample_data():
    """提供测试数据"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """使用fixture的测试"""
    assert sample_data["key"] == "value"
```

## 共享 Fixtures (conftest.py)

项目在 `tests/conftest.py` 中定义了以下共享 fixtures：

| Fixture | 说明 |
|---------|------|
| `project_root` | 项目根目录路径 |
| `temp_dir` | 临时目录 |
| `temp_json_file` | 临时JSON文件 |
| `temp_history_file` | 临时对话历史文件 |
| `temp_forever_memory_file` | 临时永久记忆文件 |
| `mock_env_vars` | Mock环境变量 |
| `mock_zhipu_client` | Mock智谱AI客户端 |
| `mock_chat_model` | Mock聊天模型 |
| `mock_file_manager` | Mock文件管理器 |
| `mock_tts_manager` | Mock TTS管理器 |
| `sample_conversation_history` | 示例对话历史数据 |
| `sample_chat_history` | 示例聊天历史列表 |
| `reset_global_state` | 重置全局状态（自动使用） |

## GUI 测试说明

### GUI 测试特点

GUI 测试需要特别注意以下几点：

1. **QApplication 实例**：GUI 测试需要 QApplication 实例，使用 fixture 确保：
   ```python
   @pytest.fixture(scope="module")
   def qapp():
       app = QApplication.instance()
       if app is None:
           app = QApplication([])
       yield app
   ```

2. **Mock 外部依赖**：GUI 模块依赖较多外部模块，需要适当 Mock：
   ```python
   with patch('yuntai.gui.gui_controller.TaskManager'):
       # 测试代码
   ```

3. **信号槽测试**：PyQt 信号槽需要特殊处理：
   ```python
   with patch.object(widget.signal, 'emit') as mock_emit:
       widget.do_something()
       mock_emit.assert_called_once()
   ```

### GUI 测试覆盖范围

| 模块 | 测试文件 | 覆盖内容 |
|------|----------|----------|
| `yuntai/gui/styles.py` | `test_styles.py` | 主题颜色、字体、样式表 |
| `yuntai/gui/output_capture.py` | `test_output_capture.py` | 输出捕获、高亮显示 |
| `yuntai/gui/gui_view.py` | `test_gui_view.py` | 视图组件、页面管理 |
| `yuntai/gui/gui_controller.py` | `test_gui_controller.py` | 控制器逻辑 |
| `yuntai/views/` | `test_views.py` | 页面构建器 |
| `yuntai/handlers/` | `test_handlers.py` | 事件处理器 |

## 常见问题

### 1. 测试运行失败

```bash
# 检查依赖是否安装
pip install pytest pytest-cov pytest-asyncio

# 检查环境变量
# 确保以下环境变量已设置（或在 conftest.py 中有默认值）
# ZHIPU_API_KEY, GPT_SOVITS_ROOT, SCRCPY_PATH, FFMPEG_PATH, FOREVER_MEMORY_FILE
```

### 2. 覆盖率不足

```bash
# 查看缺失覆盖的行
pytest --cov=yuntai --cov-report=term-missing

# 查看HTML报告获取详细信息
pytest --cov=yuntai --cov-report=html
# 然后打开 htmlcov/index.html
```

### 3. GUI 测试问题

```bash
# GUI 测试可能需要显示服务器（Linux）
export QT_QPA_PLATFORM=offscreen

# Windows 上通常不需要额外配置
```

### 4. 异步测试

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """异步测试示例"""
    result = await some_async_function()
    assert result is not None
```

## 持续集成

建议在 CI/CD 流程中添加测试步骤：

```yaml
# GitHub Actions 示例
- name: Run tests
  run: pytest --cov=yuntai --cov-report=xml
  
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## 最佳实践

1. **保持测试独立**：每个测试应该独立运行，不依赖其他测试
2. **使用有意义的断言**：断言消息应清晰说明预期结果
3. **测试边界条件**：不仅测试正常情况，还要测试边界和异常情况
4. **保持测试简洁**：每个测试只验证一个功能点
5. **及时更新测试**：代码变更时同步更新相关测试
