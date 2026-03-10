#!/usr/bin/env python3
"""
会议分析工具
"""

import os
import sys

from meeting_pipeline import MeetingAnalysisPipeline


def main():
    if len(sys.argv) < 2:
        print("使用方法: python analyze_with_gemini.py <视频文件路径>")
        sys.exit(1)

    video_path = sys.argv[1]
    if not os.path.exists(video_path):
        print(f"错误: 找不到视频文件 {video_path}")
        sys.exit(1)

    result = MeetingAnalysisPipeline().analyze(
        video_path=video_path,
        output_root="output",
        mode="complete",
        save_to_db=False,
    )

    print(f"✅ 分析完成: {result['session_dir']}")
    print(f"主题: {result.get('title', '会议分析')}")
    print(f"摘要: {result.get('summary', '无摘要')}")
    print(f"分类: {result.get('category', '未知')}")
    print(f"老板要求数: {len(result.get('boss_messages', []))}")


if __name__ == "__main__":
    main()
