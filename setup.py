from setuptools import setup, find_packages
import os
from pathlib import Path

# 确保README.md存在
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()
else:
    print("警告: README.md文件不存在")

setup(
    name="RankCrawler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.49.0",
        "beautifulsoup4>=4.12.0",
        "aiofiles>=24.1.0",
        "httpx>=0.27.0",
        "lxml>=5.3.0",
        "python-dotenv>=1.0.0",
        "aiosqlite>=0.20.0",
        "pydantic>=2.10.0",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
