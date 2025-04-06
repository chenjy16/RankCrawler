#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import asyncio
import base64
from pathlib import Path
from datetime import datetime
import anthropic
from dotenv import load_dotenv

# 确保导入正确
try:
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    from crawl4ai.async_logger import AsyncLogger
except ImportError:
    print("尝试使用替代导入路径...")
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    from crawl4ai.async_logger import AsyncLogger

# ANSI颜色代码
class Colors:
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

# 初始化日志记录器
logger = AsyncLogger()

# 确保输出目录存在
output_dir = Path("data/robinhood")
output_dir.mkdir(parents=True, exist_ok=True)

# 股票类别列表
STOCK_CATEGORIES = [
    {
        "id": "most_popular",
        "name": "最受欢迎股票",
        "url": "https://robinhood.com/collections/100-most-popular"
    },
    {
        "id": "top_movers",
        "name": "涨跌幅最大股票",
        "url": "https://robinhood.com/collections/top-movers"
    },
    {
        "id": "tech_stocks",
        "name": "科技股",
        "url": "https://robinhood.com/collections/technology"
    },
    {
        "id": "growth_stocks",
        "name": "成长股",
        "url": "https://robinhood.com/collections/growth-stocks"
    }
]

# 股票搜索关键词列表
STOCK_SEARCH_TERMS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", 
    "TSLA", "NVDA", "AMD", "INTC", "NFLX"
]

