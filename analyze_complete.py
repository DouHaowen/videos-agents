#!/usr/bin/env python3
"""
完整版会议分析工具
"""

import os
import sys

from meeting_pipeline import MeetingAnalysisPipeline


def analyze_meeting_complete(video_path, save_to_db=True):
    if not os.path.exists(video_path):
        print(f"错误: 找不到视频文件 {video_path}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("🎬 完整会议分析系统")
    print("=" * 70)
    print(f"\n📹 视频: {video_path}\n")

    result = MeetingAnalysisPipeline().analyze(
        video_path=video_path,
        output_root="output",
        mode="complete",
        save_to_db=save_to_db,
    )

    print(f"✓ 标题: {result.get('title', '会议分析')}")
    print(f"✓ 分类: {result.get('category', '未知')}")
    print(f"✓ 议题数: {result.get('segments_count', 0)}")
    print(f"✓ 待办事项: {result.get('action_items_count', 0)}")
    print(f"✓ 发言人: {result.get('speakers_count', 0)}")
    print(f"✓ 决策点: {result.get('decisions_count', 0)}")
    print(f"\n📁 输出目录: {result['session_dir']}")
    return result["session_dir"]


def main():
    if len(sys.argv) < 2:
        print("使用方法: python analyze_complete.py <视频文件> [--no-db]")
        sys.exit(1)

    analyze_meeting_complete(sys.argv[1], save_to_db="--no-db" not in sys.argv)


if __name__ == "__main__":
    main()
