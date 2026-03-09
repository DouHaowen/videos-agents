"""
阿里通义千问 Qwen2-VL 视频分析器
"""

import json
import time
from pathlib import Path
from openai import OpenAI
from .base import VideoAnalyzer


class QwenAnalyzer(VideoAnalyzer):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.model_name = "Qwen2-VL"
        # 通义千问使用 OpenAI 兼容接口
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
    
    def analyze_video(self, video_path, output_dir):
        start_time = time.time()
        
        print(f"  📤 上传视频...")
        
        # Qwen2-VL 支持直接传视频 URL 或本地文件
        # 这里使用本地文件路径
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": self.get_prompt()},
                    {
                        "type": "video",
                        "video": f"file://{Path(video_path).absolute()}"
                    }
                ]
            }
        ]
        
        print(f"  🤖 分析中...")
        
        # 调用API
        response = self.client.chat.completions.create(
            model="qwen2-vl-72b-instruct",
            messages=messages,
            temperature=0.3
        )
        
        # 解析响应
        response_text = response.choices[0].message.content
        
        # 提取JSON
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        
        result = json.loads(response_text)
        result["processing_time"] = time.time() - start_time
        
        return result
