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
    from crawl4ai.async_logger import AsyncLogger
except ImportError:
    print("尝试使用替代导入路径...")
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
    from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
    from crawl4ai.async_logger import AsyncLogger

logger = AsyncLogger()

# 确保输出目录存在
output_dir = Path("data/1688")
output_dir.mkdir(parents=True, exist_ok=True)

# 1688类目URL列表
CATEGORIES = [
    {
        "id": "digital_computer",
        "name": "数码电脑",
        "url": "https://s.1688.com/selloffer/offer_search.htm?keywords=%E6%95%B0%E7%A0%81%E7%94%B5%E8%84%91&charset=utf8&sortType=va_sales"
    }
]

async def crawl_1688_category(category):
    """爬取1688类目销量排行数据"""
    logger.info(f"开始爬取类目: {category['name']} (ID: {category['id']})")
    
    # 创建提取策略 - 更新选择器以匹配1688当前DOM结构
    extraction_strategy = JsonCssExtractionStrategy(
        schema={
            "name": "1688类目销量排行",
            # 更新选择器以匹配数码电脑页面
            "baseSelector": ".offer-list .sm-offer-item, .grid-offer .offer-item, .organic-offer-list .organic-offer-item, .sm-offer-list .sm-offer-item", 
            "fields": [
                {"name": "product_name", "selector": ".title, .offer-title, .title-text, .title a, h4.title", "type": "text"},
                {"name": "product_url", "selector": ".title a, .offer-title a, a.title-link, h4.title a", "type": "attribute", "attribute": "href"},
                {"name": "price", "selector": ".price, .offer-price, .price-text, .price strong, .sm-offer-priceNum", "type": "text"},
                {"name": "sales", "selector": ".sale-quantity, .sales, .volume, .sm-offer-trade", "type": "text"},
                {"name": "shop_name", "selector": ".company-name, .shop-name, .supplier-name, .sm-offer-companyName", "type": "text"},
                {"name": "shop_url", "selector": ".company-name a, .shop-name a, .supplier-link, .sm-offer-companyName a", "type": "attribute", "attribute": "href"},
                {"name": "rating", "selector": ".star-rating, .rating, .rate", "type": "text"},
                {"name": "location", "selector": ".location, .address, .sm-offer-location", "type": "text"},
                {"name": "image_url", "selector": ".image img, .offer-image img, .sm-offer-item img", "type": "attribute", "attribute": "src"},
                {"name": "tags", "selector": ".tags, .offer-tags, .sm-offer-tags", "type": "text"},
                {"name": "min_order", "selector": ".min-order, .offer-min-order, .sm-offer-moq", "type": "text"},
                {"name": "delivery_time", "selector": ".delivery-time, .offer-delivery-time", "type": "text"},
            ]
        }
    )
    
    # 配置浏览器 - 移除不支持的locale参数
    browser_config = BrowserConfig(
        headless=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},  # 使用更大的视口
    )
    
    # 创建爬虫运行配置 - 使用更健壮的等待策略
    config = CrawlerRunConfig(
        js_code="""
            // 模拟真实用户行为
            async function simulateUserBehavior() {
                // 随机滚动
                for (let i = 0; i < 8; i++) {
                    const scrollAmount = Math.floor(Math.random() * 500) + 100;
                    window.scrollBy(0, scrollAmount);
                    await new Promise(r => setTimeout(r, Math.random() * 1000 + 500));
                }
                
                // 滚动到底部
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(r => setTimeout(r, 2000));
                
                // 再次滚动确保加载完成
                window.scrollTo(0, document.body.scrollHeight);
                
                // 尝试点击"加载更多"按钮（如果存在）
                const loadMoreBtn = document.querySelector('.load-more, .sm-pagination-next, .next-btn');
                if (loadMoreBtn) {
                    loadMoreBtn.click();
                    await new Promise(r => setTimeout(r, 3000));
                    window.scrollTo(0, document.body.scrollHeight);
                }
                
                return true;
            }
            
            return await simulateUserBehavior();
        """,
        # 使用JavaScript等待条件而不是CSS选择器
        wait_for="js:() => {" +
                "const selectors = ['.offer-list', '.sm-offer-list', '.grid-offer', '.offer-item', '.sm-offer-item', '.organic-offer-list'];" +
                "return selectors.some(selector => document.querySelector(selector) !== null);" +
                "}",
        extraction_strategy=extraction_strategy,
        # 增加页面超时时间
        page_timeout=180000,  # 增加到180秒
        # 添加更多反爬虫设置
        magic=True,  # 启用魔法模式
        simulate_user=True,  # 模拟用户行为
        override_navigator=True,  # 覆盖navigator属性
        delay_before_return_html=5.0,  # 页面加载后额外等待5秒
    )
    
    # 执行爬取
    async with AsyncWebCrawler(config=browser_config) as crawler:
        try:
            result = await crawler.arun(url=category['url'], config=config)
            
            if not result.success:
                # 修复错误处理，使用result.message而不是result.error
                logger.error(f"爬取失败: {result.message if hasattr(result, 'message') else '未知错误'}")
                return None
            
            # 解析结果
            try:
                products = json.loads(result.extracted_content)
                
                # 按销量排序
                def extract_sales_number(sales_text):
                    try:
                        import re
                        if not sales_text:
                            return 0
                        numbers = re.findall(r'\d+', sales_text)
                        if numbers:
                            return int(numbers[0])
                        return 0
                    except:
                        return 0
                
                # 过滤掉没有销量数据的产品
                valid_products = [p for p in products if p.get("sales")]
                
                # 按销量排序
                valid_products.sort(key=lambda x: extract_sales_number(x.get("sales", "0")), reverse=True)
                
                # 截取前100个
                top_products = valid_products[:100]
                
                # 添加排名信息
                for i, product in enumerate(top_products):
                    product["rank"] = i + 1
                
                # 添加元数据
                result_data = {
                    "category_id": category['id'],
                    "category_name": category['name'],
                    "category_url": category['url'],
                    "crawl_time": datetime.now().isoformat(),
                    "total_products": len(valid_products),
                    "products": top_products
                }
                
                return result_data
            except Exception as e:
                logger.error(f"处理数据失败: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"爬取过程中发生错误: {str(e)}")
            return None

async def main():
    """主函数"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    for category in CATEGORIES:
        try:
            result = await crawl_1688_category(category)
            
            if result:
                # 保存结果
                output_file = output_dir / f"{category['id']}_{today}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                logger.info(f"成功保存类目 {category['name']} 的数据到 {output_file}")
            else:
                logger.error(f"未能获取类目 {category['name']} 的数据")
                
        except Exception as e:
            logger.error(f"处理类目 {category['name']} 时出错: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())