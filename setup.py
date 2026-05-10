#!/usr/bin/env python3
"""
LogEarn Trading Skills - Setup
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="logearn-trading-skills",
    version="1.1.0",
    author="dinnelthai",
    description="Solana Meme币交易模块 - Fibonacci + AO 策略",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dinnelthai/logearn-traidng-skills",
    packages=find_packages(),
    py_modules=["papertrading"],
    entry_points={
        "console_scripts": [
            "papertrading=papertrading:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        # 无外部依赖，仅使用Python标准库
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "mypy>=0.950",
        ],
    },
)
