"""
决策点检测模块
支持长会议分块，并将决策关联到真实时间段。
"""

from typing import Dict, List

import google.generativeai as genai

from .llm_utils import chunk_text, merge_unique_dicts, parse_json_response


class DecisionDetector:
    """决策点检测器。"""

    def __init__(self, client):
        self.client = client

    def detect_decisions(
        self,
        transcript: str,
        segments: List[Dict] = None,
        utterances: List[Dict] = None,
    ) -> List[Dict]:
        segments = segments or []
        utterances = utterances or []
        source_text = self._build_source_text(transcript, utterances)

        aggregated: List[Dict] = []
        for chunk in chunk_text(source_text, max_chars=7000, overlap=800):
            prompt = f"""请分析以下会议记录，识别明确的决策点。

会议记录：
{chunk}

请返回 JSON：
{{
  "decisions": [
    {{
      "title": "决策标题",
      "description": "决策描述",
      "rationale": "决策原因",
      "alternatives": ["备选方案1"],
      "impact": "高/中/低",
      "stakeholders": ["相关人员1"],
      "timestamp": "00:12:30"
    }}
  ]
}}

要求：
- 只保留明确拍板或达成共识的内容。
- timestamp 尽量用会议原始时间。"""

            response = self.client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
            data = parse_json_response(response.text)
            aggregated.extend(data.get("decisions", []))

        decisions = merge_unique_dicts(aggregated, ["title", "description"])
        for index, decision in enumerate(decisions, 1):
            decision["decision_id"] = index
            decision["segment_id"] = self._find_related_segment(decision, segments)
            decision["timestamp"] = decision.get("timestamp") or self._segment_timestamp(decision["segment_id"], segments)

        return decisions

    def generate_decision_report(self, decisions: List[Dict]) -> str:
        if not decisions:
            return "# 决策点分析\n\n本次会议未识别到明确的决策点。\n"

        report = "# 决策点分析\n\n"
        report += f"## 总览\n\n- 识别到 {len(decisions)} 个关键决策\n\n"
        report += "## 决策详情\n\n"

        for decision in decisions:
            report += f"### {decision.get('decision_id')}. {decision.get('title', '未命名')}\n\n"
            report += f"- 时间: {decision.get('timestamp', '未知')}\n"
            report += f"- 影响等级: {decision.get('impact', '未知')}\n"
            report += f"- 描述: {decision.get('description', '无')}\n"
            report += f"- 原因: {decision.get('rationale', '无')}\n"
            if decision.get("alternatives"):
                report += f"- 备选方案: {', '.join(decision['alternatives'])}\n"
            if decision.get("stakeholders"):
                report += f"- 相关人员: {', '.join(decision['stakeholders'])}\n"
            report += "\n"

        return report

    def _build_source_text(self, transcript: str, utterances: List[Dict]) -> str:
        if utterances:
            return "\n".join(
                [
                    f"[{item.get('start_time')}-{item.get('end_time')}] "
                    f"{item.get('speaker_name', '未知')}/{item.get('role', '未知')}: {item.get('text', '')}"
                    for item in utterances
                ]
            )
        return transcript

    def _find_related_segment(self, decision: Dict, segments: List[Dict]) -> int:
        from processors.segmenter import MeetingSegmenter

        timestamp = decision.get("timestamp")
        if timestamp:
            target = MeetingSegmenter.parse_time_to_seconds(timestamp)
            for segment in segments:
                if segment.get("start_time", 0) <= target <= segment.get("end_time", 0):
                    return segment.get("segment_id", 1)

        description = decision.get("description", "").lower()
        for segment in segments:
            if description and description[:12] in segment.get("transcript", "").lower():
                return segment.get("segment_id", 1)
        return 1

    def _segment_timestamp(self, segment_id: int, segments: List[Dict]) -> str:
        from processors.segmenter import MeetingSegmenter

        for segment in segments:
            if segment.get("segment_id") == segment_id:
                return MeetingSegmenter.format_time(segment.get("start_time", 0))
        return "00:00:00"
