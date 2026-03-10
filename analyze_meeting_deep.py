#!/usr/bin/env python3
"""
深度会议分析工具
支持智能分段、待办事项提取、多格式导出
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

from processors.segmenter import MeetingSegmenter
from processors.action_item_extractor import ActionItemExtractor
from exporters.markdown_exporter import MarkdownExporter
from timeline_report_generator import TimelineReportGenerator

load_dotenv()


def analyze_meeting_deep(video_path):
    """深度分析会议视频"""
    
    if not os.path.exists(video_path):
        print(f"错误: 找不到视频文件 {video_path}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"deep_analysis_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    print(f"🎬 开始深度分析会议视频")
    print(f"📹 视频: {video_path}")
    print(f"📁 输出: {session_dir}\n")
    
    # 配置 Gemini
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")
    
    # 步骤 1: 上传并基础分析
    print("=" * 60)
    print("📤 步骤 1/5: 上传视频并进行基础分析...")
    print("=" * 60)
    
    video_file = genai.upload_file(path=video_path)
    print(f"✓ 视频已上传")
    
    # 等待处理
    import time
    while video_file.state.name == "PROCESSING":
        print("⏳ 等待视频处理...")
        time.sleep(2)
        video_file = genai.get_file(video_file.name)
    
    if video_file.state.name == "FAILED":
        raise ValueError("视频处理失败")
    
    print("✓ 视频处理完成")
    
    # 获取转录和基础分析
    print("\n🤖 进行基础分析...")
    
    basic_prompt = """请分析这个会议视频，提供：

1. 会议主题摘要（1-2句话）
2. 主要讨论点（3-5个）
3. 场景分类（工作/私生活/健康/运动/出行）
4. 完整的会议转录文本

请以 JSON 格式返回：
{
  "summary": "会议摘要",
  "key_points": ["讨论点1", "讨论点2"],
  "category": "分类",
  "transcript": "完整转录文本"
}"""
    
    response = model.generate_content(
        [video_file, basic_prompt],
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            response_mime_type="application/json"
        )
    )
    
    basic_analysis = json.loads(response.text)
    transcript = basic_analysis.get("transcript", "")
    
    # 保存基础分析
    with open(session_dir / "basic_analysis.json", "w", encoding="utf-8") as f:
        json.dump(basic_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 基础分析完成")
    print(f"  - 分类: {basic_analysis.get('category', '未知')}")
    print(f"  - 转录长度: {len(transcript)} 字符")
    
    # 步骤 2: 智能分段
    print("\n" + "=" * 60)
    print("🔍 步骤 2/5: 智能分段...")
    print("=" * 60)
    
    segmenter = MeetingSegmenter(model)
    
    # 估算视频时长（从文件获取）
    import cv2
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_duration = frame_count / fps if fps > 0 else 600  # 默认10分钟
    cap.release()
    
    segments = segmenter.segment_meeting(transcript, video_duration)
    
    # 保存分段结果
    with open(session_dir / "segments.json", "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 分段完成，共 {len(segments)} 个议题")
    for seg in segments:
        from processors.segmenter import MeetingSegmenter
        time_str = MeetingSegmenter.format_time(seg['start_time'])
        print(f"  {seg['segment_id']}. [{time_str}] {seg['title']}")
    
    # 步骤 3: 提取待办事项
    print("\n" + "=" * 60)
    print("✅ 步骤 3/5: 提取待办事项...")
    print("=" * 60)
    
    extractor = ActionItemExtractor(model)
    action_items = extractor.extract_action_items(transcript, segments)
    
    # 保存待办事项
    with open(session_dir / "action_items.json", "w", encoding="utf-8") as f:
        json.dump(action_items, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 提取完成，共 {len(action_items)} 个待办事项")
    for i, item in enumerate(action_items, 1):
        print(f"  {i}. {item['task']} (负责人: {item['owner']})")
    
    # 步骤 4: 生成 Markdown 纪要
    print("\n" + "=" * 60)
    print("📝 步骤 4/5: 生成会议纪要...")
    print("=" * 60)
    
    md_exporter = MarkdownExporter()
    meeting_info = {
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "title": "AI 团队会议",
        "duration": MeetingSegmenter.format_time(video_duration)
    }
    
    md_path = md_exporter.export_meeting_minutes(
        basic_analysis,
        segments,
        action_items,
        session_dir,
        meeting_info
    )
    
    print(f"✓ Markdown 纪要已生成: {md_path}")
    
    # 步骤 5: 生成时间轴报告
    print("\n" + "=" * 60)
    print("📊 步骤 5/5: 生成时间轴报告...")
    print("=" * 60)
    
    timeline_gen = TimelineReportGenerator()
    timeline_path = timeline_gen.generate_timeline_report(
        basic_analysis,
        segments,
        action_items,
        session_dir
    )
    
    print(f"✓ 时间轴报告已生成: {timeline_path}")
    
    # 清理
    genai.delete_file(video_file.name)
    
    # 总结
    print("\n" + "=" * 60)
    print("✅ 深度分析完成！")
    print("=" * 60)
    print(f"\n📁 所有文件保存在: {session_dir}")
    print(f"\n📋 生成的文件:")
    print(f"  - basic_analysis.json  (基础分析)")
    print(f"  - segments.json        (分段信息)")
    print(f"  - action_items.json    (待办事项)")
    print(f"  - meeting_minutes.md   (会议纪要)")
    print(f"  - timeline_report.html (时间轴报告)")
    print(f"\n💡 快速查看: open {timeline_path}")


def main():
    if len(sys.argv) < 2:
        print("使用方法: python analyze_meeting_deep.py <视频文件>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    analyze_meeting_deep(video_path)


if __name__ == "__main__":
    main()
