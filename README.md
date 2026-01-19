Phone Agent Pro - Intelligent Multi-Modal Control Agent

Version: 1.2.3

Overview
- Phone Agent Pro is a multi-modal AI-assisted control agent that orchestrates GLM-based decision making and a command executor to operate a connected phone or devices. It evolves from a CLI tool to a GUI-enabled assistant with chat, task orchestration, and multi-modal content generation.
- Core components include: an AI decision engine, a command executor (phone_agent), GUI components, and a multimodal processor that can handle text, image, and video tasks.

What’s included
- yun package: core business logic, GUI, and multimodal features.
- main.py: entrypoint for launching the app.
- config.example.py: sample configuration for local runs.
- Documentation: this README is the primary guide for developers and users.

How to run (quick start)
- Ensure Python 3.8+ is installed.
- Install dependencies (if a requirements file exists in the repo or in the docs).
- Run: python main.py (or the project’s entry script as documented in the docs)
- For GUI usage, follow on-screen prompts and menus that appear after startup.

Project structure (high level)
- yun/ : core modules (init, gui_controller, gui_view, multimodal_processor, task_manager, config).
- yuntai/ : legacy phone_agent execution modules and adapters (preserved for compatibility).
- assets/ and models/ (if present): resources used by AI models and TTS if configured.

Notes
- This project is under active development; paths, APIs, and models may change between versions.
- For environment setup, refer to the detailed notes in the original docs or the development guide.

Contributing
- Report issues and propose changes via GitHub issues or pull requests.
- Follow the repo’s coding style and include tests where applicable.

License
- See LICENSE in the repository root for terms.
