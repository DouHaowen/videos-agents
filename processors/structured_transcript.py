"""
结构化会议理解模块
基于转录文本生成会议标题、摘要、分类和参与者角色。
"""

import json
from typing import Dict, List

from llm_client import GenerationConfig
from .llm_utils import parse_json_response


class StructuredTranscriptProcessor:
    """基于文字转录生成结构化会议信息。"""

    def __init__(self, client):
        self.client = client

    def analyze_transcript(self, transcript: str, utterances: List[Dict]) -> Dict:
        source_text = self._build_source_text(transcript, utterances)
        prompt = f"""请基于以下会议转录，生成结构化会议记录。

会议内容：
{source_text}

请返回 JSON：
{{
  "title": "会议标题",
  "summary": "会议摘要",
  "key_points": ["关键点1", "关键点2"],
  "category": "工作/其他",
  "participants": [
    {{
      "speaker_id": "speaker_0",
      "speaker_name": "张三或未知",
      "role": "老板/主持人/前端/后端/产品/测试/运营/员工/未知",
      "is_manager": true
    }}
  ]
}}

要求：
- title 要尽量具体，不要写成泛泛的“会议分析”。
- 如果无法识别姓名，speaker_name 用未知。
- 尽量识别谁是老板或主管。"""

        data = self._generate_json(prompt)
        participants = data.get("participants", []) or []

        participant_map = {item.get("speaker_id"): item for item in participants if item.get("speaker_id")}
        normalized_utterances = []
        transcript_lines = []

        for index, item in enumerate(utterances, 1):
            participant = participant_map.get(item.get("speaker_id"), {})
            speaker_name = participant.get("speaker_name") or item.get("speaker_name") or item.get("speaker_id", f"speaker_{index}")
            role = participant.get("role") or item.get("role") or "未知"
            normalized = {
                "utterance_id": item.get("utterance_id", index),
                "speaker_id": item.get("speaker_id", f"speaker_{index}"),
                "speaker_name": speaker_name,
                "role": role,
                "start_seconds": item.get("start_seconds", 0.0),
                "end_seconds": item.get("end_seconds", item.get("start_seconds", 0.0)),
                "start_time": item.get("start_time", "00:00:00"),
                "end_time": item.get("end_time", item.get("start_time", "00:00:00")),
                "text": item.get("text", "").strip(),
            }
            normalized_utterances.append(normalized)
            transcript_lines.append(
                f"[{normalized['start_time']}-{normalized['end_time']}] {speaker_name}/{role}: {normalized['text']}"
            )

        return {
            "title": data.get("title", "会议分析"),
            "summary": data.get("summary", ""),
            "key_points": data.get("key_points", []),
            "category": data.get("category", "工作"),
            "participants": participants,
            "utterances": normalized_utterances,
            "transcript": "\n".join(transcript_lines),
        }

    def _build_source_text(self, transcript: str, utterances: List[Dict]) -> str:
        if utterances:
            return "\n".join(
                [
                    f"[{item.get('start_time', '00:00:00')}-{item.get('end_time', '00:00:00')}] "
                    f"{item.get('speaker_id', 'speaker_unknown')}: {item.get('text', '')}"
                    for item in utterances
                    if item.get("text")
                ]
            )
        return transcript

    def _generate_json(self, prompt: str) -> Dict:
        last_error = None
        prompts = [
            prompt,
            prompt + "\n\n再次强调：必须返回严格合法的 JSON，不能输出解释，不能丢逗号。",
        ]

        for current_prompt in prompts:
            try:
                response = self.client.generate_content(
                    current_prompt,
                    generation_config=GenerationConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )
                return parse_json_response(response.text)
            except json.JSONDecodeError as exc:
                last_error = exc
                continue

        raise ValueError(f"会议结构化分析失败，返回 JSON 无法解析: {last_error}")
