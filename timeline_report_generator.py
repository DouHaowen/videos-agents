"""
时间轴报告生成器
生成带有交互式时间轴的 HTML 报告
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict
from processors.segmenter import MeetingSegmenter


class TimelineReportGenerator:
    """时间轴报告生成器"""
    
    def generate_timeline_report(
        self,
        analysis: Dict,
        segments: List[Dict],
        action_items: List[Dict],
        output_dir: Path
    ) -> Path:
        """
        生成带时间轴的交互式报告
        
        Args:
            analysis: 基础分析结果
            segments: 分段信息
            action_items: 待办事项
            output_dir: 输出目录
        
        Returns:
            报告文件路径
        """
        output_dir = Path(output_dir)
        report_path = output_dir / "timeline_report.html"
        
        # 生成 HTML
        html = self._build_html(analysis, segments, action_items)
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        return report_path
    
    def _build_html(self, analysis: Dict, segments: List[Dict], action_items: List[Dict]) -> str:
        """构建 HTML 内容"""
        
        # 构建时间轴项
        timeline_items = ""
        for seg in segments:
            start = MeetingSegmenter.format_time(seg['start_time'])
            end = MeetingSegmenter.format_time(seg['end_time'])
            duration = MeetingSegmenter.format_time(seg['duration'])
            
            key_points_html = "".join([f"<li>{point}</li>" for point in seg['key_points']])
            
            timeline_items += f"""
            <div class="timeline-item" data-segment="{seg['segment_id']}">
                <div class="timeline-marker">{seg['segment_id']}</div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <h3>{seg['title']}</h3>
                        <span class="time-badge">{start} - {end}</span>
                    </div>
                    <p class="summary">{seg['summary']}</p>
                    <div class="key-points">
                        <strong>关键点：</strong>
                        <ul>{key_points_html}</ul>
                    </div>
                    <button class="expand-btn" onclick="toggleTranscript({seg['segment_id']})">
                        查看完整转录 ▼
                    </button>
                    <div class="transcript" id="transcript-{seg['segment_id']}" style="display: none;">
                        <pre>{seg['transcript']}</pre>
                    </div>
                </div>
            </div>
            """
        
        # 构建待办事项
        action_items_html = ""
        if action_items:
            for i, item in enumerate(action_items, 1):
                priority_class = f"priority-{item.get('priority', '中').lower()}"
                action_items_html += f"""
                <div class="action-item {priority_class}">
                    <div class="action-header">
                        <span class="action-number">{i}</span>
                        <span class="action-task">{item.get('task', '未知任务')}</span>
                    </div>
                    <div class="action-meta">
                        <span class="action-owner">👤 {item.get('owner', '待分配')}</span>
                        <span class="action-deadline">📅 {item.get('deadline', '待定')}</span>
                        <span class="action-priority">⚡ {item.get('priority', '中')}</span>
                    </div>
                </div>
                """
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>会议分析 - 时间轴视图</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header h1 {{
            color: #667eea;
            font-size: 36px;
            margin-bottom: 15px;
        }}
        .header .meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 20px;
        }}
        .meta-item {{
            background: #f8f9ff;
            padding: 10px 20px;
            border-radius: 10px;
            font-size: 14px;
            color: #555;
        }}
        .summary-box {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .summary-box h2 {{
            color: #667eea;
            margin-bottom: 15px;
            font-size: 24px;
        }}
        .summary-box p {{
            line-height: 1.8;
            color: #555;
        }}
        .timeline {{
            position: relative;
            padding-left: 50px;
        }}
        .timeline::before {{
            content: '';
            position: absolute;
            left: 20px;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }}
        .timeline-item {{
            position: relative;
            background: white;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        .timeline-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        }}
        .timeline-marker {{
            position: absolute;
            left: -38px;
            top: 25px;
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 16px;
            box-shadow: 0 4px 10px rgba(102, 126, 234, 0.4);
        }}
        .timeline-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .timeline-header h3 {{
            color: #333;
            font-size: 20px;
        }}
        .time-badge {{
            background: #667eea;
            color: white;
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 500;
        }}
        .summary {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
        }}
        .key-points {{
            background: #f8f9ff;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
        }}
        .key-points strong {{
            color: #667eea;
            display: block;
            margin-bottom: 8px;
        }}
        .key-points ul {{
            list-style: none;
            padding-left: 0;
        }}
        .key-points li {{
            padding: 5px 0;
            padding-left: 20px;
            position: relative;
            color: #555;
        }}
        .key-points li::before {{
            content: "▸";
            position: absolute;
            left: 0;
            color: #667eea;
        }}
        .expand-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }}
        .expand-btn:hover {{
            background: #5568d3;
        }}
        .transcript {{
            margin-top: 15px;
            background: #f5f5f5;
            padding: 15px;
            border-radius: 8px;
            max-height: 300px;
            overflow-y: auto;
        }}
        .transcript pre {{
            white-space: pre-wrap;
            word-wrap: break-word;
            color: #555;
            font-size: 14px;
            line-height: 1.6;
        }}
        .actions-section {{
            background: white;
            border-radius: 20px;
            padding: 30px;
            margin-top: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .actions-section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 24px;
        }}
        .action-item {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }}
        .action-item.priority-高 {{
            border-left-color: #fc8181;
            background: #fff5f5;
        }}
        .action-item.priority-低 {{
            border-left-color: #68d391;
            background: #f0fff4;
        }}
        .action-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }}
        .action-number {{
            background: #667eea;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
        }}
        .action-task {{
            flex: 1;
            font-weight: 500;
            color: #333;
        }}
        .action-meta {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 14px;
            color: #666;
        }}
        .action-meta span {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 会议分析报告</h1>
            <div class="meta">
                <div class="meta-item">🏷️ 分类: {analysis.get('category', '未分类')}</div>
                <div class="meta-item">📅 生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
                <div class="meta-item">📝 议题数: {len(segments)}</div>
                <div class="meta-item">✅ 待办事项: {len(action_items)}</div>
            </div>
        </div>
        
        <div class="summary-box">
            <h2>📝 会议摘要</h2>
            <p>{analysis.get('summary', '无摘要')}</p>
        </div>
        
        <div class="timeline">
            {timeline_items}
        </div>
        
        {f'<div class="actions-section"><h2>✅ 待办事项</h2>{action_items_html}</div>' if action_items else ''}
    </div>
    
    <script>
        function toggleTranscript(segmentId) {{
            const transcript = document.getElementById('transcript-' + segmentId);
            const btn = event.target;
            if (transcript.style.display === 'none') {{
                transcript.style.display = 'block';
                btn.textContent = '隐藏转录 ▲';
            }} else {{
                transcript.style.display = 'none';
                btn.textContent = '查看完整转录 ▼';
            }}
        }}
    </script>
</body>
</html>"""
        
        return html
