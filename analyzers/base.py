"""
多模型视频分析器基类
"""

from abc import ABC, abstractmethod
from pathlib import Path


class VideoAnalyzer(ABC):
    """视频分析器基类"""
    
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model_name = "Unknown"
    
    @abstractmethod
    def analyze_video(self, video_path, output_dir):
        """
        分析视频并返回结构化结果
        
        Args:
            video_path: 视频文件路径
            output_dir: 输出目录
        
        Returns:
            dict: {
                "summary": str,
                "key_points": list[str],
                "category": str,
                "subcategories": list[str],
                "action_items": list[str],
                "processing_time": float
            }
        """
        pass
    
    def get_prompt(self):
        """获取统一的分析提示词"""
        return """请仔细分析这个会议视频，提供以下信息：

1. **会议主题摘要**（1-2句话概括会议的核心内容）
2. **主要讨论点**（列出3-5个关键讨论点）
3. **场景分类**（从以下类别中选择最合适的主分类和子分类）：
   - 工作：会议、电话、头脑风暴、项目讨论
   - 私生活：社交、休闲、家庭
   - 健康/休息：睡眠、放松、冥想
   - 运动：跑步、健身、游泳、其他运动
   - 出行：通勤、旅行、飞行
4. **关键决策或行动项**（如果有的话）

请以JSON格式返回，包含以下字段：
{
  "summary": "会议摘要文本",
  "key_points": ["讨论点1", "讨论点2", "讨论点3"],
  "category": "主分类名称",
  "subcategories": ["子分类1", "子分类2"],
  "action_items": ["行动项1", "行动项2"]
}

注意：
- 请基于视频中的画面和声音进行综合分析
- 如果没有明确的行动项，action_items 可以是空列表
- 子分类可以有多个，选择最相关的
"""
