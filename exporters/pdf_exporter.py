"""
PDF 导出器
生成专业的 PDF 格式会议报告
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


class PDFExporter:
    """PDF 格式导出器"""
    
    def __init__(self):
        """初始化 PDF 导出器"""
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """设置自定义样式"""
        # 标题样式
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # 章节标题
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # 子标题
        self.styles.add(ParagraphStyle(
            name='SubTitle',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=10
        ))
        
        # 正文
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            leading=16,
            textColor=colors.HexColor('#555555')
        ))
    
    def export_meeting_report(
        self,
        analysis: Dict,
        segments: List[Dict],
        action_items: List[Dict],
        output_path: Path,
        meeting_info: Dict = None,
        speakers: List[Dict] = None,
        decisions: List[Dict] = None
    ) -> Path:
        """
        导出完整的会议报告为 PDF
        
        Args:
            analysis: 基础分析结果
            segments: 分段信息
            action_items: 待办事项
            output_path: 输出路径
            meeting_info: 会议基本信息
            speakers: 发言人信息
            decisions: 决策点信息
        
        Returns:
            生成的 PDF 文件路径
        """
        output_path = Path(output_path)
        pdf_path = output_path / "meeting_report.pdf"
        
        # 创建 PDF 文档
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # 构建内容
        story = []
        
        # 标题页
        story.extend(self._build_title_page(analysis, meeting_info))
        story.append(PageBreak())
        
        # 会议摘要
        story.extend(self._build_summary_section(analysis))
        
        # 议题与讨论
        story.extend(self._build_segments_section(segments))
        
        # 待办事项
        if action_items:
            story.extend(self._build_action_items_section(action_items))
        
        # 发言人分析
        if speakers:
            story.extend(self._build_speakers_section(speakers))
        
        # 决策点
        if decisions:
            story.extend(self._build_decisions_section(decisions))
        
        # 生成 PDF
        doc.build(story)
        
        return pdf_path
    
    def _build_title_page(self, analysis: Dict, meeting_info: Dict = None) -> List:
        """构建标题页"""
        info = meeting_info or {}
        story = []
        
        # 标题
        title = Paragraph(
            info.get('title', '会议分析报告'),
            self.styles['CustomTitle']
        )
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # 元信息表格
        meta_data = [
            ['日期', info.get('date', datetime.now().strftime("%Y年%m月%d日"))],
            ['分类', analysis.get('category', '未分类')],
            ['时长', info.get('duration', '未知')],
            ['生成时间', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9ff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0'))
        ]))
        
        story.append(meta_table)
        
        return story
    
    def _build_summary_section(self, analysis: Dict) -> List:
        """构建摘要部分"""
        story = []
        
        # 章节标题
        story.append(Paragraph('会议摘要', self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # 摘要内容
        summary = Paragraph(
            analysis.get('summary', '无摘要'),
            self.styles['CustomBody']
        )
        story.append(summary)
        story.append(Spacer(1, 0.3*inch))
        
        # 关键讨论点
        if analysis.get('key_points'):
            story.append(Paragraph('关键讨论点', self.styles['SubTitle']))
            for i, point in enumerate(analysis['key_points'], 1):
                p = Paragraph(f"{i}. {point}", self.styles['CustomBody'])
                story.append(p)
                story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_segments_section(self, segments: List[Dict]) -> List:
        """构建议题部分"""
        story = []
        
        story.append(Paragraph('议题与讨论', self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        for seg in segments:
            from processors.segmenter import MeetingSegmenter
            start = MeetingSegmenter.format_time(seg['start_time'])
            end = MeetingSegmenter.format_time(seg['end_time'])
            
            # 议题标题
            title_text = f"{seg['segment_id']}. {seg['title']} [{start} - {end}]"
            story.append(Paragraph(title_text, self.styles['SubTitle']))
            
            # 摘要
            summary = Paragraph(f"<b>摘要:</b> {seg['summary']}", self.styles['CustomBody'])
            story.append(summary)
            story.append(Spacer(1, 0.1*inch))
            
            # 关键点
            if seg.get('key_points'):
                story.append(Paragraph('<b>关键点:</b>', self.styles['CustomBody']))
                for point in seg['key_points']:
                    p = Paragraph(f"• {point}", self.styles['CustomBody'])
                    story.append(p)
            
            story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _build_action_items_section(self, action_items: List[Dict]) -> List:
        """构建待办事项部分"""
        story = []
        
        story.append(Paragraph('待办事项', self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # 创建表格
        table_data = [['序号', '任务', '负责人', '截止日期', '优先级']]
        
        for i, item in enumerate(action_items, 1):
            table_data.append([
                str(i),
                item.get('task', '未知任务'),
                item.get('owner', '待分配'),
                item.get('deadline', '待定'),
                item.get('priority', '中')
            ])
        
        table = Table(table_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch, 0.8*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        return story
    
    def _build_speakers_section(self, speakers: List[Dict]) -> List:
        """构建发言人分析部分"""
        story = []
        
        story.append(Paragraph('发言人分析', self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        for speaker in speakers:
            speaker_id = speaker.get('speaker_id', '未知')
            speaker_name = speaker.get('speaker_name', '未知')
            participation = speaker.get('participation_rate', 0)
            
            text = f"<b>{speaker_id}</b> ({speaker_name}) - 参与度: {participation:.1f}%"
            story.append(Paragraph(text, self.styles['CustomBody']))
            story.append(Spacer(1, 0.1*inch))
        
        story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _build_decisions_section(self, decisions: List[Dict]) -> List:
        """构建决策点部分"""
        story = []
        
        story.append(Paragraph('关键决策', self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        for decision in decisions:
            title = f"{decision['decision_id']}. {decision.get('title', '未命名')}"
            story.append(Paragraph(title, self.styles['SubTitle']))
            
            desc = Paragraph(f"<b>描述:</b> {decision.get('description', '无')}", self.styles['CustomBody'])
            story.append(desc)
            story.append(Spacer(1, 0.1*inch))
            
            rationale = Paragraph(f"<b>理由:</b> {decision.get('rationale', '无')}", self.styles['CustomBody'])
            story.append(rationale)
            story.append(Spacer(1, 0.1*inch))
            
            impact = Paragraph(f"<b>影响程度:</b> {decision.get('impact', '未知')}", self.styles['CustomBody'])
            story.append(impact)
            story.append(Spacer(1, 0.2*inch))
        
        return story
