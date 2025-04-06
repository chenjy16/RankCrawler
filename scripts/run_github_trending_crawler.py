#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import aiohttp

# 确保输出目录存在
output_dir = Path("data/github")
output_dir.mkdir(parents=True, exist_ok=True)

# 语言列表
LANGUAGES = [
    "all", "python", "javascript", "typescript", "go", "rust", 
    "java", "c", "cpp", "csharp", "php", "ruby", "swift"
]

# 时间周期
PERIODS = ["daily", "weekly", "monthly"]

async def fetch_github_trending(language="all", period="daily"):
    """获取GitHub Trending数据"""
    print(f"开始获取GitHub Trending数据: 语言={language}, 周期={period}")
    
    url = f"https://github-trending-api.vercel.app/repositories?language={language}&since={period}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "language": language,
                        "period": period,
                        "fetch_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "repositories": data
                    }
                else:
                    print(f"获取失败，状态码: {response.status}")
                    return None
        except Exception as e:
            print(f"获取GitHub Trending数据时出错: {str(e)}")
            return None

async def main():
    """主函数"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    for language in LANGUAGES:
        for period in PERIODS:
            try:
                # 检查是否已有缓存数据
                cache_file = output_dir / f"github_{language}_{period}_{today}.json"
                if cache_file.exists():
                    print(f"发现缓存数据，跳过: {cache_file}")
                    continue
                
                # 获取数据
                result = await fetch_github_trending(language, period)
                
                if result:
                    # 保存结果
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    print(f"成功保存GitHub Trending数据: {cache_file}")
                else:
                    print(f"未能获取GitHub Trending数据: 语言={language}, 周期={period}")
                    
                # 添加延迟，避免请求过于频繁
                await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"处理GitHub Trending数据时出错: {str(e)}")
    
    print("GitHub Trending数据爬取完成")

if __name__ == "__main__":
    asyncio.run(main())