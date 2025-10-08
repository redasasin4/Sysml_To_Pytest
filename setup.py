"""
Setup script for sysml2pytest
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="sysml2pytest",
    version="0.1.0",
    author="Systems Engineering Team",
    description="Convert SysML V2 requirements to pytest tests with property-based testing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/sysml2pytest",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Code Generators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pytest>=7.4.0",
        "hypothesis>=6.90.0",
        "jinja2>=3.1.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "mypy>=1.7.0",
            "ruff>=0.1.0",
            "pytest-cov>=4.1.0",
        ],
        "sysml": [
            "sysml-v2-api-client>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "sysml2pytest=sysml2pytest.cli:main",
        ],
        "pytest11": [
            "sysml2pytest = sysml2pytest.plugin.plugin",
        ],
    },
)