async def crawl_robinhood_category(category, max_retries=3):
    """爬取Robinhood股票类别数据"""
    logger.info(f"开始爬取类别: {category['name']} (ID: {category['id']})")
    print(f"{Colors.CYAN}开始爬取类别: {category['name']} (ID: {category['id']}){Colors.RESET}")
    
    # 创建提取策略 - 针对Robinhood网站结构
    extraction_strategy = JsonCssExtractionStrategy(
        schema={
            "name": "Robinhood股票列表",
            "baseSelector": ".rh-hyperlink, [data-testid='stock-card'], [data-testid='stock-item'], .instrument-card, .stock-card, .list-item, .stock-list-item", 
            "fields": [
                {"name": "stock_symbol", "selector": ".symbol, [data-testid='symbol'], .ticker, .ticker-symbol", "type": "text"},
                {"name": "stock_name", "selector": ".company-name, [data-testid='name'], .name, .stock-name", "type": "text"},
                {"name": "stock_price", "selector": ".price, [data-testid='price'], .current-price, .stock-price", "type": "text"},
                {"name": "price_change", "selector": ".price-change, [data-testid='price-change'], .change, .stock-change", "type": "text"},
                {"name": "percent_change", "selector": ".percent-change, [data-testid='percent-change'], .change-percent, .stock-percent", "type": "text"},
                {"name": "stock_url", "selector": "a", "type": "attribute", "attribute": "href"},
                {"name": "market_cap", "selector": ".market-cap, [data-testid='market-cap'], .cap", "type": "text"},
                {"name": "volume", "selector": ".volume, [data-testid='volume']", "type": "text"},
            ]
        }
    )
    
    # 配置浏览器 - 增强反爬虫能力
    browser_config = BrowserConfig(
        headless=False,  # 非无头模式，更容易通过反爬检测
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
        headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://robinhood.com/",
        },
    )
    
    # 创建爬虫运行配置 - 增强等待策略和交互逻辑
    config = CrawlerRunConfig(
        js_code="""
            // 模拟真实用户行为
            async function simulateUserBehavior() {
                console.log('开始模拟用户行为...');
                
                // 等待页面完全加载
                await new Promise(r => setTimeout(r, 15000));  // 增加等待时间到15秒
                
                // 检查是否有弹窗并关闭
                const closeButtons = document.querySelectorAll('.close-btn, .modal-close, .popup-close, .dialog-close, .btn-close, .close, button[aria-label="Close"]');
                for (const btn of closeButtons) {
                    try {
                        btn.click();
                        console.log('关闭了弹窗');
                        await new Promise(r => setTimeout(r, 1000));
                    } catch (e) {}
                }
                
                // 随机滚动模拟真实用户
                for (let i = 0; i < 20; i++) {
                    const scrollAmount = Math.floor(Math.random() * 500) + 200;
                    window.scrollBy(0, scrollAmount);
                    await new Promise(r => setTimeout(r, Math.random() * 800 + 500));
                    
                    // 随机暂停，模拟用户查看内容
                    if (i % 3 === 0) {
                        await new Promise(r => setTimeout(r, Math.random() * 2000 + 1000));
                    }
                }
                
                // 滚动到底部以加载更多内容
                window.scrollTo(0, document.body.scrollHeight * 0.7);
                await new Promise(r => setTimeout(r, 3000));
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(r => setTimeout(r, 3000));
                
                return true;
            }
            
            return await simulateUserBehavior();
        """,
        wait_for="networkidle",  # 等待网络空闲
        extraction_strategy=extraction_strategy,
        page_timeout=600000,  # 10分钟超时
        magic=True,  # 启用魔法模式
        simulate_user=True,  # 模拟用户行为
        override_navigator=True,  # 覆盖navigator属性
        delay_before_return_html=45.0,  # 增加到45秒
        verbose=True,  # 启用详细日志
        screenshot=True,
        screenshot_full_path=str(Path("debug/screenshots").absolute()),
    )
    
    # 确保截图目录存在
    Path("debug/screenshots").mkdir(parents=True, exist_ok=True)
    
    # 执行爬取，添加重试机制
    for attempt in range(max_retries):
        try:
            print(f"{Colors.YELLOW}尝试第 {attempt+1}/{max_retries} 次爬取{Colors.RESET}")
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=category['url'], config=config)
                
                if not result.success:
                    print(f"{Colors.RED}爬取失败: {result.message if hasattr(result, 'message') else '未知错误'}{Colors.RESET}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 递增等待时间
                        print(f"{Colors.YELLOW}等待 {wait_time} 秒后重试...{Colors.RESET}")
                        await asyncio.sleep(wait_time)
                        continue
                    return None
                
                # 检查是否有提取到内容
                if not result.extracted_content or result.extracted_content == "[]":
                    print(f"{Colors.RED}提取内容为空，可能选择器不匹配{Colors.RESET}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"{Colors.YELLOW}等待 {wait_time} 秒后重试...{Colors.RESET}")
                        await asyncio.sleep(wait_time)
                        continue
                    return None
                
                # 解析结果
                try:
                    stocks = json.loads(result.extracted_content)
                    
                    # 记录原始数据数量
                    print(f"{Colors.GREEN}提取到 {len(stocks)} 只股票{Colors.RESET}")
                    
                    # 添加排名信息
                    for i, stock in enumerate(stocks):
                        stock["rank"] = i + 1
                    
                    # 添加元数据
                    result_data = {
                        "category_id": category['id'],
                        "category_name": category['name'],
                        "category_url": category['url'],
                        "crawl_time": datetime.now().isoformat(),
                        "total_stocks": len(stocks),
                        "stocks": stocks
                    }
                    
                    return result_data
                except Exception as e:
                    print(f"{Colors.RED}处理数据失败: {str(e)}{Colors.RESET}")
                    if attempt < max_retries - 1:
                        continue
                    return None
        except Exception as e:
            print(f"{Colors.RED}爬取过程中发生错误: {str(e)}{Colors.RESET}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"{Colors.YELLOW}等待 {wait_time} 秒后重试...{Colors.RESET}")
                await asyncio.sleep(wait_time)
                continue
            return None
    
    return None

async def crawl_stock_detail(stock_symbol, max_retries=3):
    """爬取单个股票详细信息"""
    logger.info(f"开始爬取股票详情: {stock_symbol}")
    print(f"{Colors.CYAN}开始爬取股票详情: {stock_symbol}{Colors.RESET}")
    
    url = f"https://robinhood.com/stocks/{stock_symbol}"
    
    # 创建提取策略 - 针对Robinhood股票详情页
    extraction_strategy = JsonCssExtractionStrategy(
        schema={
            "name": "Robinhood股票详情",
            "fields": [
                {"name": "stock_symbol", "selector": "[data-testid='symbol'], .symbol, .ticker", "type": "text"},
                {"name": "stock_name", "selector": "[data-testid='name'], .company-name, .name", "type": "text"},
                {"name": "current_price", "selector": "[data-testid='price'], .price", "type": "text"},
                {"name": "price_change", "selector": "[data-testid='price-change'], .price-change", "type": "text"},
                {"name": "percent_change", "selector": "[data-testid='percent-change'], .percent-change", "type": "text"},
                {"name": "market_cap", "selector": "[data-testid='market-cap'], .market-cap", "type": "text"},
                {"name": "pe_ratio", "selector": "[data-testid='pe-ratio'], .pe-ratio", "type": "text"},
                {"name": "dividend_yield", "selector": "[data-testid='dividend-yield'], .dividend-yield", "type": "text"},
                {"name": "volume", "selector": "[data-testid='volume'], .volume", "type": "text"},
                {"name": "avg_volume", "selector": "[data-testid='avg-volume'], .avg-volume", "type": "text"},
                {"name": "high_52_week", "selector": "[data-testid='high-52-week'], .high-52-week", "type": "text"},
                {"name": "low_52_week", "selector": "[data-testid='low-52-week'], .low-52-week", "type": "text"},
                {"name": "about", "selector": "[data-testid='about'], .about, .description", "type": "text"},
                {"name": "news_titles", "selector": "[data-testid='news-title'], .news-title, .article-title", "type": "text", "multiple": True},
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
        simulate_user=True,
        verbose=True,
        screenshot=True,
        screenshot_full_path=str(Path("debug/screenshots").absolute()),
    )
    
    # 执行爬取，添加重试机制
    for attempt in range(max_retries):
        try:
            print(f"{Colors.YELLOW}尝试第 {attempt+1}/{max_retries} 次爬取{Colors.RESET}")
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=config)
                
                if not result.success:
                    print(f"{Colors.RED}爬取失败: {result.message if hasattr(result, 'message') else '未知错误'}{Colors.RESET}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        print(f"{Colors.YELLOW}等待 {wait_time} 秒后重试...{Colors.RESET}")
                        await asyncio.sleep(wait_time)
                        continue
                    return None
                
                # 解析结果
                try:
                    stock_detail = json.loads(result.extracted_content)
                    
                    # 添加元数据
                    stock_detail["url"] = url
                    stock_detail["crawl_time"] = datetime.now().isoformat()
                    
                    return stock_detail
                except Exception as e:
                    print(f"{Colors.RED}处理数据失败: {str(e)}{Colors.RESET}")
                    if attempt < max_retries - 1:
                        continue
                    return None
        except Exception as e:
            print(f"{Colors.RED}爬取过程中发生错误: {str(e)}{Colors.RESET}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"{Colors.YELLOW}等待 {wait_time} 秒后重试...{Colors.RESET}")
                await asyncio.sleep(wait_time)
                continue
            return None
    
    return None

# 使用Anthropic分析股票数据
def analyze_stocks(stock_data_list, client):
    """使用Anthropic分析股票数据并提供投资建议"""
    try:
        print(f"{Colors.YELLOW}开始分析股票数据...{Colors.RESET}")
        
        # 准备分析内容
        stock_contents = []
        for category_data in stock_data_list:
            if not category_data or "stocks" not in category_data:
                continue
                
            for stock in category_data["stocks"][:10]:  # 每个类别取前10只股票
                stock_contents.append({
                    "symbol": stock.get("stock_symbol", ""),
                    "name": stock.get("stock_name", ""),
                    "price": stock.get("stock_price", ""),
                    "change": stock.get("price_change", ""),
                    "percent": stock.get("percent_change", ""),
                    "rank": stock.get("rank", 0)
                })
        
        # 构建分析提示
        analyze_prompt = f"""
基于以下Robinhood股票数据，分析并确定哪些股票是最佳投资机会。只返回JSON格式的结果，不要包含其他文本。

请按以下JSON格式返回结果：
{{
    "scores": [
        {{
            "stock_symbol": "<股票代码>",
            "stock_name": "<股票名称>",
            "score": <评分（满分100）>,
            "recommendation": "<投资建议：买入/持有/卖出>",
            "reason": "<简短分析理由>"
        }},
        ...
    ]
}}

股票数据:
{json.dumps(stock_contents, ensure_ascii=False, indent=2)}

只返回JSON，不要包含其他文本。
"""

        # 调用Anthropic API
        completion = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            temperature=0,
            system="你是一位专业的金融分析师。只返回JSON格式的结果，不要包含其他文本。",
            messages=[
                {
                    "role": "user",
                    "content": analyze_prompt
                }
            ]
        )

        result = completion.content[0].text
        print(f"{Colors.GREEN}分析完成。以下是投资建议:{Colors.RESET}")
        print(f"{Colors.MAGENTA}{result}{Colors.RESET}")
        
        # 保存分析结果
        today = datetime.now().strftime('%Y-%m-%d')
        analysis_file = output_dir / f"stock_analysis_{today}.json"
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(json.loads(result), f, ensure_ascii=False, indent=2)
            
        print(f"{Colors.GREEN}分析结果已保存到 {analysis_file}{Colors.RESET}")
        
        return json.loads(result)
    except Exception as e:
        print(f"{Colors.RED}分析股票数据时出错: {str(e)}{Colors.RESET}")
        return None

async def main():
    """主函数"""
    print(f"{Colors.MAGENTA}===== Robinhood股票数据爬取 ====={Colors.RESET}")
    
    # 加载环境变量
    load_dotenv()
    
    # 初始化Anthropic客户端
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        print(f"{Colors.RED}未找到ANTHROPIC_API_KEY环境变量{Colors.RESET}")
        return
        
    client = anthropic.Anthropic(api_key=anthropic_api_key)
    
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 爬取类别数据
    category_results = []
    for category in STOCK_CATEGORIES:
        try:
            print(f"{Colors.BLUE}===== 开始处理类别: {category['name']} ====={Colors.RESET}")
            
            # 检查是否已有缓存数据
            cache_file = output_dir / f"{category['id']}_{today}.json"
            if cache_file.exists():
                print(f"{Colors.YELLOW}发现缓存数据，正在加载: {cache_file}{Colors.RESET}")
                with open(cache_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                print(f"{Colors.GREEN}成功加载缓存数据，包含 {len(result['stocks'])} 只股票{Colors.RESET}")
            else:
                # 爬取数据
                result = await crawl_robinhood_category(category)
                
                if result:
                    # 保存结果
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    
                    print(f"{Colors.GREEN}成功保存类别 {category['name']} 的数据到 {cache_file}{Colors.RESET}")
                else:
                    print(f"{Colors.RED}未能获取类别 {category['name']} 的数据{Colors.RESET}")
                    continue
            
            category_results.append(result)
                
        except Exception as e:
            print(f"{Colors.RED}处理类别 {category['name']} 时出错: {str(e)}{Colors.RESET}")
    
    # 爬取单个股票详情
    for symbol in STOCK_SEARCH_TERMS:
        try:
            print(f"{Colors.BLUE}===== 开始处理股票: {symbol} ====={Colors.RESET}")
            
            # 检查是否已有缓存数据
            cache_file = output_dir / f"stock_{symbol}_{today}.json"
            if cache_file.exists():
                print(f"{Colors.YELLOW}发现缓存数据，正在加载: {cache_file}{Colors.RESET}")
                continue
            
            # 爬取数据
            result = await crawl_stock_detail(symbol)
            
            if result:
                # 保存结果
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                print(f"{Colors.GREEN}成功保存股票 {symbol} 的详情数据到 {cache_file}{Colors.RESET}")
            else:
                print(f"{Colors.RED}未能获取股票 {symbol} 的详情数据{Colors.RESET}")
                
        except Exception as e:
            print(f"{Colors.RED}处理股票 {symbol} 时出错: {str(e)}{Colors.RESET}")
    
    # 分析股票数据
    if category_results:
        analyze_stocks(category_results, client)
    else:
        print(f"{Colors.RED}没有可用的股票数据进行分析{Colors.RESET}")

if __name__ == "__main__":
    asyncio.run(main())