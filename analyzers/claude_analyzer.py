"""
Anthropic Claude 3.5 Sonnet 视频分析器
"""

import json
import time
import base64
from pathlib import Path
import cv2
from moviepy.editor import VideoFileClip
from anthropic import Anthropic
from .base import VideoAnalyzer


class ClaudeAnalyzer(VideoAnalyzer):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.model_name = "Claude 3.5 Sonnet"
        self.client = Anthropic(api_key=api_key)
    
    def analyze_video(self, video_path, output_dir):
        start_time = time.time()
        
        output_dir = Path(output_dir)
        
        # 提取音频（使用 Whisper API 转录）
        print(f"  🎵 提取音频...")
        video = VideoFileClip(video_path)
        audio_path = output_dir / "audio.mp3"
        video.audio.write_audiofile(str(audio_path), verbose=False, logger=None)
        
        # 使用 OpenAI Whisper 转录（Claude 没有语音API）
        print(f"  🎤 转录音频...")
        from openai import OpenAI
        openai_client = OpenAI()  # 需要 OPENAI_API_KEY
        with open(audio_path, "rb") as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="zh"
            )
        
        # 提取关键帧
        print(f"  🖼️  提取关键帧...")
        frames = self._extract_frames(video_path, output_dir, num_frames=10)
        
        # 编码图片
        images = []
        for frame_path in frames[:5]:  # Claude 限制图片数量
            with open(frame_path, "rb") as f:
                images.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": base64.b64encode(f.read()).decode()
                    }
                })
        
        # 构建消息
        print(f"  🤖 分析中...")
        content = [
            {"type": "text", "text": f"{self.get_prompt()}\n\n会议转录内容：\n{transcript.text[:4000]}"}
        ]
        content.extend(images)
        
        # 调用API
        response = self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2048,
            messages=[{"role": "user", "content": content}]
        )
        
        # 解析响应
        response_text = response.content[0].text
        # 提取JSON（Claude 可能返回带说明的文本）
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        
        result = json.loads(response_text)
        result["processing_time"] = time.time() - start_time
        
        video.close()
        return result
    
    def _extract_frames(self, video_path, output_dir, num_frames=10):
        """提取均匀分布的关键帧"""
        frames_dir = output_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        interval = max(1, total_frames // num_frames)
        
        frames = []
        for i in range(num_frames):
            frame_idx = i * interval
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if ret:
                frame_path = frames_dir / f"frame_{i:04d}.jpg"
                cv2.imwrite(str(frame_path), frame)
                frames.append(frame_path)
        
        cap.release()
        return frames
