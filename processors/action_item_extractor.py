"""
待办事项提取器
支持长会议分块和结构化发言输入。
"""

from typing import Dict, List

import google.generativeai as genai

from .llm_utils import chunk_text, merge_unique_dicts, parse_json_response


class ActionItemExtractor:
    """待办事项提取器。"""

    def __init__(self, client):
        self.client = client

    def extract_action_items(
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
            prompt = f"""请从以下会议记录中提取所有待办事项。

会议记录：
{chunk}

如有议题信息，可参考：
{segments[:8]}

请返回 JSON：
{{
  "action_items": [
    {{
      "task": "任务描述",
      "owner": "负责人",
      "deadline": "截止日期或待定",
      "priority": "高/中/低",
      "context": "来自哪个议题",
      "source_speaker": "谁提出或负责",
      "status": "待开始"
    }}
  ]
}}

要求：
- 只保留明确可执行事项。
- 如果老板明确布置任务，优先保留。
- owner 不清楚时填 待分配。"""

            response = self.client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
            data = parse_json_response(response.text)
            aggregated.extend(data.get("action_items", []))

        action_items = merge_unique_dicts(aggregated, ["task", "owner"])
        for item in action_items:
            item["status"] = item.get("status", "待开始")
            item["owner"] = item.get("owner") or "待分配"
            item["deadline"] = item.get("deadline") or "待定"
            item["priority"] = item.get("priority") or "中"
            item["context"] = item.get("context") or self._infer_context(item, segments)

        return action_items

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

    def _infer_context(self, item: Dict, segments: List[Dict]) -> str:
        task_text = item.get("task", "").lower()
        for segment in segments or []:
            if task_text and task_text[:12] in segment.get("transcript", "").lower():
                return segment.get("title", "会议讨论")
        return "会议讨论"
