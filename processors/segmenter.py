"""
会议智能分段模块
自动识别会议中的不同议题，生成带时间戳的结构化内容
"""

import json
from typing import List, Dict
from datetime import timedelta


class MeetingSegmenter:
    """会议智能分段器"""
    
    def __init__(self, client):
        """
        初始化分段器
        
        Args:
            client: AI 客户端（支持 OpenAI/Gemini 等）
        """
        self.client = client
    
    def segment_meeting(self, transcript: str, video_duration: float) -> List[Dict]:
        """
        将会议转录文本分段
        
        Args:
            transcript: 完整的会议转录文本
            video_duration: 视频总时长（秒）
        
        Returns:
            分段列表，每个分段包含：
            {
                "segment_id": int,
                "title": str,
                "start_time": float,
                "end_time": float,
                "duration": float,
                "summary": str,
                "key_points": List[str],
                "transcript": str
            }
        """
        # 使用 LLM 进行智能分段
        prompt = f"""请分析以下会议转录内容，将其分成不同的议题段落。

会议转录：
{transcript}

请按照以下要求进行分段：
1. 识别明显的议题切换点（话题转变、新议题开始等）
2. 每个段落应该是一个相对独立的讨论主题
3. 为每个段落生成简洁的标题（5-10字）
4. 为每个段落写一句话摘要
5. 提取每个段落的2-3个关键点

请以 JSON 格式返回，格式如下：
{{
  "segments": [
    {{
      "title": "段落标题",
      "summary": "段落摘要",
      "key_points": ["关键点1", "关键点2"],
      "content": "该段落的原文内容"
    }}
  ]
}}

注意：
- 建议分成 3-8 个段落
- 标题要简洁明了
- 摘要要抓住核心内容
"""
        
        # 调用 LLM
        if hasattr(self.client, 'chat'):  # OpenAI 风格
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 使用更便宜的模型
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
        else:  # Gemini 风格
            import google.generativeai as genai
            response = self.client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
        
        # 处理分段结果，添加时间信息
        segments = result.get("segments", [])
        processed_segments = []
        
        # 估算每个段落的时间（基于文本长度比例）
        total_chars = sum(len(seg.get("content", "")) for seg in segments)
        current_time = 0.0
        
        for i, seg in enumerate(segments):
            content = seg.get("content", "")
            # 根据文本长度估算时长
            segment_duration = (len(content) / total_chars) * video_duration if total_chars > 0 else 0
            
            processed_segments.append({
                "segment_id": i + 1,
                "title": seg.get("title", f"议题 {i+1}"),
                "start_time": current_time,
                "end_time": current_time + segment_duration,
                "duration": segment_duration,
                "summary": seg.get("summary", ""),
                "key_points": seg.get("key_points", []),
                "transcript": content
            })
            
            current_time += segment_duration
        
        return processed_segments
    
    @staticmethod
    def format_time(seconds: float) -> str:
        """
        将秒数格式化为 HH:MM:SS
        
        Args:
            seconds: 秒数
        
        Returns:
            格式化的时间字符串
        """
        td = timedelta(seconds=int(seconds))
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
