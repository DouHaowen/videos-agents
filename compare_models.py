#!/usr/bin/env python3
"""
多模型对比分析工具
同时使用多个AI模型分析同一个视频，对比效果
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from analyzers import get_analyzer, get_available_models
from report_generator import ReportGenerator

load_dotenv()


def compare_models(video_path, models=None):
    """
    使用多个模型分析视频并对比结果
    
    Args:
        video_path: 视频文件路径
        models: 要使用的模型列表，None表示使用所有可用模型
    """
    if not os.path.exists(video_path):
        print(f"错误: 找不到视频文件 {video_path}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"comparison_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    print(f"🎬 开始多模型对比分析")
    print(f"📹 视频: {video_path}")
    print(f"📁 输出: {session_dir}\n")
    
    # 确定要使用的模型
    if models is None:
        models = get_available_models()
    
    # API密钥映射
    api_keys = {
        "gemini": os.getenv("GOOGLE_API_KEY"),
        "gpt4o": os.getenv("OPENAI_API_KEY"),
        "claude": os.getenv("ANTHROPIC_API_KEY"),
        "qwen": os.getenv("DASHSCOPE_API_KEY")
    }
    
    results = {}
    
    # 逐个模型分析
    for model_name in models:
        api_key = api_keys.get(model_name)
        if not api_key:
            print(f"⚠️  跳过 {model_name}: 未配置API密钥")
            continue
        
        print(f"\n{'='*60}")
        print(f"🤖 使用 {model_name.upper()} 分析...")
        print(f"{'='*60}")
        
        try:
            # 创建模型专属目录
            model_dir = session_dir / model_name
            model_dir.mkdir(exist_ok=True)
            
            # 获取分析器
            analyzer = get_analyzer(model_name, api_key)
            
            # 分析视频
            result = analyzer.analyze_video(video_path, model_dir)
            results[model_name] = result
            
            # 保存结果
            result_path = model_dir / "analysis.json"
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            # 生成报告
            generator = ReportGenerator()
            report_path = generator.generate_report(result, model_dir)
            
            print(f"✅ {analyzer.model_name} 完成")
            print(f"   ⏱️  处理时间: {result['processing_time']:.2f}秒")
            print(f"   📊 分类: {result.get('category', '未知')}")
            
        except Exception as e:
            print(f"❌ {model_name} 失败: {str(e)}")
            results[model_name] = {"error": str(e)}
    
    # 生成对比报告
    print(f"\n{'='*60}")
    print("📊 生成对比报告...")
    comparison_report = generate_comparison_report(results, session_dir)
    print(f"✅ 对比报告: {comparison_report}")
    
    print(f"\n✅ 所有分析完成！")
    print(f"📁 结果保存在: {session_dir}")


def generate_comparison_report(results, output_dir):
    """生成对比报告"""
    output_dir = Path(output_dir)
    report_path = output_dir / "comparison.html"
    
    # 构建对比表格
    models_html = ""
    for model_name, result in results.items():
        if "error" in result:
            models_html += f"""
            <div class="model-card error">
                <h3>{model_name.upper()}</h3>
                <p class="error-msg">❌ 分析失败: {result['error']}</p>
            </div>
            """
        else:
            subcats = ", ".join(result.get('subcategories', []))
            action_items = "<br>".join([f"• {item}" for item in result.get('action_items', [])])
            if not action_items:
                action_items = "无"
            
            models_html += f"""
            <div class="model-card">
                <h3>{model_name.upper()}</h3>
                <div class="metric">
                    <span class="label">处理时间:</span>
                    <span class="value">{result.get('processing_time', 0):.2f}秒</span>
                </div>
                <div class="metric">
                    <span class="label">分类:</span>
                    <span class="value category">{result.get('category', '未知')}</span>
                </div>
                <div class="metric">
                    <span class="label">子分类:</span>
                    <span class="value">{subcats or '无'}</span>
                </div>
                <div class="section">
                    <div class="label">摘要:</div>
                    <div class="summary">{result.get('summary', '无')}</div>
                </div>
                <div class="section">
                    <div class="label">行动项:</div>
                    <div class="actions">{action_items}</div>
                </div>
                <a href="{model_name}/report.html" class="view-detail">查看详细报告 →</a>
            </div>
            """
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>多模型对比分析</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}
        .header h1 {{
            font-size: 42px;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        .header p {{
            opacity: 0.9;
            font-size: 16px;
        }}
        .models-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 30px;
        }}
        .model-card {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s;
        }}
        .model-card:hover {{
            transform: translateY(-5px);
        }}
        .model-card.error {{
            background: #fff5f5;
            border: 2px solid #fc8181;
        }}
        .model-card h3 {{
            color: #1e3c72;
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #2a5298;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
        }}
        .label {{
            font-weight: 600;
            color: #555;
        }}
        .value {{
            color: #333;
        }}
        .value.category {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 14px;
        }}
        .section {{
            margin-top: 20px;
        }}
        .summary {{
            background: #f8f9ff;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
            line-height: 1.6;
            color: #555;
        }}
        .actions {{
            margin-top: 10px;
            color: #555;
            line-height: 1.8;
        }}
        .view-detail {{
            display: inline-block;
            margin-top: 20px;
            color: #2a5298;
            text-decoration: none;
            font-weight: 600;
            transition: color 0.3s;
        }}
        .view-detail:hover {{
            color: #1e3c72;
        }}
        .error-msg {{
            color: #c53030;
            padding: 15px;
            background: white;
            border-radius: 8px;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 多模型对比分析</h1>
            <p>同一视频，不同AI的理解</p>
        </div>
        
        <div class="models-grid">
            {models_html}
        </div>
    </div>
</body>
</html>"""
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    return report_path


def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python compare_models.py <视频文件> [模型1 模型2 ...]")
        print("\n可用模型: gemini, gpt4o, claude, qwen")
        print("\n示例:")
        print("  python compare_models.py video.mp4              # 使用所有模型")
        print("  python compare_models.py video.mp4 gemini gpt4o # 只使用指定模型")
        sys.exit(1)
    
    video_path = sys.argv[1]
    models = sys.argv[2:] if len(sys.argv) > 2 else None
    
    compare_models(video_path, models)


if __name__ == "__main__":
    main()
