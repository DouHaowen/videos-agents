"""
跨会议任务追踪器
用于根据本次会议内容回写全局任务状态。
"""

from typing import Dict, List

import google.generativeai as genai

from .llm_utils import parse_json_response


class TaskTracker:
    """识别本次会议中提到的历史任务进展。"""

    def __init__(self, client):
        self.client = client

    def detect_updates(self, transcript: str, tasks: List[Dict]) -> List[Dict]:
        if not transcript or not tasks:
            return []

        candidate_tasks = [
            task for task in tasks
            if task.get("status") != "completed" or task.get("occurrence_count", 0) <= 3
        ][:80]
        if not candidate_tasks:
            return []

        task_digest = [
            {
                "task_id": task.get("id"),
                "title": task.get("title"),
                "owner": task.get("owner"),
                "status": task.get("status"),
                "deadline": task.get("deadline"),
                "source_meeting": task.get("created_from_meeting_title"),
                "source_date": task.get("created_from_meeting_date"),
            }
            for task in candidate_tasks
        ]

        prompt = f"""你是会议任务跟踪助手。请基于历史任务总表和本次会议转录，识别哪些历史任务在这次会议里被明确提到，并判断其状态变化。

历史任务总表：
{task_digest}

本次会议转录：
{transcript[:14000]}

判断规则：
1. 只有在会议里有明确证据时才输出更新。
2. update_type 只能是 progress、completed、blocked、reopened。
3. 如果只是模糊提到，不要输出。
4. summary 用一句中文说明本次会议对该任务的最新结论。
5. source_context 提取支持判断的原话片段，尽量短。

请返回 JSON：
{{
  "updates": [
    {{
      "task_id": 12,
      "update_type": "completed",
      "summary": "首页改版已完成并准备上线。",
      "source_context": "首页交互已经全部调完了，今晚可以上线。"
    }}
  ]
}}"""

        response = self.client.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            ),
        )
        data = parse_json_response(response.text)

        valid_ids = {task.get("id") for task in candidate_tasks}
        updates = []
        for item in data.get("updates", []):
            task_id = item.get("task_id")
            update_type = item.get("update_type")
            if task_id not in valid_ids:
                continue
            if update_type not in {"progress", "completed", "blocked", "reopened"}:
                continue
            updates.append(
                {
                    "task_id": task_id,
                    "update_type": update_type,
                    "summary": item.get("summary", ""),
                    "source_context": item.get("source_context", ""),
                }
            )
        return updates
