#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import aiohttp

# 确保输出目录存在
output_dir = Path("data/hackernews")
output_dir.mkdir(parents=True, exist_ok=True)

# HackerNews API端点
API_BASE = "https://hacker-news.firebaseio.com/v0"

async def fetch_json(url, session):
    """获取JSON数据"""
    try:
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None
    except Exception as e:
        print(f"获取数据失败: {url}, 错误: {str(e)}")
        return None

async def fetch_story(story_id, session):
    """获取单个故事详情"""
    url = f"{API_BASE}/item/{story_id}.json"
    return await fetch_json(url, session)

async def fetch_top_stories(limit=100):
    """获取HackerNews热门故事"""
    print(f"开始获取HackerNews热门故事，数量: {limit}")
    
    async with aiohttp.ClientSession() as session:
        # 获取热门故事ID列表
        top_stories_url = f"{API_BASE}/topstories.json"
        story_ids = await fetch_json(top_stories_url, session)
        
        if not story_ids:
            print("获取热门故事ID列表失败")
            return None
        
        # 限制数量
        story_ids = story_ids[:limit]
        
        # 并发获取故事详情
        tasks = [fetch_story(story_id, session) for story_id in story_ids]
        stories = await asyncio.gather(*tasks)
        
        # 过滤掉获取失败的故事
        stories = [story for story in stories if story]
        
        return {
            "fetch_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "stories": stories
        }

async def main():
    """主函数"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 检查是否已有缓存数据
    cache_file = output_dir / f"hackernews_top_{today}.json"
    if cache_file.exists():
        print(f"发现缓存数据，跳过: {cache_file}")
        return
    
    # 获取数据
    result = await fetch_top_stories()
    
    if result:
        # 保存结果
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"成功保存HackerNews热门故事数据: {cache_file}")
    else:
        print("未能获取HackerNews热门故事数据")
    
    print("HackerNews数据爬取完成")

if __name__ == "__main__":
    asyncio.run(main())