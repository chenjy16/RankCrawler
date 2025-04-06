#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime
from pathlib import Path

def update_readme_links():
    """更新README.md中的数据链接"""
    readme_path = Path("README.md")
    data_dir = Path("data/1688")
    
    # 确保数据目录存在
    if not data_dir.exists():
        print(f"数据目录 {data_dir} 不存在")
        return
    
    # 获取最新的数据文件
    data_files = {}
    for file in data_dir.glob("*.json"):
        category_id = file.stem.split("_")[0]
        date_str = "_".join(file.stem.split("_")[1:])
        if category_id not in data_files or date_str > data_files[category_id][1]:
            data_files[category_id] = (file.name, date_str)
    
    if not data_files:
        print("未找到数据文件")
        return
    
    # 读取当前README内容
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 检查是否已有数据链接部分
    data_links_section = "## 数据链接"
    if data_links_section not in content:
        # 添加数据链接部分
        content += f"\n{data_links_section}\n\n"
        content += "通过GitHub Actions自动爬取的最新排行榜数据可以通过以下链接访问：\n\n"
    
    # 更新链接部分
    links_pattern = r"## 数据链接\n\n.*?(?=\n\n|$)"
    links_content = f"## 数据链接\n\n通过GitHub Actions自动爬取的最新排行榜数据可以通过以下链接访问：\n\n"
    
    # 添加每个类别的链接
    for category_id, (filename, date_str) in data_files.items():
        if category_id == "digital_computer":
            category_name = "数码电脑"
        else:
            category_name = category_id
            
        # 使用完整的URL，确保链接可点击
        links_content += f"- [{category_name}排行榜](https://github.com/chenjy16/RankCrawler/blob/main/data/1688/{filename}) - 更新时间: {date_str}\n"
    
    # 添加可视化页面链接
    links_content += f"- [排行榜可视化页面](https://chenjy16.github.io/RankCrawler/1688_rankings.html) - 交互式数据可视化界面\n"
    
    # 更新README内容
    if re.search(links_pattern, content, re.DOTALL):
        content = re.sub(links_pattern, links_content, content, flags=re.DOTALL)
    else:
        content += links_content
    
    # 写入更新后的README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"README.md 数据链接已更新")

if __name__ == "__main__":
    update_readme_links()