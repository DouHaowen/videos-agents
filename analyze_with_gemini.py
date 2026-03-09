#!/usr/bin/env python3
"""
使用 Gemini 多模态能力直接分析会议视频
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

from report_generator import ReportGenerator

load_dotenv()


def upload_video(video_path, client):
    """上传视频到 Gemini"""
    print(f"📤 上传视频到 Gemini...")
    video_file = genai.upload_file(path=video_path)
    print(f"✓ 上传完成: {video_file.name}")
    
    # 等待视频处理完成
    while video_file.state.name == "PROCESSING":
        print("⏳ 等待视频处理...")
        time.sleep(2)
        video_file = genai.get_file(video_file.name)
    
    if video_file.state.name == "FAILED":
        raise ValueError("视频处理失败")
    
    print("✓ 视频处理完成")
    return video_file


def analyze_video(video_file, model):
    """使用 Gemini 分析视频"""
    prompt = """请仔细观看和分析这个会议视频，提供以下信息：

1. **会议主题摘要**（1-2句话概括会议的核心内容）
2. **主要讨论点**（列出3-5个关键讨论点）
3. **场景分类**（从以下类别中选择最合适的主分类和子分类）：
   - 工作：会议、电话、头脑风暴、项目讨论
   - 私生活：社交、休闲、家庭
   - 健康/休息：睡眠、放松、冥想
   - 运动：跑步、健身、游泳、其他运动
   - 出行：通勤、旅行、飞行
4. **关键决策或行动项**（如果有的话）

请以JSON格式返回，包含以下字段：
{
  "summary": "会议摘要文本",
  "key_points": ["讨论点1", "讨论点2", "讨论点3"],
  "category": "主分类名称",
  "subcategories": ["子分类1", "子分类2"],
  "action_items": ["行动项1", "行动项2"]
}

注意：
- 请基于视频中的画面和声音进行综合分析
- 如果没有明确的行动项，action_items 可以是空列表
- 子分类可以有多个，选择最相关的
"""
    
    print("\n🤖 Gemini 正在分析视频...")
    response = model.generate_content(
        [video_file, prompt],
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json"
        )
    )
    
    return json.loads(response.text)


def main():
    if len(sys.argv) < 2:
        print("使用方法: python analyze_with_gemini.py <视频文件路径>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"错误: 找不到视频文件 {video_path}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"meeting_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    print(f"🎬 开始分析视频: {video_path}")
    print(f"📁 输出目录: {session_dir}")
    
    # 配置 Gemini
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    # 上传并分析视频
    video_file = upload_video(video_path, genai)
    analysis = analyze_video(video_file, model)
    
    # 保存分析结果
    analysis_path = session_dir / "analysis.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"✓ 分析完成")
    
    # 生成报告
    print("\n📊 生成报告...")
    generator = ReportGenerator()
    report_path = generator.generate_report(analysis, session_dir)
    print(f"✓ 报告已生成: {report_path}")
    
    # 清理上传的文件
    genai.delete_file(video_file.name)
    print("✓ 已清理临时文件")
    
    print(f"\n✅ 分析完成！所有文件保存在: {session_dir}")
    print(f"\n📋 会议摘要:")
    print(f"   主题: {analysis.get('summary', '未知')}")
    print(f"   分类: {analysis.get('category', '未知')}")
    if 'subcategories' in analysis and analysis['subcategories']:
        print(f"   子分类: {', '.join(analysis['subcategories'])}")
    if 'action_items' in analysis and analysis['action_items']:
        print(f"   行动项: {len(analysis['action_items'])} 项")


if __name__ == "__main__":
    main()
