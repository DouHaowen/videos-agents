"""
PDF 导出器
生成完整会议报告。
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PDFExporter:
    """PDF 格式导出器。"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        self._setup_styles()

    def _setup_styles(self):
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#0f766e"),
                spaceAfter=24,
                alignment=TA_CENTER,
                fontName="STSong-Light",
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="SectionTitle",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#115e59"),
                spaceAfter=10,
                spaceBefore=10,
                fontName="STSong-Light",
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CustomBody",
                parent=self.styles["BodyText"],
                fontSize=10.5,
                leading=15,
                fontName="STSong-Light",
            )
        )

    def export_meeting_report(
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
        pdf_path = output_path / "meeting_report.pdf"
        doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=30)

        story = []
        story.extend(self._build_title_page(analysis, meeting_info))
        story.append(PageBreak())
        story.extend(self._build_manager_section(analysis))
        story.extend(self._build_segments_section(segments))
        story.extend(self._build_action_items_section(action_items))
        story.extend(self._build_speakers_section(speakers or []))
        story.extend(self._build_decisions_section(decisions or []))

        doc.build(story)
        return pdf_path

    def _build_title_page(self, analysis: Dict, meeting_info: Dict = None):
        info = meeting_info or {}
        story = [
            Paragraph(info.get("title", analysis.get("title", "会议分析报告")), self.styles["CustomTitle"]),
            Spacer(1, 0.3 * inch),
        ]
        table = Table(
            [
                ["日期", info.get("date", datetime.now().strftime("%Y年%m月%d日"))],
                ["分类", analysis.get("category", "未分类")],
                ["时长", info.get("duration", "未知")],
                ["生成时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ],
            colWidths=[1.5 * inch, 4.5 * inch],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#ecfeff")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#99f6e4")),
                    ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ]
            )
        )
        story.append(table)
        return story

    def _build_manager_section(self, analysis: Dict):
        story = [
            Paragraph("管理视角摘要", self.styles["SectionTitle"]),
            Paragraph(analysis.get("summary", "无摘要"), self.styles["CustomBody"]),
            Spacer(1, 0.15 * inch),
        ]
        manager_summary = analysis.get("manager_summary", {})

        story.append(Paragraph("老板要求", self.styles["SectionTitle"]))
        story.extend(self._paragraph_list(manager_summary.get("boss_messages", []), "未识别到老板要求"))
        story.append(Paragraph("员工汇报", self.styles["SectionTitle"]))
        updates = manager_summary.get("employee_updates", [])
        if updates:
            for item in updates:
                text = f"{item.get('speaker_name', '未知')} ({item.get('role', '未知')}): {item.get('summary', '无')}"
                story.append(Paragraph(text, self.styles["CustomBody"]))
        else:
            story.append(Paragraph("未识别到员工汇报。", self.styles["CustomBody"]))

        story.append(Paragraph("风险与阻塞", self.styles["SectionTitle"]))
        story.extend(self._paragraph_list(manager_summary.get("risks", []), "未识别到明显风险。"))
        return story

    def _build_segments_section(self, segments: List[Dict]):
        from processors.segmenter import MeetingSegmenter

        story = [Paragraph("议题与讨论", self.styles["SectionTitle"])]
        for seg in segments:
            title = f"{seg.get('segment_id')}. {seg.get('title')} [{MeetingSegmenter.format_time(seg.get('start_time', 0))} - {MeetingSegmenter.format_time(seg.get('end_time', 0))}]"
            story.append(Paragraph(title, self.styles["CustomBody"]))
            story.append(Paragraph(seg.get("summary", "无"), self.styles["CustomBody"]))
            story.append(Spacer(1, 0.1 * inch))
        return story

    def _build_action_items_section(self, action_items: List[Dict]):
        story = [Paragraph("待办事项", self.styles["SectionTitle"])]
        if not action_items:
            story.append(Paragraph("未提取到明确待办事项。", self.styles["CustomBody"]))
            return story

        table_data = [["序号", "任务", "负责人", "截止日期", "优先级"]]
        for index, item in enumerate(action_items, 1):
            table_data.append(
                [
                    str(index),
                    item.get("task", "未知任务"),
                    item.get("owner", "待分配"),
                    item.get("deadline", "待定"),
                    item.get("priority", "中"),
                ]
            )
        table = Table(table_data, colWidths=[0.4 * inch, 3.0 * inch, 1.0 * inch, 1.0 * inch, 0.6 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14b8a6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ]
            )
        )
        story.append(table)
        return story

    def _build_speakers_section(self, speakers: List[Dict]):
        story = [Paragraph("发言人分析", self.styles["SectionTitle"])]
        if not speakers:
            story.append(Paragraph("暂无发言人数据。", self.styles["CustomBody"]))
            return story
        for speaker in speakers:
            text = (
                f"{speaker.get('speaker_name', '未知')} / {speaker.get('role', '未知')} / "
                f"参与度 {speaker.get('participation_rate', 0):.1f}%"
            )
            story.append(Paragraph(text, self.styles["CustomBody"]))
        return story

    def _build_decisions_section(self, decisions: List[Dict]):
        story = [Paragraph("关键决策", self.styles["SectionTitle"])]
        if not decisions:
            story.append(Paragraph("未识别到关键决策。", self.styles["CustomBody"]))
            return story
        for decision in decisions:
            text = (
                f"{decision.get('title', '未命名')} ({decision.get('timestamp', '未知时间')}): "
                f"{decision.get('description', '无描述')}"
            )
            story.append(Paragraph(text, self.styles["CustomBody"]))
        return story

    def _paragraph_list(self, items: List[str], empty_text: str):
        if not items:
            return [Paragraph(empty_text, self.styles["CustomBody"])]
        return [Paragraph(f"• {item}", self.styles["CustomBody"]) for item in items]
