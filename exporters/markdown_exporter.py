"""
Markdown 导出器
生成更贴近管理场景的会议纪要。
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List


class MarkdownExporter:
    """Markdown 格式导出器。"""

    def export_meeting_minutes(
        self,
        analysis: Dict,
        segments: List[Dict],
        action_items: List[Dict],
        output_path: Path,
        meeting_info: Dict = None,
        speakers: List[Dict] = None,
        decisions: List[Dict] = None,
    ) -> Path:
        output_path = Path(output_path)
        md_content = self._build_markdown(
            analysis,
            segments,
            action_items,
            meeting_info,
            speakers=speakers or [],
            decisions=decisions or [],
        )
        minutes_path = output_path / "meeting_minutes.md"
        with open(minutes_path, "w", encoding="utf-8") as file:
            file.write(md_content)
        return minutes_path

    def _build_markdown(
        self,
        analysis: Dict,
        segments: List[Dict],
        action_items: List[Dict],
        meeting_info: Dict = None,
        speakers: List[Dict] = None,
        decisions: List[Dict] = None,
    ) -> str:
        info = meeting_info or {}
        manager_summary = analysis.get("manager_summary", {})

        md = f"""# {info.get("title", analysis.get("title", "会议纪要"))}

**日期**: {info.get("date", datetime.now().strftime("%Y年%m月%d日"))}  
**分类**: {analysis.get('category', '未分类')}  
**时长**: {info.get('duration', '未知')}

---

## 会议摘要

{analysis.get('summary', '无摘要')}

---

## 老板要求

"""
        boss_messages = manager_summary.get("boss_messages", [])
        md += self._render_text_list(boss_messages, "未识别到明确老板要求")

        md += "\n---\n\n## 员工汇报\n\n"
        employee_updates = manager_summary.get("employee_updates", [])
        if employee_updates:
            for item in employee_updates:
                md += (
                    f"### {item.get('speaker_name', '未知')} "
                    f"({item.get('role', '未知')})\n\n"
                    f"{item.get('summary', '无内容')}\n\n"
                )
        else:
            md += "未识别到员工汇报摘要。\n\n"

        md += "---\n\n## 风险与阻塞\n\n"
        md += self._render_text_list(manager_summary.get("risks", []), "未识别到明显风险。")

        md += "\n---\n\n## 下一步动作\n\n"
        md += self._render_text_list(manager_summary.get("next_steps", []), "未识别到明确下一步。")

        md += "\n---\n\n## 议题与讨论\n\n"
        for seg in segments:
            from processors.segmenter import MeetingSegmenter

            start = MeetingSegmenter.format_time(seg["start_time"])
            end = MeetingSegmenter.format_time(seg["end_time"])
            md += f"### {seg['segment_id']}. {seg['title']} `[{start} - {end}]`\n\n"
            md += f"**摘要**: {seg.get('summary', '无')}\n\n"
            md += "**关键点**:\n"
            md += self._render_text_list(seg.get("key_points", []), "无")
            md += "\n"

        md += "---\n\n## 待办事项\n\n"
        if action_items:
            md += "| 序号 | 任务 | 负责人 | 截止日期 | 优先级 | 来源 |\n"
            md += "|------|------|--------|----------|--------|------|\n"
            for index, item in enumerate(action_items, 1):
                md += (
                    f"| {index} | {item.get('task', '未知任务')} | {item.get('owner', '待分配')} | "
                    f"{item.get('deadline', '待定')} | {item.get('priority', '中')} | "
                    f"{item.get('context', '会议讨论')} |\n"
                )
        else:
            md += "未提取到明确待办事项。\n"

        md += "\n---\n\n## 发言人概览\n\n"
        if speakers:
            for speaker in speakers:
                md += (
                    f"- {speaker.get('speaker_name', '未知')} / {speaker.get('role', '未知')} / "
                    f"参与度 {speaker.get('participation_rate', 0):.1f}%\n"
                )
        else:
            md += "暂无发言人数据。\n"

        md += "\n---\n\n## 关键决策\n\n"
        if decisions:
            for decision in decisions:
                md += (
                    f"- **{decision.get('title', '未命名')}** "
                    f"({decision.get('timestamp', '未知时间')})："
                    f"{decision.get('description', '无描述')}\n"
                )
        else:
            md += "未识别到关键决策。\n"

        md += f"\n---\n\n*本纪要由 AI 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        return md

    def _render_text_list(self, items: List[str], empty_text: str) -> str:
        if not items:
            return f"{empty_text}\n"
        return "".join([f"- {item}\n" for item in items])
