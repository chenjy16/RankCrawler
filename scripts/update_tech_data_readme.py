#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import json
from pathlib import Path
from datetime import datetime

def update_readme_links():
    """更新README.md中的技术数据链接"""
    readme_path = Path("README.md")
    
    # 数据目录列表 - 移除 ProductHunt
    data_dirs = {
        "github": Path("data/github"),
        "hackernews": Path("data/hackernews")
        # 移除 producthunt
    }
    
    # 读取README内容
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 构建新的数据链接部分
    new_section = f"## Tech Trending Data\n\n"
    new_section += "Access the latest technology trending data automatically crawled via GitHub Actions:\n\n"
    
    # 添加可视化链接
    new_section += "* [Tech Trending Visualization Dashboard](https://chenjy16.github.io/RankCrawler/tech_trending.html) - Interactive technology trending visualization interface\n\n"
    
    # 处理每个数据目录
    for data_type, data_dir in data_dirs.items():
        if not data_dir.exists():
            continue
            
        # 查找最新的数据文件
        latest_files = {}
        
        if data_type == "github":
            # GitHub数据文件处理
            for file in data_dir.glob("github_*.json"):
                match = re.match(r'github_(.+)_(.+)_(\d{4}-\d{2}-\d{2})\.json', file.name)
                if match:
                    language = match.group(1)
                    period = match.group(2)
                    date_str = match.group(3)
                    
                    key = f"{language}_{period}"
                    if key not in latest_files or date_str > latest_files[key][1]:
                        latest_files[key] = (file, date_str)
        
        elif data_type == "hackernews":
            # HackerNews数据文件处理
            for file in data_dir.glob("hackernews_*.json"):
                match = re.match(r'hackernews_(.+)_(\d{4}-\d{2}-\d{2})\.json', file.name)
                if match:
                    category = match.group(1)
                    date_str = match.group(2)
                    
                    if category not in latest_files or date_str > latest_files[category][1]:
                        latest_files[category] = (file, date_str)
        
        # 移除 ProductHunt 数据文件处理部分
        
        # 添加数据链接
        if latest_files:
            new_section += f"### {data_type.title()} Data\n\n"
            
            for key, (file, date_str) in sorted(latest_files.items()):
                # 修复路径问题 - 使用字符串而不是Path对象的relative_to方法
                relative_path = str(file)
                
                if data_type == "github":
                    language, period = key.split("_")
                    display_name = f"{language.title()} - {period.title()}"
                    new_section += f"* [{display_name}](https://github.com/chenjy16/RankCrawler/blob/main/{relative_path}) - Updated: {date_str}\n"
                
                elif data_type == "hackernews":
                    display_name = f"{key.replace('_', ' ').title()} Stories"
                    new_section += f"* [{display_name}](https://github.com/chenjy16/RankCrawler/blob/main/{relative_path}) - Updated: {date_str}\n"
                
                # 移除 ProductHunt 链接生成部分
            
            new_section += "\n"
    
    # 查找插入位置
    tech_section_pattern = r"## Tech Trending Data\s*\n\n.*?(?=\n\n## |$)"
    tech_section_match = re.search(tech_section_pattern, content, flags=re.DOTALL)
    
    if tech_section_match:
        # 替换现有部分
        content = content.replace(tech_section_match.group(0), new_section)
    else:
        # 查找Data Links部分
        data_links_pattern = r"(## Data Links\s*\n\n.*?)(?=\n\n## |$)"
        data_links_match = re.search(data_links_pattern, content, flags=re.DOTALL)
        
        if data_links_match:
            # 在Data Links部分后添加
            insert_pos = data_links_match.end()
            content = content[:insert_pos] + "\n\n" + new_section + content[insert_pos:]
        else:
            # 查找Robinhood Stock Data部分
            robinhood_pattern = r"(## Robinhood Stock Data\s*\n\n.*?)(?=\n\n## |$)"
            robinhood_match = re.search(robinhood_pattern, content, flags=re.DOTALL)
            
            if robinhood_match:
                # 在Robinhood部分后添加
                insert_pos = robinhood_match.end()
                content = content[:insert_pos] + "\n\n" + new_section + content[insert_pos:]
            else:
                # 如果没有找到合适的位置，添加到文件末尾
                content = content.rstrip() + "\n\n" + new_section + "\n"
    
    # 保存更新后的README
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"README.md已更新，添加了最新的技术数据链接")

if __name__ == "__main__":
    update_readme_links()