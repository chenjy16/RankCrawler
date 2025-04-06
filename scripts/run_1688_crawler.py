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
            # 更新选择器以匹配最新的1688页面结构 - 使用更广泛的选择器
            "baseSelector": ".offer-list-row-offer, .sm-offer-item, .grid-offer .offer-item, .organic-offer-list .organic-offer-item, .sm-offer-list .sm-offer-item, .common-offer-card, .card-container, .offer-card, .offer, .item, .product-item, .product-card", 
            "fields": [
                {"name": "product_name", "selector": ".title, .offer-title, .title-text, .title a, h4.title, .title-container, .title-text, .offer-card-title, .product-title, .item-title, a[title]", "type": "text"},
                {"name": "product_url", "selector": ".title a, .offer-title a, a.title-link, h4.title a, .title-container a, .offer-card-title a, a[href*='detail.1688.com'], a[href*='offer']", "type": "attribute", "attribute": "href"},
                {"name": "price", "selector": ".price, .offer-price, .price-text, .price strong, .sm-offer-priceNum, .price-container, .price-info, .offer-price-container, .price-original, .price-current, .price-num", "type": "text"},
                {"name": "sales", "selector": ".sale-quantity, .sales, .volume, .sm-offer-trade, .trade-container, .trade-count, .offer-trade, .transaction, .sold, .deal-cnt", "type": "text"},
                {"name": "shop_name", "selector": ".company-name, .shop-name, .supplier-name, .sm-offer-companyName, .company-container, .company-info, .offer-company, .store-name, .seller-name", "type": "text"},
                {"name": "shop_url", "selector": ".company-name a, .shop-name a, .supplier-link, .sm-offer-companyName a, .company-container a, a[href*='winport.1688.com'], a[href*='shop']", "type": "attribute", "attribute": "href"},
                {"name": "image_url", "selector": ".image img, .offer-image img, .sm-offer-item img, .product-img img, .offer-card-img img, .img img, .pic img, img.offer-image, img[src*='img.alicdn.com']", "type": "attribute", "attribute": "src"},
            ]
        }
    )
    
    # 配置浏览器 - 增强反爬虫能力
    browser_config = BrowserConfig(
        headless=True,
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Referer": "https://www.1688.com/",  # 添加Referer头
            "Cookie": "cna=random; _m_h5_tk=random; _m_h5_tk_enc=random",  # 添加一些基本Cookie
        },
    )
    
    # 创建爬虫运行配置 - 增强等待策略和交互逻辑
    config = CrawlerRunConfig(
        js_code="""
            // 模拟真实用户行为
            async function simulateUserBehavior() {
                // 等待页面完全加载
                await new Promise(r => setTimeout(r, 5000));  // 增加等待时间
                
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
                for (let i = 0; i < 15; i++) {  // 增加滚动次数
                    const scrollAmount = Math.floor(Math.random() * 500) + 200;
                    window.scrollBy(0, scrollAmount);
                    await new Promise(r => setTimeout(r, Math.random() * 800 + 500));  // 增加滚动间隔
                    
                    // 随机暂停，模拟用户查看内容
                    if (i % 3 === 0) {
                        await new Promise(r => setTimeout(r, Math.random() * 2000 + 1000));  // 增加暂停时间
                    }
                }
                
                // 滚动到底部以加载更多内容
                window.scrollTo(0, document.body.scrollHeight * 0.7);
                await new Promise(r => setTimeout(r, 3000));  // 增加等待时间
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(r => setTimeout(r, 3000));  // 增加等待时间
                
                // 尝试点击"加载更多"按钮（如果存在）
                const loadMoreSelectors = [
                    '.load-more', '.sm-pagination-next', '.next-btn', 
                    '.pagination-next', '.next-page', '[data-spm-click*="loadmore"]',
                    '.pagination .next', '.load-more-btn', '.next', '.btn-next',
                    'button:contains("加载更多")', 'a:contains("下一页")'
                ];
                
                for (const selector of loadMoreSelectors) {
                    const loadMoreBtn = document.querySelector(selector);
                    if (loadMoreBtn) {
                        try {
                            loadMoreBtn.click();
                            console.log('点击了加载更多按钮');
                            await new Promise(r => setTimeout(r, 4000));  // 增加等待时间
                            window.scrollTo(0, document.body.scrollHeight);
                            await new Promise(r => setTimeout(r, 3000));  // 增加等待时间
                        } catch (e) {}
                    }
                }
                
                // 最后再滚动一次确保所有内容都已加载
                window.scrollTo(0, 0);
                await new Promise(r => setTimeout(r, 1500));  // 增加等待时间
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(r => setTimeout(r, 3000));  // 增加等待时间
                
                // 检查是否有商品数据并输出调试信息
                const selectors = [
                    '.offer-list-row-offer', '.sm-offer-item', '.grid-offer .offer-item', 
                    '.organic-offer-list .organic-offer-item', '.sm-offer-list .sm-offer-item', 
                    '.common-offer-card', '.card-container', '.offer-card', '.offer', 
                    '.item', '.product-item', '.product-card'
                ];
                
                let productCount = 0;
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        console.log(`找到 ${elements.length} 个商品，使用选择器: ${selector}`);
                        productCount += elements.length;
                    }
                }
                
                console.log(`总共找到 ${productCount} 个商品`);
                
                // 输出页面结构调试信息
                console.log('页面主要容器:');
                ['#sm-offer-list', '.offer-list', '.grid-offer', '.organic-offer-list'].forEach(selector => {
                    const el = document.querySelector(selector);
                    if (el) console.log(`找到容器: ${selector}`);
                });
                
                return true;
            }
            
            return await simulateUserBehavior();
        """,
        # 使用更灵活的等待条件
        wait_for="js:() => {" +
                "const selectors = ['.offer-list', '.sm-offer-list', '.grid-offer', '.offer-item', '.sm-offer-item', '.organic-offer-list', '.common-offer-card', '.card-container', '.offer-card', '.offer', '.item', '.product-item', '.product-card'];" +
                "return selectors.some(selector => document.querySelector(selector) !== null) || document.readyState === 'complete';" +
                "}",
        extraction_strategy=extraction_strategy,
        # 增加页面超时时间
        page_timeout=600000,  # 增加到600秒
        # 添加更多反爬虫设置
        magic=True,  # 启用魔法模式
        simulate_user=True,  # 模拟用户行为
        override_navigator=True,  # 覆盖navigator属性
        delay_before_return_html=12.0,  # 页面加载后额外等待12秒
    )
    
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