"""
决策点检测模块
自动识别会议中的关键决策时刻
"""

import json
from typing import List, Dict


class DecisionDetector:
    """决策点检测器"""
    
    def __init__(self, client):
        """
        初始化检测器
        
        Args:
            client: AI 客户端
        """
        self.client = client
    
    def detect_decisions(
        self,
        transcript: str,
        segments: List[Dict] = None
    ) -> List[Dict]:
        """
        检测会议中的决策点
        
        Args:
            transcript: 会议转录文本
            segments: 分段信息（可选）
        
        Returns:
            决策点列表，每项包含：
            {
                "decision_id": int,
                "title": str,           # 决策标题
                "description": str,     # 决策描述
                "rationale": str,       # 决策理由
                "alternatives": List[str],  # 考虑过的其他方案
                "impact": str,          # 影响程度（高/中/低）
                "stakeholders": List[str],  # 相关人员
                "segment_id": int,      # 所属议题
                "timestamp": str        # 时间戳（如果有）
            }
        """
        prompt = f"""请分析以下会议转录内容，识别所有的决策点。

会议转录：
{transcript[:4000]}

决策点的特征：
1. 明确的决定或结论（"我们决定..."、"最终确定..."）
2. 方案选择（"选择方案A"、"采用XX方案"）
3. 行动承诺（"我们将..."、"下一步..."）
4. 资源分配（"投入XX"、"分配XX"）
5. 时间节点确定（"截止日期是..."）

对于每个决策点，请提取：
- 决策的核心内容
- 为什么做出这个决策
- 是否讨论过其他方案
- 这个决策的重要程度
- 涉及哪些人或团队

请以 JSON 格式返回：
{{
  "decisions": [
    {{
      "title": "决策标题（简短）",
      "description": "决策的详细描述",
      "rationale": "做出这个决策的原因",
      "alternatives": ["考虑过的其他方案1", "方案2"],
      "impact": "高/中/低",
      "stakeholders": ["相关人员1", "相关人员2"]
    }}
  ]
}}

注意：
- 只提取明确的决策，不要包含讨论或建议
- 如果没有明确决策，返回空列表
- 影响程度根据决策的重要性和影响范围判断
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
        decisions = result.get("decisions", [])
        
        # 添加 ID 和关联到分段
        for i, decision in enumerate(decisions, 1):
            decision['decision_id'] = i
            
            # 如果有分段信息，尝试关联
            if segments:
                decision['segment_id'] = self._find_related_segment(
                    decision, segments
                )
        
        return decisions
    
    def _find_related_segment(self, decision: Dict, segments: List[Dict]) -> int:
        """找到决策所属的议题"""
        decision_text = decision.get('description', '').lower()
        
        # 简单的关键词匹配
        for seg in segments:
            seg_text = seg.get('transcript', '').lower()
            if any(word in seg_text for word in decision_text.split()[:5]):
                return seg.get('segment_id', 1)
        
        return 1  # 默认第一个议题
    
    def generate_decision_report(self, decisions: List[Dict]) -> str:
        """
        生成决策点报告
        
        Args:
            decisions: 决策点列表
        
        Returns:
            Markdown 格式的报告
        """
        if not decisions:
            return "# 决策点分析\n\n本次会议未识别到明确的决策点。\n"
        
        report = "# 决策点分析\n\n"
        report += f"## 总览\n\n"
        report += f"- 识别到 {len(decisions)} 个关键决策\n"
        
        # 按影响程度分类
        high_impact = [d for d in decisions if d.get('impact') == '高']
        medium_impact = [d for d in decisions if d.get('impact') == '中']
        low_impact = [d for d in decisions if d.get('impact') == '低']
        
        report += f"- 高影响决策: {len(high_impact)} 个\n"
        report += f"- 中影响决策: {len(medium_impact)} 个\n"
        report += f"- 低影响决策: {len(low_impact)} 个\n\n"
        
        report += "## 决策详情\n\n"
        
        for decision in decisions:
            impact_emoji = {
                '高': '🔴',
                '中': '🟡',
                '低': '🟢'
            }.get(decision.get('impact', '中'), '⚪')
            
            report += f"### {impact_emoji} 决策 {decision['decision_id']}: {decision.get('title', '未命名')}\n\n"
            report += f"**描述**: {decision.get('description', '无')}\n\n"
            report += f"**理由**: {decision.get('rationale', '无')}\n\n"
            
            alternatives = decision.get('alternatives', [])
            if alternatives:
                report += "**考虑过的其他方案**:\n"
                for alt in alternatives:
                    report += f"- {alt}\n"
                report += "\n"
            
            stakeholders = decision.get('stakeholders', [])
            if stakeholders:
                report += f"**相关人员**: {', '.join(stakeholders)}\n\n"
            
            report += f"**影响程度**: {decision.get('impact', '未知')}\n\n"
            report += "---\n\n"
        
        return report
