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
    
    # 修改这部分，避免移除整个Data Links部分
    # 而是只替换1688相关的内容
    data_links_pattern = r"(## Data Links\s*\n\nAccess the latest ranking data.*?)(?=\n\n## Robinhood Stock Data|\n\n## |$)"
    data_links_match = re.search(data_links_pattern, content, flags=re.DOTALL)
    
    if data_links_match:
        # 只替换1688相关的部分，保留其他部分
        content = content.replace(data_links_match.group(0), links_content)
    else:
        # 如果没有找到Data Links部分，则添加新的部分
        # 移除Features部分下可能存在的重复链接
        features_pattern = r"(## Features\n\n.*?)(\* digital Rankings.*?interface)(\n\n)"
        features_match = re.search(features_pattern, content, re.DOTALL)
        if features_match:
            # 保留Features部分，但移除重复的链接
            content = content.replace(features_match.group(0), features_match.group(1) + "\n\n")
        
        # 构建新的数据链接部分，确保有足够的空行
        links_content = "\n\n## Data Links\n\nAccess the latest ranking data automatically crawled via GitHub Actions through the following links:\n\n"
        
        # 添加每个类别的链接
        for category_id, (filename, date_str) in data_files.items():
            # 根据类别ID确定类别名称
            category_names = {
                "digital_computer": "Digital & Computer"
            }
            category_name = category_names.get(category_id, category_id)
            
            # 正确格式化日期字符串，避免显示问题
            formatted_date = date_str.replace("_", "-")
            
            # 使用完整的URL，确保链接可点击
            links_content += f"* [{category_name} Rankings Data Download](https://github.com/chenjy16/RankCrawler/blob/main/data/1688/{filename}) - Updated: {formatted_date}\n"
        
        # 添加可视化页面链接
        links_content += f"* [Rankings Visualization Dashboard](https://chenjy16.github.io/RankCrawler/1688_rankings.html) - Interactive data visualization interface\n"
        
        # 将新的数据链接部分添加到README中
        # 查找Features部分的结束位置
        features_pattern = r"(## Features\n\n.*?Interactive web dashboard for viewing ranking data\n)"
        features_match = re.search(features_pattern, content, re.DOTALL)
        
        if features_match:
            # 在Features部分后添加数据链接部分，确保有足够的空行
            insert_pos = features_match.end()
            content = content[:insert_pos] + links_content + content[insert_pos:]
        else:
            # 如果没有找到Features部分，使用原来的逻辑
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