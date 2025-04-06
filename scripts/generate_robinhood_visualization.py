#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from pathlib import Path
from datetime import datetime
import re

# 定义路径
DATA_DIR = Path("data/robinhood")
VIZ_DIR = Path("docs/visualization/robinhood")
MAIN_PAGE = Path("docs/robinhood_stocks.html")

# 确保目录存在
VIZ_DIR.mkdir(parents=True, exist_ok=True)

def get_latest_data_files():
    """获取每个类别的最新数据文件"""
    latest_files = {}
    
    # 获取类别数据文件
    for file in DATA_DIR.glob("*.json"):
        if file.name.startswith("stock_analysis_"):
            continue
            
        if file.name.startswith("stock_"):
            # 股票详情文件
            match = re.match(r'stock_([A-Z]+)_(\d{4}-\d{2}-\d{2})\.json', file.name)
            if match:
                symbol = match.group(1)
                date_str = match.group(2)
                
                if f"stock_{symbol}" not in latest_files or date_str > latest_files[f"stock_{symbol}"][1]:
                    latest_files[f"stock_{symbol}"] = (file, date_str)
        else:
            # 类别文件
            match = re.match(r'(.+)_(\d{4}-\d{2}-\d{2})\.json', file.name)
            if match:
                category_id = match.group(1)
                date_str = match.group(2)
                
                if category_id not in latest_files or date_str > latest_files[category_id][1]:
                    latest_files[category_id] = (file, date_str)
    
    # 获取最新的分析文件
    analysis_files = list(DATA_DIR.glob("stock_analysis_*.json"))
    if analysis_files:
        latest_analysis = max(analysis_files, key=lambda f: f.stat().st_mtime)
        latest_files["analysis"] = (latest_analysis, "")
    
    return {k: v[0] for k, v in latest_files.items()}

def extract_percent_change(percent_text):
    """从百分比文本中提取数值"""
    if not percent_text:
        return 0
        
    # 移除所有非数字、小数点和正负号字符
    cleaned_text = ''.join(c for c in percent_text if c.isdigit() or c in '.-+')
    
    # 尝试转换为浮点数
    try:
        return float(cleaned_text)
    except ValueError:
        print(f"无法解析百分比文本: {percent_text}")
        return 0
        
    # 匹配数字，包括带符号的百分比
    match = re.search(r'([+-]?\d+(?:\.\d+)?)%?', percent_text)
    if match:
        return float(match.group(1))
    return 0

def generate_category_chart(category_data, category_id):
    """生成类别股票图表HTML"""
    if not category_data or "stocks" not in category_data or not category_data["stocks"]:
        return ""
    
    stocks = category_data["stocks"][:10]  # 取前10只股票
    
    # 提取数据
    symbols = [stock.get("stock_symbol", "未知") for stock in stocks]
    names = [stock.get("stock_name", "未知") for stock in stocks]
    prices = [stock.get("stock_price", "0").replace("$", "").replace(",", "") for stock in stocks]
    percent_changes = [extract_percent_change(stock.get("percent_change", "0%")) for stock in stocks]
    
    # 生成颜色列表（涨为绿色，跌为红色）
    colors = ["#4CAF50" if change >= 0 else "#F44336" for change in percent_changes]
    
    # 生成图表HTML
    chart_html = f"""
    <div class="chart-container">
        <h3>{category_data["category_name"]}</h3>
        <canvas id="{category_id}_chart"></canvas>
        <script>
            new Chart(document.getElementById('{category_id}_chart').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(symbols)},
                    datasets: [{{
                        label: '涨跌幅 (%)',
                        data: {json.dumps(percent_changes)},
                        backgroundColor: {json.dumps(colors)},
                        borderColor: {json.dumps(colors)},
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'top',
                        }},
                        title: {{
                            display: true,
                            text: '{category_data["category_name"]} - 涨跌幅排行'
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return [
                                        '股票: ' + {json.dumps(names)}[context.dataIndex],
                                        '价格: $' + {json.dumps(prices)}[context.dataIndex],
                                        '涨跌幅: ' + context.raw + '%'
                                    ];
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: false,
                            title: {{
                                display: true,
                                text: '涨跌幅 (%)'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </div>
    """
    return chart_html

