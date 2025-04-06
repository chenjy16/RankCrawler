#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from pathlib import Path
from datetime import datetime

def update_readme_links():
    """更新README.md中的Robinhood股票数据链接"""
    readme_path = Path("README.md")
    data_dir = Path("data/robinhood")
    
    # 读取README内容
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找最新的数据文件
    latest_files = {}
    for file in data_dir.glob("*.json"):
        if file.name.startswith("stock_analysis_"):
            # 分析文件
            match = re.match(r'stock_analysis_(\d{4}-\d{2}-\d{2})\.json', file.name)
            if match:
                date_str = match.group(1)
                if "analysis" not in latest_files or date_str > latest_files["analysis"][1]:
                    latest_files["analysis"] = (file, date_str)
        elif file.name.startswith("stock_"):
            # 股票详情文件，忽略
            continue
        else:
            # 类别文件
            match = re.match(r'(.+)_(\d{4}-\d{2}-\d{2})\.json', file.name)
            if match:
                category_id = match.group(1)
                date_str = match.group(2)
                if category_id not in latest_files or date_str > latest_files[category_id][1]:
                    latest_files[category_id] = (file, date_str)
    
    # 如果没有找到文件，直接返回
    if not latest_files:
        print("未找到任何Robinhood数据文件，无法更新README")
        return
    
    # 查找README中的数据链接部分
    robinhood_section_pattern = r'(## Robinhood Stock Data\n\n.*?)(?=\n##|\Z)'
    robinhood_section_match = re.search(robinhood_section_pattern, content, re.DOTALL)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 构建新的数据链接部分
    new_section = f"## Robinhood Stock Data\n\n"
    new_section += "Access the latest Robinhood stock data automatically crawled via GitHub Actions:\n\n"
    
    # 添加类别数据链接
    for category_id, (file, date_str) in sorted(latest_files.items()):
        if category_id == "analysis":
            continue
            
        # 从文件中读取类别名称
        try:
            import json
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                category_name = data.get("category_name", category_id)
        except:
            category_name = category_id.replace("_", " ").title()
        
        # 添加链接
        relative_path = file.relative_to(Path.cwd())
        new_section += f"* [{category_name} Data](https://github.com/chenjy16/RankCrawler/blob/main/{relative_path}) - Updated: {date_str}\n"
    
    # 添加分析数据链接
    if "analysis" in latest_files:
        file, date_str = latest_files["analysis"]
        relative_path = file.relative_to(Path.cwd())
        new_section += f"* [Stock Analysis Results](https://github.com/chenjy16/RankCrawler/blob/main/{relative_path}) - Updated: {date_str}\n"
    
    # 添加可视化仪表盘链接
    new_section += f"* [Stock Visualization Dashboard](https://chenjy16.github.io/RankCrawler/robinhood_stocks.html) - Interactive data visualization interface\n"
    
    # 更新README内容
    if robinhood_section_match:
        # 替换现有部分
        new_content = content[:robinhood_section_match.start()] + new_section + content[robinhood_section_match.end():]
    else:
        # 在Data Links部分后添加
        data_links_pattern = r'(## Data Links\n\n.*?)(?=\n##|\Z)'
        data_links_match = re.search(data_links_pattern, content, re.DOTALL)
        
        if data_links_match:
            new_content = content[:data_links_match.end()] + "\n\n" + new_section + content[data_links_match.end():]
        else:
            # 如果没有找到Data Links部分，在文件末尾添加
            new_content = content + "\n\n" + new_section
    
    # 保存更新后的README
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"README.md已更新，添加了最新的Robinhood股票数据链接")

if __name__ == "__main__":
    update_readme_links()