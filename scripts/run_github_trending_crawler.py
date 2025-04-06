#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
import aiohttp
from bs4 import BeautifulSoup

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

# 添加请求头，模拟浏览器
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

async def fetch_github_trending(language="all", period="daily"):
    """直接从GitHub页面获取Trending数据"""
    print(f"开始获取GitHub Trending数据: 语言={language}, 周期={period}")
    
    # 构建URL
    lang_param = "" if language == "all" else f"/{language}"
    url = f"https://github.com/trending{lang_param}?since={period}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # 使用BeautifulSoup解析HTML
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 查找所有仓库项
                    repo_items = soup.select('article.Box-row')
                    
                    repositories = []
                    for item in repo_items:
                        try:
                            # 提取仓库名称和链接
                            repo_link = item.select_one('h2 a')
                            if not repo_link:
                                continue
                                
                            repo_path = repo_link.get('href', '').strip('/')
                            repo_name = repo_path
                            
                            # 提取描述
                            description_elem = item.select_one('p')
                            description = description_elem.text.strip() if description_elem else ""
                            
                            # 提取语言
                            lang_elem = item.select_one('span[itemprop="programmingLanguage"]')
                            repo_language = lang_elem.text.strip() if lang_elem else None
                            
                            # 提取星星数
                            stars_elem = item.select_one('a.Link--muted:nth-of-type(1)')
                            stars = stars_elem.text.strip().replace(',', '') if stars_elem else "0"
                            
                            # 提取fork数
                            forks_elem = item.select_one('a.Link--muted:nth-of-type(2)')
                            forks = forks_elem.text.strip().replace(',', '') if forks_elem else "0"
                            
                            # 提取今日新增星星
                            today_stars_elem = item.select_one('span.d-inline-block.float-sm-right')
                            today_stars = today_stars_elem.text.strip() if today_stars_elem else ""
                            
                            repositories.append({
                                "author": repo_path.split('/')[0] if '/' in repo_path else "",
                                "name": repo_path.split('/')[1] if '/' in repo_path else repo_path,
                                "full_name": repo_path,
                                "url": f"https://github.com/{repo_path}",
                                "description": description,
                                "language": repo_language,
                                "stars": stars,
                                "forks": forks,
                                "today_stars": today_stars,
                            })
                        except Exception as e:
                            print(f"解析仓库项时出错: {str(e)}")
                    
                    return {
                        "language": language,
                        "period": period,
                        "fetch_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "repositories": repositories
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
                
                if result and result.get("repositories"):
                    # 保存结果
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    print(f"成功保存GitHub Trending数据: {cache_file}")
                else:
                    print(f"未能获取GitHub Trending数据: 语言={language}, 周期={period}")
                    
                # 添加延迟，避免请求过于频繁
                await asyncio.sleep(5)  # 增加延迟时间，避免被限制
                    
            except Exception as e:
                print(f"处理GitHub Trending数据时出错: {str(e)}")
    
    print("GitHub Trending数据爬取完成")

if __name__ == "__main__":
    asyncio.run(main())