def generate_analysis_chart(analysis_data):
    """生成股票分析图表HTML"""
    if not analysis_data or "scores" not in analysis_data or not analysis_data["scores"]:
        return ""
    
    scores = analysis_data["scores"]
    
    # 提取数据
    symbols = [score.get("stock_symbol", "未知") for score in scores]
    names = [score.get("stock_name", "未知") for score in scores]
    score_values = [score.get("score", 0) for score in scores]
    recommendations = [score.get("recommendation", "未知") for score in scores]
    reasons = [score.get("reason", "无") for score in scores]
    
    # 生成颜色列表（根据评分高低）
    colors = []
    for score in score_values:
        if score >= 80:
            colors.append("#4CAF50")  # 绿色
        elif score >= 60:
            colors.append("#FFC107")  # 黄色
        else:
            colors.append("#F44336")  # 红色
    
    # 生成图表HTML
    chart_html = f"""
    <div class="chart-container">
        <h3>股票投资评分分析</h3>
        <canvas id="analysis_chart"></canvas>
        <script>
            new Chart(document.getElementById('analysis_chart').getContext('2d'), {{
                type: 'bar',
                data: {{
                    labels: {json.dumps(symbols)},
                    datasets: [{{
                        label: '投资评分',
                        data: {json.dumps(score_values)},
                        backgroundColor: {json.dumps(colors)},
                        borderColor: {json.dumps(colors)},
                        borderWidth: 1
                    }}]
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            position: 'top',
                        }},
                        title: {{
                            display: true,
                            text: '股票投资评分分析'
                        }},
                        tooltip: {{
                            callbacks: {{
                                label: function(context) {{
                                    return [
                                        '股票: ' + {json.dumps(names)}[context.dataIndex],
                                        '评分: ' + context.raw + '/100',
                                        '建议: ' + {json.dumps(recommendations)}[context.dataIndex],
                                        '理由: ' + {json.dumps(reasons)}[context.dataIndex]
                                    ];
                                }}
                            }}
                        }}
                    }},
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100,
                            title: {{
                                display: true,
                                text: '投资评分'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
    </div>
    """
    return chart_html

def generate_stock_table(category_data):
    """生成股票数据表格HTML"""
    if not category_data or "stocks" not in category_data or not category_data["stocks"]:
        return ""
    
    stocks = category_data["stocks"][:20]  # 取前20只股票
    
    # 生成表格HTML
    table_html = f"""
    <div class="table-container">
        <h3>{category_data["category_name"]}</h3>
        <table class="stock-table">
            <thead>
                <tr>
                    <th>排名</th>
                    <th>代码</th>
                    <th>名称</th>
                    <th>价格</th>
                    <th>涨跌额</th>
                    <th>涨跌幅</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for stock in stocks:
        percent_change = stock.get("percent_change", "0%")
        price_change = stock.get("price_change", "$0")
        
        # 根据涨跌设置颜色
        color_class = ""
        if percent_change and ("+" in percent_change or percent_change.startswith("0.00%")):
            color_class = "positive"
        elif percent_change and "-" in percent_change:
            color_class = "negative"
        
        table_html += f"""
                <tr>
                    <td>{stock.get("rank", "")}</td>
                    <td>{stock.get("stock_symbol", "")}</td>
                    <td>{stock.get("stock_name", "")}</td>
                    <td>{stock.get("stock_price", "")}</td>
                    <td class="{color_class}">{price_change}</td>
                    <td class="{color_class}">{percent_change}</td>
                </tr>
        """
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    return table_html

def generate_analysis_table(analysis_data):
    """生成股票分析表格HTML"""
    if not analysis_data or "scores" not in analysis_data or not analysis_data["scores"]:
        return ""
    
    scores = analysis_data["scores"]
    
    # 生成表格HTML
    table_html = """
    <div class="table-container">
        <h3>股票投资分析结果</h3>
        <table class="stock-table">
            <thead>
                <tr>
                    <th>代码</th>
                    <th>名称</th>
                    <th>评分</th>
                    <th>建议</th>
                    <th>分析理由</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for score in scores:
        score_value = score.get("score", 0)
        
        # 根据评分设置颜色
        color_class = ""
        if score_value >= 80:
            color_class = "positive"
        elif score_value >= 60:
            color_class = "neutral"
        else:
            color_class = "negative"
        
        table_html += f"""
                <tr>
                    <td>{score.get("stock_symbol", "")}</td>
                    <td>{score.get("stock_name", "")}</td>
                    <td class="{color_class}">{score_value}/100</td>
                    <td class="{color_class}">{score.get("recommendation", "")}</td>
                    <td>{score.get("reason", "")}</td>
                </tr>
        """
    
    table_html += """
            </tbody>
        </table>
    </div>
    """
    return table_html

