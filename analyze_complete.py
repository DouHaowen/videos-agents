#!/usr/bin/env python3
"""
完整版会议分析工具
整合所有功能：智能分段、发言人识别、决策点检测、多格式导出、知识库管理
"""

import os
import sys
import json
import cv2
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai

from processors.segmenter import MeetingSegmenter
from processors.action_item_extractor import ActionItemExtractor
from processors.speaker_diarizer import SpeakerDiarizer
from processors.decision_detector import DecisionDetector
from exporters.markdown_exporter import MarkdownExporter
from exporters.pdf_exporter import PDFExporter
from timeline_report_generator import TimelineReportGenerator
from knowledge.database import MeetingDatabase
from knowledge.search import MeetingSearchEngine

load_dotenv()


def analyze_meeting_complete(video_path, save_to_db=True):
    """完整的会议分析流程"""
    
    if not os.path.exists(video_path):
        print(f"错误: 找不到视频文件 {video_path}")
        sys.exit(1)
    
    # 创建输出目录
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = output_dir / f"complete_analysis_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*70)
    print("🎬 完整会议分析系统")
    print("="*70)
    print(f"\n📹 视频: {video_path}")
    print(f"📁 输出: {session_dir}\n")
    
    # 配置 Gemini
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    # ========== 步骤 1: 上传并基础分析 ==========
    print("="*70)
    print("📤 步骤 1/8: 上传视频并进行基础分析")
    print("="*70)
    
    video_file = genai.upload_file(path=video_path)
    print("✓ 视频已上传")
    
    import time
    while video_file.state.name == "PROCESSING":
        print("⏳ 等待视频处理...")
        time.sleep(2)
        video_file = genai.get_file(video_file.name)
    
    if video_file.state.name == "FAILED":
        raise ValueError("视频处理失败")
    
    print("✓ 视频处理完成")
    
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
    
    with open(session_dir / "basic_analysis.json", "w", encoding="utf-8") as f:
        json.dump(basic_analysis, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 基础分析完成 (分类: {basic_analysis.get('category', '未知')})")
    
    # 获取视频时长
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    video_duration = frame_count / fps if fps > 0 else 600
    cap.release()
    
    # ========== 步骤 2: 智能分段 ==========
    print("\n" + "="*70)
    print("🔍 步骤 2/8: 智能分段")
    print("="*70)
    
    segmenter = MeetingSegmenter(model)
    segments = segmenter.segment_meeting(transcript, video_duration)
    
    with open(session_dir / "segments.json", "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 分段完成，共 {len(segments)} 个议题")
    
    # ========== 步骤 3: 提取待办事项 ==========
    print("\n" + "="*70)
    print("✅ 步骤 3/8: 提取待办事项")
    print("="*70)
    
    extractor = ActionItemExtractor(model)
    action_items = extractor.extract_action_items(transcript, segments)
    
    with open(session_dir / "action_items.json", "w", encoding="utf-8") as f:
        json.dump(action_items, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 提取完成，共 {len(action_items)} 个待办事项")
    
    # ========== 步骤 4: 发言人识别 ==========
    print("\n" + "="*70)
    print("👥 步骤 4/8: 发言人识别")
    print("="*70)
    
    diarizer = SpeakerDiarizer(model)
    speakers = diarizer.identify_speakers(transcript, segments)
    
    with open(session_dir / "speakers.json", "w", encoding="utf-8") as f:
        json.dump(speakers, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 识别完成，共 {len(speakers)} 位发言人")
    
    # 生成发言人报告
    speaker_report = diarizer.generate_speaker_report(speakers)
    with open(session_dir / "speaker_report.md", "w", encoding="utf-8") as f:
        f.write(speaker_report)
    
    # ========== 步骤 5: 决策点检测 ==========
    print("\n" + "="*70)
    print("🎯 步骤 5/8: 决策点检测")
    print("="*70)
    
    detector = DecisionDetector(model)
    decisions = detector.detect_decisions(transcript, segments)
    
    with open(session_dir / "decisions.json", "w", encoding="utf-8") as f:
        json.dump(decisions, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 检测完成，共 {len(decisions)} 个决策点")
    
    # 生成决策点报告
    decision_report = detector.generate_decision_report(decisions)
    with open(session_dir / "decision_report.md", "w", encoding="utf-8") as f:
        f.write(decision_report)
    
    # ========== 步骤 6: 生成多格式报告 ==========
    print("\n" + "="*70)
    print("📊 步骤 6/8: 生成多格式报告")
    print("="*70)
    
    meeting_info = {
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "title": "会议分析",
        "duration": MeetingSegmenter.format_time(video_duration)
    }
    
    # Markdown 纪要
    md_exporter = MarkdownExporter()
    md_path = md_exporter.export_meeting_minutes(
        basic_analysis, segments, action_items, session_dir, meeting_info
    )
    print(f"✓ Markdown 纪要: {md_path.name}")
    
    # 时间轴报告
    timeline_gen = TimelineReportGenerator()
    timeline_path = timeline_gen.generate_timeline_report(
        basic_analysis, segments, action_items, session_dir
    )
    print(f"✓ 时间轴报告: {timeline_path.name}")
    
    # PDF 报告
    try:
        pdf_exporter = PDFExporter()
        pdf_path = pdf_exporter.export_meeting_report(
            basic_analysis, segments, action_items, session_dir,
            meeting_info, speakers, decisions
        )
        print(f"✓ PDF 报告: {pdf_path.name}")
    except Exception as e:
        print(f"⚠️  PDF 生成失败: {e}")
        print("   提示: 运行 'pip install reportlab' 安装 PDF 支持")
    
    # ========== 步骤 7: 保存到知识库 ==========
    if save_to_db:
        print("\n" + "="*70)
        print("💾 步骤 7/8: 保存到知识库")
        print("="*70)
        
        try:
            db = MeetingDatabase()
            meeting_id = db.save_meeting(
                title=meeting_info['title'],
                date=meeting_info['date'],
                analysis=basic_analysis,
                segments=segments,
                action_items=action_items,
                video_path=video_path,
                speakers=speakers,
                decisions=decisions,
                duration=video_duration
            )
            db.close()
            print(f"✓ 已保存到知识库 (ID: {meeting_id})")
        except Exception as e:
            print(f"⚠️  保存失败: {e}")
    
    # ========== 步骤 8: 生成统计报告 ==========
    print("\n" + "="*70)
    print("📈 步骤 8/8: 生成统计报告")
    print("="*70)
    
    stats = {
        "video_duration": video_duration,
        "segments_count": len(segments),
        "action_items_count": len(action_items),
        "speakers_count": len(speakers),
        "decisions_count": len(decisions),
        "transcript_length": len(transcript)
    }
    
    with open(session_dir / "statistics.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 统计报告已生成")
    
    # 清理
    genai.delete_file(video_file.name)
    
    # ========== 完成总结 ==========
    print("\n" + "="*70)
    print("✅ 分析完成！")
    print("="*70)
    print(f"\n📁 所有文件保存在: {session_dir}\n")
    print("📋 生成的文件:")
    print("  ├─ basic_analysis.json     (基础分析)")
    print("  ├─ segments.json           (智能分段)")
    print("  ├─ action_items.json       (待办事项)")
    print("  ├─ speakers.json           (发言人信息)")
    print("  ├─ decisions.json          (决策点)")
    print("  ├─ meeting_minutes.md      (会议纪要)")
    print("  ├─ speaker_report.md       (发言人报告)")
    print("  ├─ decision_report.md      (决策点报告)")
    print("  ├─ timeline_report.html    (时间轴报告)")
    print("  ├─ meeting_report.pdf      (PDF报告)")
    print("  └─ statistics.json         (统计信息)")
    
    print(f"\n💡 快速查看: open {timeline_path}")
    print(f"💡 查看纪要: open {md_path}")
    
    return session_dir


def main():
    if len(sys.argv) < 2:
        print("使用方法: python analyze_complete.py <视频文件> [--no-db]")
        print("\n选项:")
        print("  --no-db    不保存到知识库")
        sys.exit(1)
    
    video_path = sys.argv[1]
    save_to_db = "--no-db" not in sys.argv
    
    analyze_meeting_complete(video_path, save_to_db)


if __name__ == "__main__":
    main()
