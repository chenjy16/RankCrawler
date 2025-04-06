#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
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
        # 解析文件名，正确处理类别和日期
        parts = file.stem.split("_")
        category_id = parts[0]
        date_str = "_".join(parts[1:])
        
        if category_id not in data_files or date_str > data_files[category_id][1]:
            data_files[category_id] = (file.name, date_str)
    
    if not data_files:
        print("未找到数据文件")
        return
    
    # 读取当前README内容
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 移除现有的数据链接部分（如果存在）
    content = re.sub(r"## 数据链接\n\n.*?(?=\n\n|$)", "", content, flags=re.DOTALL)
    
    # 构建新的数据链接部分
    links_content = "## 数据链接\n\n通过GitHub Actions自动爬取的最新排行榜数据可以通过以下链接访问：\n\n"
    
    # 添加每个类别的链接
    for category_id, (filename, date_str) in data_files.items():
        # 根据类别ID确定类别名称
        if category_id == "digital_computer":
            category_name = "数码电脑"
        else:
            category_name = category_id
        
        # 正确格式化日期字符串，避免显示问题
        formatted_date = date_str.replace("_", "-")
        
        # 使用完整的URL，确保链接可点击
        links_content += f"- [{category_name}排行榜数据下载](https://github.com/chenjy16/RankCrawler/blob/main/data/1688/{filename}) - 更新时间: {formatted_date}\n"
    
    # 添加可视化页面链接
    links_content += f"- [排行榜可视化页面](https://chenjy16.github.io/RankCrawler/1688_rankings.html) - 交互式数据可视化界面\n"
    
    # 将新的数据链接部分添加到README中
    # 查找Installation部分的结束位置
    installation_pattern = r"## Installation\n\n```bash[\s\S]*?```"
    installation_match = re.search(installation_pattern, content)
    
    if installation_match:
        # 在Installation部分后添加数据链接部分
        insert_pos = installation_match.end()
        content = content[:insert_pos] + "\n\n" + links_content + content[insert_pos+1:]
    else:
        # 如果没有找到Installation部分，直接添加到末尾
        content = content.rstrip() + "\n\n" + links_content + "\n"
    
    # 写入更新后的README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"README.md 数据链接已更新")

if __name__ == "__main__":
    update_readme_links()