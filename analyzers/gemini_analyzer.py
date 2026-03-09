"""
Gemini 视频分析器
"""

import json
import time
from pathlib import Path
import google.generativeai as genai
from .base import VideoAnalyzer


class GeminiAnalyzer(VideoAnalyzer):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.model_name = "Gemini 2.0 Flash"
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
    
    def analyze_video(self, video_path, output_dir):
        start_time = time.time()
        
        # 上传视频
        print(f"  📤 上传视频...")
        video_file = genai.upload_file(path=video_path)
        
        # 等待处理
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)
        
        if video_file.state.name == "FAILED":
            raise ValueError("视频处理失败")
        
        print(f"  🤖 分析中...")
        
        # 分析视频
        response = self.model.generate_content(
            [video_file, self.get_prompt()],
            generation_config=genai.GenerationConfig(
                temperature=0.3,
                response_mime_type="application/json"
            )
        )
        
        result = json.loads(response.text)
        result["processing_time"] = time.time() - start_time
        
        # 清理
        genai.delete_file(video_file.name)
        
        return result
