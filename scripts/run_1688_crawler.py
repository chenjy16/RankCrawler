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
            # 简化基础选择器，专注于最可能的元素
            "baseSelector": ".offer-item, .sm-offer-item, .item, .product-item, [data-offer-id], [data-spm-anchor-id*='offer'], .offer-list > div, .sm-offer-list > div, .grid-offer > div, .organic-offer-list > div, .m-gallery2 > div, .m-offer-list > div, .pc-offer-list > div, .goods-list > div, .search-list > div, .result-list > div, .list-items > div, .list-container > div, .offer-container > div, .product-container > div, .goods-container > div, .search-container > div, .result-container > div", 
            "fields": [
                # 保持现有字段选择器不变
                {"name": "product_name", "selector": ".title, .offer-title, .title-text, .title a, h4.title, .title-container, .title-text, .offer-card-title, .product-title, .item-title, a[title], .subject, .name, .product-name, .product-info .name, .description, .desc, .product-info .title, .product-info h4, .product-info a", "type": "text"},
                {"name": "product_url", "selector": ".title a, .offer-title a, a.title-link, h4.title a, .title-container a, .offer-card-title a, a[href*='detail.1688.com'], a[href*='offer'], a.item-link, a.product-link, a.offer-link, a[data-spm-anchor-id*='offer'], a[href*='detail'], a[href*='product'], a[href*='item']", "type": "attribute", "attribute": "href"},
                {"name": "price", "selector": ".price, .offer-price, .price-text, .price strong, .sm-offer-priceNum, .price-container, .price-info, .offer-price-container, .price-original, .price-current, .price-num, .value, .price-value, .price-area, .price-wrap, .price-box, [class*='price']", "type": "text"},
                {"name": "sales", "selector": ".sale-quantity, .sales, .volume, .sm-offer-trade, .trade-container, .trade-count, .offer-trade, .transaction, .sold, .deal-cnt, .sale, .sale-num, .sale-count, .trade, .trade-amount, [class*='sale'], [class*='trade']", "type": "text"},
                {"name": "shop_name", "selector": ".company-name, .shop-name, .supplier-name, .sm-offer-companyName, .company-container, .company-info, .offer-company, .store-name, .seller-name, .supplier, .merchant, .vendor, .store, .shop, [class*='company'], [class*='shop']", "type": "text"},
                {"name": "shop_url", "selector": ".company-name a, .shop-name a, .supplier-link, .sm-offer-companyName a, .company-container a, a[href*='winport.1688.com'], a[href*='shop'], a[href*='company'], a.company-link, a.shop-link, a.supplier-link, a[data-spm-anchor-id*='company']", "type": "attribute", "attribute": "href"},
                {"name": "image_url", "selector": ".image img, .offer-image img, .sm-offer-item img, .product-img img, .offer-card-img img, .img img, .pic img, img.offer-image, img[src*='img.alicdn.com'], .product-image img, .item-image img, .main-pic img, .pic-box img, img.main, img.primary, img.product-img, img[alt], img[src]", "type": "attribute", "attribute": "src"},
            ]
        }
    )
    
    # 配置浏览器 - 增强反爬虫能力
    browser_config = BrowserConfig(
        headless=False,  # 改为非无头模式，更容易通过反爬检测
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
        headers={
            # 保持现有headers不变
        },
    )
    
    # 创建爬虫运行配置 - 增强等待策略和交互逻辑
    config = CrawlerRunConfig(
        js_code="""
            // 模拟真实用户行为
            async function simulateUserBehavior() {
                // 等待页面完全加载
                await new Promise(r => setTimeout(r, 12000));  // 增加等待时间到12秒
                
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
                
                // 添加调试信息 - 输出页面结构
                console.log('页面DOM结构分析:');
                
                // 分析页面主要容器
                const containers = [
                    '.offer-list', '.sm-offer-list', '.grid-offer', '.organic-offer-list',
                    '.m-gallery2', '.m-offer-list', '.m-content', '.m-item-list',
                    '#sm-offer-list', '#offer-list', '.list-content', '.search-content',
                    '.pc-offer-list', '.pc-offer', '.offer-container', '.product-list',
                    '.goods-list', '.item-list', '.search-list', '.result-list',
                    // 添加新的可能容器
                    '.list-items', '.list-container', '.search-container', '.result-container',
                    '.items-container', '.products-container', '.goods-container',
                    '.search-results', '.result-items', '.offer-results', '.product-results'
                ];
                
                // 记录所有找到的容器
                let foundContainers = [];
                
                for (const selector of containers) {
                    const container = document.querySelector(selector);
                    if (container) {
                        console.log(`找到容器: ${selector}, 子元素数量: ${container.children.length}`);
                        foundContainers.push({
                            selector: selector,
                            childCount: container.children.length,
                            firstChildClass: container.children.length > 0 ? container.children[0].className : 'none'
                        });
                        
                        // 输出第一个子元素的类名，帮助确定正确的选择器
                        if (container.children.length > 0) {
                            console.log(`第一个子元素类名: ${container.children[0].className}`);
                            console.log(`第一个子元素HTML: ${container.children[0].outerHTML.substring(0, 200)}...`);
                        }
                    }
                }
                
                // 如果没有找到任何容器，尝试分析页面结构
                if (foundContainers.length === 0) {
                    console.log('未找到任何已知容器，分析页面结构...');
                    
                    // 获取所有可能的商品容器
                    const allDivs = document.querySelectorAll('div');
                    const potentialContainers = Array.from(allDivs).filter(div => {
                        // 查找包含多个子元素的div，可能是商品列表
                        return div.children.length > 5 && 
                               (div.className.includes('list') || 
                                div.className.includes('item') || 
                                div.className.includes('offer') || 
                                div.className.includes('product') || 
                                div.className.includes('goods') || 
                                div.className.includes('result'));
                    });
                    
                    console.log(`找到 ${potentialContainers.length} 个潜在商品容器`);
                    
                    // 输出前3个潜在容器的信息
                    potentialContainers.slice(0, 3).forEach((container, index) => {
                        console.log(`潜在容器 ${index+1}:`);
                        console.log(`- 类名: ${container.className}`);
                        console.log(`- 子元素数量: ${container.children.length}`);
                        console.log(`- 第一个子元素类名: ${container.children.length > 0 ? container.children[0].className : 'none'}`);
                        console.log(`- HTML片段: ${container.outerHTML.substring(0, 200)}...`);
                    });
                }
                
                // 尝试查找所有可能的商品元素
                const selectors = [
                    '[data-offer-id]', 
                    '[data-spm-anchor-id*="offer"]', 
                    '.item', 
                    '.product-item', 
                    '.offer',
                    '.goods-item',
                    '.search-item',
                    '.result-item',
                    '.product',
                    '.offer-card',
                    '.product-card',
                    '.item-card',
                    '.goods-card',
                    '.search-card',
                    '.result-card',
                    // 添加新的可能选择器
                    '[data-index]',
                    '[data-product-id]',
                    '[data-item-id]',
                    '[data-goods-id]',
                    '[data-spm]',
                    '.list-item',
                    '.search-result-item',
                    '.product-list-item',
                    '.offer-list-item',
                    '.goods-list-item'
                ];
                
                // 对每个选择器进行查询并记录结果
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    if (elements.length > 0) {
                        console.log(`选择器 "${selector}" 找到 ${elements.length} 个元素`);
                        if (elements.length > 0) {
                            console.log(`- 第一个元素类名: ${elements[0].className}`);
                            console.log(`- HTML片段: ${elements[0].outerHTML.substring(0, 200)}...`);
                        }
                    }
                }
                
                // 输出页面HTML结构，帮助分析
                console.log('页面HTML结构:');
                console.log(document.documentElement.outerHTML.substring(0, 5000) + '...');
                
                // 尝试直接提取商品信息并输出
                try {
                    const products = [];
                    // 尝试多种可能的商品容器选择器
                    const itemSelectors = [
                        '.offer-item', '.sm-offer-item', '.item', '.product-item', 
                        '[data-offer-id]', '[data-spm-anchor-id*="offer"]', 
                        '.offer-list > div', '.sm-offer-list > div', '.grid-offer > div',
                        '.list-items > div', '.list-container > div'
                    ];
                    
                    for (const selector of itemSelectors) {
                        const items = document.querySelectorAll(selector);
                        if (items.length > 0) {
                            console.log(`使用选择器 "${selector}" 找到 ${items.length} 个商品`);
                            
                            // 尝试从第一个商品中提取信息
                            const firstItem = items[0];
                            const productInfo = {
                                name: firstItem.querySelector('.title, .offer-title, h4, a[title]')?.textContent?.trim(),
                                url: firstItem.querySelector('a[href*="detail"], a[href*="offer"]')?.href,
                                price: firstItem.querySelector('.price, [class*="price"]')?.textContent?.trim(),
                                sales: firstItem.querySelector('.sale-quantity, .sales, [class*="sale"], [class*="trade"]')?.textContent?.trim()
                            };
                            
                            console.log('提取到的第一个商品信息:', productInfo);
                            break;
                        }
                    }
                } catch (e) {
                    console.log('尝试直接提取商品信息失败:', e);
                }
                
                return true;
            }
            
            return await simulateUserBehavior();
        """,
        # 使用更灵活的等待条件
        wait_for="networkidle",  # 改为等待网络空闲
        extraction_strategy=extraction_strategy,
        # 增加页面超时时间
        page_timeout=600000,  # 保持600秒
        # 添加更多反爬虫设置
        magic=True,  # 启用魔法模式
        simulate_user=True,  # 模拟用户行为
        override_navigator=True,  # 覆盖navigator属性
        delay_before_return_html=30.0,  # 增加到30秒
        verbose=True,  # 启用详细日志
        # 添加截图功能，帮助调试
        screenshot=True,
        screenshot_path=str(Path("debug/screenshots").absolute()),
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