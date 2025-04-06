#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

# 确保导入正确
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
except ImportError:
    print("尝试使用替代导入路径...")
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# 确保输出目录存在
output_dir = Path("data/producthunt")
output_dir.mkdir(parents=True, exist_ok=True)

async def crawl_producthunt():
    """爬取ProductHunt今日产品"""
    print("开始爬取ProductHunt今日产品")
    
    url = "https://www.producthunt.com/"
    
    # 创建提取策略
    extraction_strategy = JsonCssExtractionStrategy(
        schema={
            "name": "ProductHunt今日产品",
            "baseSelector": "[data-test='product-item'], .product-item, .post-item, .post",
            "fields": [
                {"name": "product_name", "selector": "h3, .product-name, .post-name, .title", "type": "text"},
                {"name": "product_description", "selector": "p, .product-description, .post-description, .description", "type": "text"},
                {"name": "product_url", "selector": "a[href*='/posts/']", "type": "attribute", "attribute": "href"},
                {"name": "upvotes", "selector": ".vote-button, .upvote-button, [data-test='vote-button'], [data-test='upvote-count']", "type": "text"},
                {"name": "product_image", "selector": "img", "type": "attribute", "attribute": "src"},
                {"name": "maker_name", "selector": ".maker-name, .user-name, [data-test='maker-name']", "type": "text"},
            ]
        }
    )
    
    # 配置浏览器
    browser_config = BrowserConfig(
        headless=False,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    
    # 创建爬虫运行配置
    config = CrawlerRunConfig(
        js_code="""
            // 等待页面完全加载
            await new Promise(r => setTimeout(r, 10000));
            
            // 滚动页面以加载更多内容
            window.scrollTo(0, document.body.scrollHeight * 0.3);
            await new Promise(r => setTimeout(r, 2000));
            window.scrollTo(0, document.body.scrollHeight * 0.6);
            await new Promise(r => setTimeout(r, 2000));
            window.scrollTo(0, document.body.scrollHeight);
            await new Promise(r => setTimeout(r, 2000));
            
            return true;
        """,
        wait_for="networkidle",
        extraction_strategy=extraction_strategy,
        page_timeout=300000,  # 5分钟超时
        magic=True,
    )
    
    # 创建爬虫实例
    crawler = AsyncWebCrawler(browser_config=browser_config)
    
    # 执行爬取
    result = None
    for attempt in range(3):  # 最多尝试3次
        try:
            print(f"尝试爬取 ProductHunt (尝试 {attempt+1}/3)")
            result = await crawler.run(url, config)
            if result:
                break
        except Exception as e:
            print(f"爬取失败: {str(e)}")
            await asyncio.sleep(5)  # 等待5秒后重试
    
    # 处理结果
    if result and "items" in result and result["items"]:
        # 添加元数据
        final_result = {
            "fetch_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "products": result["items"]
        }
        
        # 处理产品URL，确保是完整URL
        for product in final_result["products"]:
            if "product_url" in product and product["product_url"] and not product["product_url"].startswith("http"):
                product["product_url"] = f"https://www.producthunt.com{product['product_url']}"
        
        return final_result
    
    print("未能获取ProductHunt数据")
    return None

async def main():
    """主函数"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 检查是否已有缓存数据
    cache_file = output_dir / f"producthunt_{today}.json"
    if cache_file.exists():
        print(f"发现缓存数据，跳过: {cache_file}")
        return
    
    # 获取数据
    result = await crawl_producthunt()
    
    if result:
        # 保存结果
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"成功保存ProductHunt今日产品数据: {cache_file}")
    else:
        print("未能获取ProductHunt今日产品数据")
    
    print("ProductHunt数据爬取完成")

if __name__ == "__main__":
    asyncio.run(main())