"""
会议洞察提取器
用于角色识别、老板要求、员工汇报和风险提炼。
"""

from typing import Dict, List

import google.generativeai as genai

from .llm_utils import chunk_text, merge_unique_dicts, parse_json_response


class MeetingInsightExtractor:
    """从结构化转录中提炼管理视角信息。"""

    def __init__(self, client):
        self.client = client

    def extract(self, transcript: str, participants: List[Dict], utterances: List[Dict]) -> Dict:
        chunks = chunk_text(transcript, max_chars=7000, overlap=600)

        aggregate = {
            "boss_messages": [],
            "employee_updates": [],
            "risks": [],
            "next_steps": [],
            "participant_roles": [],
        }

        for chunk in chunks:
            prompt = f"""请基于以下会议转录，抽取管理视角信息。

已知参与者：
{participants}

会议转录：
{chunk}

请返回 JSON：
{{
  "boss_messages": ["老板明确要求、判断、决策或督办"],
  "employee_updates": [
    {{
      "speaker_id": "发言人ID",
      "speaker_name": "姓名",
      "role": "前端/后端/产品/测试/运营/未知",
      "summary": "该员工在本段里的汇报摘要"
    }}
  ],
  "risks": ["风险、阻塞、延期因素"],
  "next_steps": ["后续动作"],
  "participant_roles": [
    {{
      "speaker_id": "发言人ID",
      "speaker_name": "姓名",
      "role": "老板/主持人/前端/后端/产品/测试/运营/员工/未知",
      "is_manager": true
    }}
  ]
}}"""

            response = self.client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
            data = parse_json_response(response.text)

            aggregate["boss_messages"].extend(data.get("boss_messages", []))
            aggregate["employee_updates"].extend(data.get("employee_updates", []))
            aggregate["risks"].extend(data.get("risks", []))
            aggregate["next_steps"].extend(data.get("next_steps", []))
            aggregate["participant_roles"].extend(data.get("participant_roles", []))

        aggregate["boss_messages"] = self._unique_texts(aggregate["boss_messages"])
        aggregate["risks"] = self._unique_texts(aggregate["risks"])
        aggregate["next_steps"] = self._unique_texts(aggregate["next_steps"])
        aggregate["employee_updates"] = merge_unique_dicts(
            aggregate["employee_updates"],
            ["speaker_id", "summary"],
        )
        aggregate["participant_roles"] = merge_unique_dicts(
            aggregate["participant_roles"],
            ["speaker_id", "role"],
        )

        if not aggregate["participant_roles"]:
            aggregate["participant_roles"] = participants or []

        if not aggregate["employee_updates"]:
            aggregate["employee_updates"] = self._build_fallback_updates(utterances)

        return aggregate

    def _unique_texts(self, items: List[str]) -> List[str]:
        seen = set()
        results = []
        for item in items:
            normalized = item.strip()
            if not normalized:
                continue
            key = normalized.lower()
            if key in seen:
                continue
            seen.add(key)
            results.append(normalized)
        return results

    def _build_fallback_updates(self, utterances: List[Dict]) -> List[Dict]:
        grouped = {}
        for item in utterances:
            speaker_id = item.get("speaker_id")
            if not speaker_id:
                continue
            grouped.setdefault(
                speaker_id,
                {
                    "speaker_id": speaker_id,
                    "speaker_name": item.get("speaker_name", "未知"),
                    "role": item.get("role", "未知"),
                    "texts": [],
                },
            )
            grouped[speaker_id]["texts"].append(item.get("text", ""))

        updates = []
        for entry in grouped.values():
            if entry["role"] == "老板":
                continue
            summary = " ".join(entry["texts"])[:200]
            updates.append(
                {
                    "speaker_id": entry["speaker_id"],
                    "speaker_name": entry["speaker_name"],
                    "role": entry["role"],
                    "summary": summary,
                }
            )
        return updates
