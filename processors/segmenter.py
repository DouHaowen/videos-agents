"""
会议智能分段模块
基于结构化转录生成真实时间轴议题。
"""

import json
import re
from datetime import timedelta
from typing import Dict, List

from llm_client import GenerationConfig
from .llm_utils import parse_json_response


class MeetingSegmenter:
    """会议智能分段器。"""

    def __init__(self, client):
        self.client = client

    def segment_meeting(
        self,
        transcript: str,
        video_duration: float,
        utterances: List[Dict] = None,
    ) -> List[Dict]:
        utterances = utterances or []
        source_text = self._build_source_text(transcript, utterances)

        prompt = f"""请根据以下会议发言记录，将会议划分为 3-10 个议题段落。

会议内容：
{source_text}

请返回 JSON：
{{
  "segments": [
    {{
      "title": "议题标题",
      "summary": "一句话摘要",
      "key_points": ["关键点1", "关键点2"],
      "speaker_ids": ["发言人A", "发言人B"],
      "start_time": "00:00:10",
      "end_time": "00:04:20",
      "segment_focus": "该议题主要在讨论什么"
    }}
  ]
}}

要求：
- 尽量利用原始时间戳。
- 议题边界要对应真实发言切换。
- speaker_ids 填写该议题中主要发言人。"""

        response = self.client.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        result = parse_json_response(response.text)

        segments = result.get("segments", [])
        processed_segments = []

        for index, seg in enumerate(segments, 1):
            start_seconds = self.parse_time_to_seconds(seg.get("start_time", "00:00:00"))
            end_seconds = self.parse_time_to_seconds(seg.get("end_time", self.format_time(video_duration)))

            related_utterances = self._collect_utterances(
                utterances,
                start_seconds,
                end_seconds,
                seg.get("speaker_ids", []),
            )

            if not related_utterances and utterances:
                related_utterances = self._nearest_utterances(utterances, start_seconds, end_seconds)

            if related_utterances:
                start_seconds = self.parse_time_to_seconds(related_utterances[0]["start_time"])
                end_seconds = self.parse_time_to_seconds(related_utterances[-1]["end_time"])

            if end_seconds < start_seconds:
                end_seconds = start_seconds

            processed_segments.append(
                {
                    "segment_id": index,
                    "title": seg.get("title", f"议题 {index}"),
                    "start_time": start_seconds,
                    "end_time": end_seconds,
                    "duration": end_seconds - start_seconds,
                    "summary": seg.get("summary", seg.get("segment_focus", "")),
                    "key_points": seg.get("key_points", []),
                    "speaker_ids": seg.get("speaker_ids", []),
                    "transcript": self._join_utterances(related_utterances) or transcript,
                    "utterance_ids": [item.get("utterance_id") for item in related_utterances],
                }
            )

        if not processed_segments:
            processed_segments.append(
                {
                    "segment_id": 1,
                    "title": "完整会议",
                    "start_time": 0.0,
                    "end_time": video_duration,
                    "duration": video_duration,
                    "summary": "未能自动识别议题，保留为完整会议。",
                    "key_points": [],
                    "speaker_ids": [],
                    "transcript": transcript,
                    "utterance_ids": [],
                }
            )

        return processed_segments

    def _build_source_text(self, transcript: str, utterances: List[Dict]) -> str:
        if utterances:
            lines = []
            for item in utterances:
                lines.append(
                    f"[{item.get('start_time')}-{item.get('end_time')}] "
                    f"{item.get('speaker_name', '未知')}/{item.get('role', '未知')}: "
                    f"{item.get('text', '')}"
                )
            return "\n".join(lines)
        return transcript

    def _collect_utterances(
        self,
        utterances: List[Dict],
        start_seconds: float,
        end_seconds: float,
        speaker_ids: List[str],
    ) -> List[Dict]:
        matches = []
        for item in utterances:
            item_start = self.parse_time_to_seconds(item.get("start_time", "00:00:00"))
            item_end = self.parse_time_to_seconds(item.get("end_time", item.get("start_time", "00:00:00")))
            overlaps = item_end >= start_seconds and item_start <= end_seconds
            speaker_match = not speaker_ids or item.get("speaker_id") in speaker_ids
            if overlaps and speaker_match:
                matches.append(item)
        return matches

    def _nearest_utterances(self, utterances: List[Dict], start_seconds: float, end_seconds: float) -> List[Dict]:
        matches = []
        for item in utterances:
            item_start = self.parse_time_to_seconds(item.get("start_time", "00:00:00"))
            if start_seconds <= item_start <= end_seconds:
                matches.append(item)
        return matches

    def _join_utterances(self, utterances: List[Dict]) -> str:
        if not utterances:
            return ""
        return "\n".join(
            [
                f"[{item.get('start_time')}-{item.get('end_time')}] "
                f"{item.get('speaker_name', '未知')}/{item.get('role', '未知')}: {item.get('text', '')}"
                for item in utterances
            ]
        )

    @staticmethod
    def parse_time_to_seconds(time_value) -> float:
        if isinstance(time_value, (int, float)):
            return float(time_value)

        raw_value = str(time_value or "").strip()
        if not raw_value:
            return 0.0

        raw_value = raw_value.strip("[]()")
        raw_value = raw_value.replace("：", ":")

        if re.fullmatch(r"\d{1,2}-\d{1,2}", raw_value):
            raw_value = raw_value.replace("-", ":")

        if "-" in raw_value and ":" in raw_value:
            raw_value = raw_value.split("-", 1)[0].strip()

        parts = [part.strip() for part in raw_value.split(":") if part.strip()]
        if not parts:
            return 0.0

        try:
            values = [int(part) for part in parts]
        except ValueError:
            return 0.0

        if len(values) == 2:
            minutes, seconds = values
            return minutes * 60 + seconds
        if len(values) == 3:
            hours, minutes, seconds = values
            return hours * 3600 + minutes * 60 + seconds
        return 0.0

    @staticmethod
    def format_time(seconds: float) -> str:
        td = timedelta(seconds=int(seconds))
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"
