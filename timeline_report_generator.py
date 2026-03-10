"""
时间轴报告生成器
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from processors.segmenter import MeetingSegmenter


class TimelineReportGenerator:
    """时间轴报告生成器。"""

    def generate_timeline_report(
        self,
        analysis: Dict,
        segments: List[Dict],
        action_items: List[Dict],
        output_dir: Path,
        speakers: List[Dict] = None,
        decisions: List[Dict] = None,
    ) -> Path:
        output_dir = Path(output_dir)
        report_path = output_dir / "timeline_report.html"
        html = self._build_html(analysis, segments, action_items, speakers or [], decisions or [])
        with open(report_path, "w", encoding="utf-8") as file:
            file.write(html)
        return report_path

    def _build_html(
        self,
        analysis: Dict,
        segments: List[Dict],
        action_items: List[Dict],
        speakers: List[Dict],
        decisions: List[Dict],
    ) -> str:
        manager_summary = analysis.get("manager_summary", {})
        timeline_items = ""
        for seg in segments:
            timeline_items += f"""
            <section class="segment-card">
                <div class="segment-top">
                    <div>
                        <div class="eyebrow">议题 {seg['segment_id']}</div>
                        <h3>{seg['title']}</h3>
                    </div>
                    <div class="time-chip">{MeetingSegmenter.format_time(seg['start_time'])} - {MeetingSegmenter.format_time(seg['end_time'])}</div>
                </div>
                <p class="summary">{seg.get('summary', '无')}</p>
                <ul class="point-list">
                    {''.join([f'<li>{point}</li>' for point in seg.get('key_points', [])]) or '<li>无关键点</li>'}
                </ul>
                <details>
                    <summary>查看议题原文</summary>
                    <pre>{seg.get('transcript', '')}</pre>
                </details>
            </section>
            """

        actions_html = "".join(
            [
                f"""
                <div class="task-card">
                    <div class="task-main">{item.get('task', '未知任务')}</div>
                    <div class="task-meta">{item.get('owner', '待分配')} · {item.get('deadline', '待定')} · {item.get('priority', '中')}</div>
                    <div class="task-context">{item.get('context', '会议讨论')}</div>
                </div>
                """
                for item in action_items
            ]
        ) or "<p>未提取到明确待办事项。</p>"

        speaker_html = "".join(
            [
                f"<li>{speaker.get('speaker_name', '未知')} / {speaker.get('role', '未知')} / 参与度 {speaker.get('participation_rate', 0):.1f}%</li>"
                for speaker in speakers
            ]
        ) or "<li>暂无发言人数据</li>"

        decision_html = "".join(
            [
                f"<li><strong>{decision.get('title', '未命名')}</strong> ({decision.get('timestamp', '未知时间')}) - {decision.get('description', '无描述')}</li>"
                for decision in decisions
            ]
        ) or "<li>未识别到关键决策</li>"

        employee_updates_html = "".join(
            [
                f"<li><strong>{item.get('speaker_name', '未知')}</strong> ({item.get('role', '未知')})：{item.get('summary', '无')}</li>"
                for item in manager_summary.get("employee_updates", [])
            ]
        ) or "<li>未识别到员工汇报摘要</li>"

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{analysis.get('title', '会议分析报告')}</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: "Helvetica Neue", "PingFang SC", sans-serif;
            color: #0f172a;
            background:
                radial-gradient(circle at top left, rgba(20,184,166,0.18), transparent 28%),
                linear-gradient(160deg, #f8fafc 0%, #ecfeff 45%, #f0fdf4 100%);
        }}
        .wrap {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }}
        .hero {{
            background: rgba(255,255,255,0.86);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(148,163,184,0.2);
            border-radius: 28px;
            padding: 28px;
            box-shadow: 0 18px 50px rgba(15,23,42,0.08);
        }}
        h1 {{ margin: 0 0 8px; font-size: 40px; }}
        .meta-row {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 18px; }}
        .meta-pill {{
            background: #0f766e;
            color: white;
            border-radius: 999px;
            padding: 8px 14px;
            font-size: 14px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1.2fr 0.8fr;
            gap: 20px;
            margin-top: 24px;
        }}
        .panel {{
            background: rgba(255,255,255,0.9);
            border-radius: 24px;
            padding: 24px;
            box-shadow: 0 14px 36px rgba(15,23,42,0.07);
        }}
        .panel h2 {{ margin-top: 0; font-size: 22px; }}
        .segment-list {{ display: grid; gap: 16px; }}
        .segment-card {{
            background: #ffffff;
            border: 1px solid #ccfbf1;
            border-radius: 18px;
            padding: 18px;
        }}
        .segment-top {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: start;
        }}
        .eyebrow {{ color: #0f766e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; }}
        .time-chip {{
            background: #ccfbf1;
            color: #115e59;
            border-radius: 999px;
            padding: 8px 12px;
            white-space: nowrap;
            font-size: 13px;
        }}
        .summary {{ line-height: 1.7; color: #334155; }}
        .point-list, .side-list {{ padding-left: 18px; line-height: 1.8; }}
        .task-card {{
            background: #f8fafc;
            border-left: 4px solid #14b8a6;
            border-radius: 12px;
            padding: 14px;
            margin-bottom: 12px;
        }}
        .task-main {{ font-weight: 700; }}
        .task-meta, .task-context {{ color: #475569; font-size: 14px; margin-top: 6px; }}
        details {{ margin-top: 12px; }}
        pre {{ white-space: pre-wrap; overflow-wrap: anywhere; background: #f8fafc; border-radius: 12px; padding: 12px; }}
        @media (max-width: 900px) {{
            .grid {{ grid-template-columns: 1fr; }}
            h1 {{ font-size: 30px; }}
        }}
    </style>
</head>
<body>
    <div class="wrap">
        <section class="hero">
            <h1>{analysis.get('title', '会议分析报告')}</h1>
            <p>{analysis.get('summary', '无摘要')}</p>
            <div class="meta-row">
                <div class="meta-pill">分类: {analysis.get('category', '未分类')}</div>
                <div class="meta-pill">议题数: {len(segments)}</div>
                <div class="meta-pill">待办事项: {len(action_items)}</div>
                <div class="meta-pill">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
            </div>
        </section>

        <div class="grid">
            <section class="panel">
                <h2>时间轴议题</h2>
                <div class="segment-list">{timeline_items}</div>
            </section>

            <section class="panel">
                <h2>老板要求</h2>
                <ul class="side-list">
                    {''.join([f'<li>{item}</li>' for item in manager_summary.get('boss_messages', [])]) or '<li>未识别到明确老板要求</li>'}
                </ul>
                <h2>员工汇报</h2>
                <ul class="side-list">{employee_updates_html}</ul>
                <h2>风险与阻塞</h2>
                <ul class="side-list">
                    {''.join([f'<li>{item}</li>' for item in manager_summary.get('risks', [])]) or '<li>未识别到明显风险</li>'}
                </ul>
                <h2>下一步动作</h2>
                <ul class="side-list">
                    {''.join([f'<li>{item}</li>' for item in manager_summary.get('next_steps', [])]) or '<li>未识别到明确下一步</li>'}
                </ul>
            </section>
        </div>

        <div class="grid">
            <section class="panel">
                <h2>待办事项</h2>
                {actions_html}
            </section>
            <section class="panel">
                <h2>发言人概览</h2>
                <ul class="side-list">{speaker_html}</ul>
                <h2>关键决策</h2>
                <ul class="side-list">{decision_html}</ul>
            </section>
        </div>
    </div>
</body>
</html>"""
