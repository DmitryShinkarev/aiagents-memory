"""Setup configuration for memory-agents package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="memory-agents",
    version="0.1.0",
    author="Memory-Agents Team",
    author_email="",
    description="Comprehensive memory system for multi-agent systems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/memory-agents",
    packages=find_packages(exclude=["tests", "tests.*", "examples"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.1",
            "ruff>=0.1.9",
            "mypy>=1.8.0",
        ],
        "clickhouse": [
            "clickhouse-driver>=0.2.6",
            "asynch>=0.2.3",
        ],
    },
    entry_points={
        "console_scripts": [
            "memory-agents=utils.cli:main",
        ],
    },
)


