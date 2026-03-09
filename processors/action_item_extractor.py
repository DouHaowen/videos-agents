"""
待办事项提取器
从会议内容中自动识别和提取行动项
"""

import json
from typing import List, Dict


class ActionItemExtractor:
    """待办事项提取器"""
    
    def __init__(self, client):
        """
        初始化提取器
        
        Args:
            client: AI 客户端
        """
        self.client = client
    
    def extract_action_items(
        self,
        transcript: str,
        segments: List[Dict] = None
    ) -> List[Dict]:
        """
        从会议内容中提取待办事项
        
        Args:
            transcript: 会议转录文本
            segments: 分段信息（可选，用于更精确的提取）
        
        Returns:
            待办事项列表，每项包含：
            {
                "task": str,           # 任务描述
                "owner": str,          # 负责人
                "deadline": str,       # 截止日期
                "priority": str,       # 优先级（高/中/低）
                "context": str,        # 上下文（来自哪个议题）
                "status": str          # 状态（待开始）
            }
        """
        prompt = f"""请从以下会议内容中提取所有的待办事项（Action Items）。

会议内容：
{transcript[:4000]}  # 限制长度

请识别以下类型的待办事项：
1. 明确提到的任务分配（"XX负责做YY"）
2. 需要跟进的事项（"需要调查/研究/确认..."）
3. 决策后的执行项（"决定做XX，由YY负责"）
4. 会议中承诺的交付物

对于每个待办事项，请提取：
- task: 任务描述（清晰、可执行）
- owner: 负责人（如果提到了名字，否则标记为"待分配"）
- deadline: 截止日期（如果提到了，否则标记为"待定"）
- priority: 优先级（根据讨论的紧急程度判断：高/中/低）
- context: 这个任务来自哪个议题或讨论

请以 JSON 格式返回：
{{
  "action_items": [
    {{
      "task": "任务描述",
      "owner": "负责人",
      "deadline": "截止日期",
      "priority": "优先级",
      "context": "上下文"
    }}
  ]
}}

注意：
- 只提取明确的、可执行的任务
- 如果没有待办事项，返回空列表
- 任务描述要具体，避免模糊
"""
        
        # 调用 LLM
        if hasattr(self.client, 'chat'):  # OpenAI 风格
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
        else:  # Gemini 风格
            import google.generativeai as genai
            response = self.client.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.2,  # 更低的温度以提高准确性
                    response_mime_type="application/json"
                )
            )
            result = json.loads(response.text)
        
        # 处理结果
        action_items = result.get("action_items", [])
        
        # 添加默认状态
        for item in action_items:
            item["status"] = "待开始"
        
        return action_items
