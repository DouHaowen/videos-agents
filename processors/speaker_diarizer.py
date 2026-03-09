"""
说话人识别模块
使用 Gemini 的多模态能力识别不同的发言人
"""

import json
from typing import List, Dict


class SpeakerDiarizer:
    """说话人识别器"""
    
    def __init__(self, client):
        """
        初始化识别器
        
        Args:
            client: AI 客户端（Gemini）
        """
        self.client = client
    
    def identify_speakers(
        self,
        transcript: str,
        segments: List[Dict] = None
    ) -> List[Dict]:
        """
        识别转录文本中的不同发言人
        
        Args:
            transcript: 会议转录文本
            segments: 分段信息（可选）
        
        Returns:
            发言人信息列表，每项包含：
            {
                "speaker_id": str,        # 发言人ID（如 "发言人A"）
                "speaker_name": str,      # 发言人名称（如果能识别）
                "segments": [             # 该发言人的发言片段
                    {
                        "text": str,      # 发言内容
                        "start_time": float,  # 开始时间（如果有）
                        "end_time": float     # 结束时间（如果有）
                    }
                ],
                "total_duration": float,  # 总发言时长
                "word_count": int,        # 发言字数
                "participation_rate": float  # 参与度百分比
            }
        """
        prompt = f"""请分析以下会议转录内容，识别不同的发言人。

会议转录：
{transcript[:4000]}

请完成以下任务：
1. 识别对话中有几个不同的发言人
2. 为每个发言人分配一个标识（如"发言人A"、"发言人B"等）
3. 如果能从对话中推断出发言人的名字或角色，请标注
4. 将转录内容按发言人分段
5. 估算每个发言人的发言比例

请以 JSON 格式返回：
{{
  "speakers": [
    {{
      "speaker_id": "发言人A",
      "speaker_name": "张三（如果能识别）或 未知",
      "role": "主持人/参与者/未知",
      "segments": [
        {{
          "text": "发言内容",
          "context": "在哪个议题中发言"
        }}
      ],
      "word_count": 发言字数,
      "participation_rate": 参与度百分比
    }}
  ],
  "total_speakers": 总发言人数
}}

注意：
- 根据语气、称呼、话题连贯性等判断发言人
- 如果无法明确区分，可以标注为"无法区分"
- 参与度 = 该发言人字数 / 总字数 * 100
"""
        
        # 调用 LLM
        import google.generativeai as genai
        response = self.client.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        speakers = result.get("speakers", [])
        
        # 计算总时长（如果有分段信息）
        if segments:
            total_duration = sum(seg.get('duration', 0) for seg in segments)
            for speaker in speakers:
                # 估算发言时长 = 总时长 * 参与度
                speaker['total_duration'] = total_duration * (speaker.get('participation_rate', 0) / 100)
        
        return speakers
    
    def generate_speaker_report(self, speakers: List[Dict]) -> str:
        """
        生成发言人分析报告
        
        Args:
            speakers: 发言人信息列表
        
        Returns:
            Markdown 格式的报告
        """
        report = "# 发言人分析报告\n\n"
        report += f"## 总览\n\n"
        report += f"- 识别到 {len(speakers)} 位发言人\n\n"
        
        report += "## 发言人详情\n\n"
        
        for i, speaker in enumerate(speakers, 1):
            speaker_id = speaker.get('speaker_id', f'发言人{i}')
            speaker_name = speaker.get('speaker_name', '未知')
            role = speaker.get('role', '未知')
            word_count = speaker.get('word_count', 0)
            participation = speaker.get('participation_rate', 0)
            
            report += f"### {i}. {speaker_id}\n\n"
            report += f"- **姓名**: {speaker_name}\n"
            report += f"- **角色**: {role}\n"
            report += f"- **发言字数**: {word_count}\n"
            report += f"- **参与度**: {participation:.1f}%\n"
            
            if 'total_duration' in speaker:
                from processors.segmenter import MeetingSegmenter
                duration_str = MeetingSegmenter.format_time(speaker['total_duration'])
                report += f"- **发言时长**: {duration_str}\n"
            
            report += "\n**主要发言**:\n\n"
            segments = speaker.get('segments', [])[:3]  # 只显示前3段
            for seg in segments:
                text = seg.get('text', '')[:100]  # 限制长度
                report += f"- {text}...\n"
            
            report += "\n"
        
        return report
