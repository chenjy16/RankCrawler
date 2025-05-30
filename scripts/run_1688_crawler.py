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

async def crawl_1688_category(category, max_retries=3):
    """爬取1688类目销量排行数据"""
    logger.info(f"开始爬取类目: {category['name']} (ID: {category['id']})")
    
    # 创建提取策略 - 更新选择器以匹配1688最新DOM结构
    extraction_strategy = JsonCssExtractionStrategy(
        schema={
            "name": "1688类目销量排行",
            # 根据截图更新基础选择器，专注于商品卡片元素
            "baseSelector": ".grid-offer .offer-item, .grid-offer > div, .offer-list > div, .sm-offer-list > div, .m-offer-list > div, .pc-offer-list > div, .goods-list > div, .search-list > div, .result-list > div, [data-offer-id], [data-spm-anchor-id*='offer']", 
            "fields": [
                # 根据截图中的商品卡片结构更新选择器
                {"name": "product_name", "selector": ".title, .offer-title, h4, a[title], .subject, .name, .product-name", "type": "text"},
                {"name": "product_url", "selector": "a[href*='detail.1688.com'], a[href*='offer'], a.item-link, a.product-link, a.offer-link", "type": "attribute", "attribute": "href"},
                {"name": "price", "selector": ".price, .offer-price, [class*='price']", "type": "text"},
                {"name": "sales", "selector": ".sale-quantity, .sales, [class*='sale'], [class*='trade']", "type": "text"},
                {"name": "shop_name", "selector": ".company-name, .shop-name, .supplier-name, [class*='company'], [class*='shop']", "type": "text"},
                {"name": "shop_url", "selector": ".company-name a, .shop-name a, a[href*='winport.1688.com'], a[href*='shop'], a[href*='company']", "type": "attribute", "attribute": "href"},
                {"name": "image_url", "selector": "img[src*='img.alicdn.com'], img.offer-image, img.main, img.primary, img.product-img, img[alt], img[src]", "type": "attribute", "attribute": "src"},
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
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.1688.com/",
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
                const closeButtons = document.querySelectorAll('.close-btn, .modal-close, .popup-close, .dialog-close, .btn-close, .close, button[aria-label="Close"], .baxia-dialog-close');
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
                
                // 根据截图分析页面结构
                console.log('分析页面结构...');
                
                // 直接分析商品元素
                const productElements = document.querySelectorAll('.grid-offer .offer-item, .grid-offer > div, .offer-list > div, [data-offer-id]');
                console.log(`找到 ${productElements.length} 个商品元素`);
                
                if (productElements.length > 0) {
                    // 分析第一个商品元素的结构
                    const firstProduct = productElements[0];
                    console.log('第一个商品元素类名:', firstProduct.className);
                    console.log('第一个商品元素HTML:', firstProduct.outerHTML.substring(0, 300));
                    
                    // 尝试提取关键信息
                    const productInfo = {
                        name: firstProduct.querySelector('.title, h4, a[title]')?.textContent?.trim(),
                        url: firstProduct.querySelector('a[href*="detail"], a[href*="offer"]')?.href,
                        price: firstProduct.querySelector('.price, [class*="price"]')?.textContent?.trim(),
                        sales: firstProduct.querySelector('.sale-quantity, .sales, [class*="sale"], [class*="trade"]')?.textContent?.trim(),
                        image: firstProduct.querySelector('img')?.src
                    };
                    
                    console.log('提取到的商品信息:', productInfo);
                }
                
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
            logger.info(f"尝试第 {attempt+1}/{max_retries} 次爬取")
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=category['url'], config=config)
                
                if not result.success:
                    logger.error(f"爬取失败: {result.message if hasattr(result, 'message') else '未知错误'}")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 递增等待时间
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time)
                        continue
                    return None
                
                # 检查是否有提取到内容
                if not result.extracted_content or result.extracted_content == "[]":
                    logger.error("提取内容为空，可能选择器不匹配")
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5
                        logger.info(f"等待 {wait_time} 秒后重试...")
                        await asyncio.sleep(wait_time)
                        continue
                    return None
                
                # 解析结果
                try:
                    products = json.loads(result.extracted_content)
                    
                    # 记录原始数据数量
                    logger.info(f"提取到 {len(products)} 个商品")
                    
                    # 按销量排序
                    def extract_sales_number(sales_text):
                        try:
                            import re
                            if not sales_text:
                                return 0
                            # 匹配数字，包括带单位的数字（如1万+）
                            numbers = re.findall(r'(\d+(?:\.\d+)?)[万+]*', sales_text)
                            if not numbers:
                                return 0
                                
                            num = float(numbers[0])
                            # 处理"万"单位
                            if "万" in sales_text:
                                num *= 10000
                            return int(num)
                        except:
                            return 0
                    
                    # 过滤掉没有销量数据的产品
                    valid_products = [p for p in products if p.get("sales")]
                    logger.info(f"有效商品（含销量数据）: {len(valid_products)} 个")
                    
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
                    if attempt < max_retries - 1:
                        continue
                    return None
        except Exception as e:
            logger.error(f"爬取过程中发生错误: {str(e)}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                logger.info(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
                continue
            return None
    
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