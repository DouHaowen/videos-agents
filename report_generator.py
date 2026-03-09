"""
报告生成模块
生成美观的HTML报告
"""

from pathlib import Path
from datetime import datetime


class ReportGenerator:
    def generate_report(self, analysis, output_dir):
        """
        生成HTML报告
        
        Args:
            analysis: 分析结果字典
            output_dir: 输出目录
        
        Returns:
            报告文件路径
        """
        output_dir = Path(output_dir)
        report_path = output_dir / "report.html"
        
        # 生成HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>会议分析报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        .header .date {{
            opacity: 0.9;
            font-size: 14px;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 35px;
        }}
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }}
        .category-badge {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 16px;
            font-weight: 500;
            margin-right: 10px;
        }}
        .subcategory-badge {{
            display: inline-block;
            background: #f0f0f0;
            color: #667eea;
            padding: 6px 15px;
            border-radius: 15px;
            font-size: 14px;
            margin: 5px 5px 5px 0;
        }}
        .summary {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            line-height: 1.8;
            color: #333;
        }}
        .key-points {{
            list-style: none;
        }}
        .key-points li {{
            padding: 12px 0;
            padding-left: 30px;
            position: relative;
            line-height: 1.6;
            color: #555;
        }}
        .key-points li:before {{
            content: "▸";
            position: absolute;
            left: 10px;
            color: #667eea;
            font-size: 18px;
        }}
        .action-items {{
            list-style: none;
        }}
        .action-items li {{
            background: #fff9e6;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            color: #555;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 12px;
            border-top: 1px solid #f0f0f0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 会议分析报告</h1>
            <div class="date">{datetime.now().strftime("%Y年%m月%d日 %H:%M")}</div>
        </div>
        
        <div class="content">
            <div class="section">
                <div class="section-title">🏷️ 场景分类</div>
                <div>
                    <span class="category-badge">{analysis.get('category', '未分类')}</span>
                    <div style="margin-top: 10px;">
                        {self._render_subcategories(analysis.get('subcategories', []))}
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">📝 会议摘要</div>
                <div class="summary">
                    {analysis.get('summary', '无摘要')}
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">💡 主要讨论点</div>
                <ul class="key-points">
                    {self._render_key_points(analysis.get('key_points', []))}
                </ul>
            </div>
            
            {self._render_action_items(analysis.get('action_items', []))}
        </div>
        
        <div class="footer">
            由 AI 会议分析系统自动生成
        </div>
    </div>
</body>
</html>"""
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        return report_path
    
    def _render_subcategories(self, subcategories):
        if not subcategories:
            return ""
        return "".join([
            f'<span class="subcategory-badge">{sub}</span>'
            for sub in subcategories
        ])
    
    def _render_key_points(self, key_points):
        if not key_points:
            return "<li>无讨论点</li>"
        return "".join([f"<li>{point}</li>" for point in key_points])
    
    def _render_action_items(self, action_items):
        if not action_items:
            return ""
        
        items_html = "".join([f"<li>{item}</li>" for item in action_items])
        return f"""
            <div class="section">
                <div class="section-title">✅ 行动项</div>
                <ul class="action-items">
                    {items_html}
                </ul>
            </div>
        """
