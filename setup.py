#!/usr/bin/env python3
"""Setup script for YuntaiPhoneAgent."""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="YuntaiPhoneAgent",
    version="1.3.2",
    description="AI-powered intelligent phone automation framework with multi-platform support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/YunTaiHua/YuntaiPhoneAgent",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.9.1",
        "Pillow>=10.0.0",
        "openai>=2.9.0",
        "zhipuai>=2.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
        "langchain>=0.3.0",
        "langchain-core>=0.3.0",
        "langchain-openai>=0.3.0",
        "langgraph>=0.2.0",
        "PyAudio>=0.2.14",
        "soundfile>=0.12.0",
        "pyperclip>=1.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
        ],
        "torch": [
            "torch>=2.0.0",
        ],
        "multimodal": [
            "markitdown[all]>=0.1.4",
        ],
    },
    entry_points={
        "console_scripts": [
            "yuntai-agent=main:main",
        ],
    },
    keywords="ai agent phone automation android ios harmonyos langchain langgraph",
)
