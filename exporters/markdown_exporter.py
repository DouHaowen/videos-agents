"""
Markdown 导出器
生成结构化的会议纪要
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict


class MarkdownExporter:
    """Markdown 格式导出器"""
    
    def export_meeting_minutes(
        self,
        analysis: Dict,
        segments: List[Dict],
        action_items: List[Dict],
        output_path: Path,
        meeting_info: Dict = None
    ) -> Path:
        """
        导出会议纪要为 Markdown 格式
        
        Args:
            analysis: 基础分析结果
            segments: 分段信息
            action_items: 待办事项列表
            output_path: 输出路径
            meeting_info: 会议基本信息（可选）
        
        Returns:
            生成的文件路径
        """
        output_path = Path(output_path)
        
        # 构建 Markdown 内容
        md_content = self._build_markdown(analysis, segments, action_items, meeting_info)
        
        # 写入文件
        minutes_path = output_path / "meeting_minutes.md"
        with open(minutes_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        return minutes_path
    
    def _build_markdown(
        self,
        analysis: Dict,
        segments: List[Dict],
        action_items: List[Dict],
        meeting_info: Dict = None
    ) -> str:
        """构建 Markdown 内容"""
        
        # 会议信息
        info = meeting_info or {}
        date = info.get("date", datetime.now().strftime("%Y年%m月%d日"))
        title = info.get("title", "会议纪要")
        
        md = f"""# {title}

**日期**: {date}  
**分类**: {analysis.get('category', '未分类')}  
**时长**: {info.get('duration', '未知')}

---

## 📋 会议摘要

{analysis.get('summary', '无摘要')}

---

## 📌 议题与讨论

"""
        
        # 添加分段内容
        for seg in segments:
            from processors.segmenter import MeetingSegmenter
            start = MeetingSegmenter.format_time(seg['start_time'])
            end = MeetingSegmenter.format_time(seg['end_time'])
            
            md += f"""### {seg['segment_id']}. {seg['title']} `[{start} - {end}]`

**摘要**: {seg['summary']}

**关键点**:
"""
            for point in seg['key_points']:
                md += f"- {point}\n"
            
            md += "\n"
        
        # 添加待办事项
        if action_items:
            md += """---

## ✅ 待办事项

| 序号 | 任务 | 负责人 | 截止日期 | 优先级 |
|------|------|--------|----------|--------|
"""
            for i, item in enumerate(action_items, 1):
                task = item.get('task', '未知任务')
                owner = item.get('owner', '待分配')
                deadline = item.get('deadline', '待定')
                priority = item.get('priority', '中')
                md += f"| {i} | {task} | {owner} | {deadline} | {priority} |\n"
            
            md += "\n"
        
        # 添加关键决策
        if analysis.get('key_points'):
            md += """---

## 💡 关键讨论点

"""
            for i, point in enumerate(analysis['key_points'], 1):
                md += f"{i}. {point}\n"
            
            md += "\n"
        
        # 添加页脚
        md += f"""---

*本纪要由 AI 自动生成于 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        return md