def generate_main_page(data_files):
    """生成主页HTML"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 加载数据
    category_data = {}
    analysis_data = None
    
    for key, file_path in data_files.items():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if key == "analysis":
                    analysis_data = data
                else:
                    category_data[key] = data
        except Exception as e:
            print(f"加载数据文件 {file_path} 时出错: {str(e)}")
    
    # 生成图表和表格HTML
    charts_html = ""
    tables_html = ""
    
    # 添加类别图表和表格
    for category_id, data in category_data.items():
        if not category_id.startswith("stock_"):  # 只处理类别数据
            charts_html += generate_category_chart(data, category_id)
            tables_html += generate_stock_table(data)
    
    # 添加分析图表和表格（如果有分析数据）
    if analysis_data and "scores" in analysis_data and analysis_data["scores"]:
        charts_html += generate_analysis_chart(analysis_data)
        tables_html += generate_analysis_table(analysis_data)
    
    # 生成完整HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Robinhood股票数据分析 - {today}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        header {{
            background-color: #1e88e5;
            color: white;
            padding: 20px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            margin: 0;
            padding: 0;
        }}
        .update-info {{
            font-size: 0.9em;
            margin-top: 10px;
            color: rgba(255,255,255,0.8);
        }}
        .charts-section, .tables-section {{
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .section-title {{
            border-bottom: 2px solid #1e88e5;
            padding-bottom: 10px;
            margin-bottom: 20px;
            color: #1e88e5;
        }}
        .chart-container {{
            margin-bottom: 30px;
        }}
        .table-container {{
            margin-bottom: 30px;
            overflow-x: auto;
        }}
        .stock-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        .stock-table th, .stock-table td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .stock-table th {{
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .stock-table tr:hover {{
            background-color: #f5f5f5;
        }}
        .positive {{
            color: #4CAF50;
        }}
        .negative {{
            color: #F44336;
        }}
        .neutral {{
            color: #FFC107;
        }}
        footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}
            .stock-table th, .stock-table td {{
                padding: 8px 10px;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>Robinhood股票数据分析</h1>
        <p class="update-info">最后更新: {today}</p>
    </header>
    
    <div class="container">
        <div class="charts-section">
            <h2 class="section-title">股票数据可视化</h2>
            {charts_html}
        </div>
        
        <div class="tables-section">
            <h2 class="section-title">股票数据表格</h2>
            {tables_html}
        </div>
    </div>
    
    <footer>
        <p>数据来源: Robinhood | 由GitHub Actions自动爬取并生成</p>
    </footer>
</body>
</html>
"""
    
    # 保存HTML文件
    with open(MAIN_PAGE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"主页已生成: {MAIN_PAGE}")

def main():
    """主函数"""
    print("开始生成Robinhood股票数据可视化...")
    
    # 获取最新数据文件
    data_files = get_latest_data_files()
    
    if not data_files:
        print("未找到任何数据文件，无法生成可视化")
        return
    
    # 生成主页
    generate_main_page(data_files)
    
    print("Robinhood股票数据可视化生成完成")

if __name__ == "__main__":
    main()