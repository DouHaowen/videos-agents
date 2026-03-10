"""
音频提取与转录模块
从视频中抽取音频，使用 OpenAI Speech-to-Text 生成带说话人的转录。
"""

import json
import math
import os
from pathlib import Path
from typing import Dict, List

from moviepy import VideoFileClip
from openai import OpenAI


class AudioTranscriber:
    """视频音频转录器。"""

    MAX_AUDIO_FILE_SIZE = 24 * 1024 * 1024
    DEFAULT_CHUNK_SECONDS = 20 * 60

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("未配置 OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def transcribe_video(self, video_path: str, output_dir: Path) -> Dict:
        output_dir = Path(output_dir)
        audio_dir = output_dir / "audio"
        audio_dir.mkdir(exist_ok=True)

        audio_files, total_duration = self._extract_audio_chunks(video_path, audio_dir)

        all_segments: List[Dict] = []
        combined_texts: List[str] = []
        usage = []

        for file_path, chunk_offset in audio_files:
            transcription = self._transcribe_file(file_path)
            if transcription.get("text"):
                combined_texts.append(transcription["text"])
            usage.append(transcription.get("usage"))

            for index, segment in enumerate(transcription.get("segments", []), 1):
                start = float(segment.get("start", 0.0)) + chunk_offset
                end = float(segment.get("end", start)) + chunk_offset
                speaker = segment.get("speaker", "speaker_unknown")
                all_segments.append(
                    {
                        "utterance_id": len(all_segments) + 1,
                        "speaker_id": speaker,
                        "speaker_name": speaker,
                        "role": "未知",
                        "start_seconds": start,
                        "end_seconds": end,
                        "start_time": self._format_time(start),
                        "end_time": self._format_time(end),
                        "text": segment.get("text", "").strip(),
                    }
                )

        transcript_text = "\n".join(
            [
                f"[{item['start_time']}-{item['end_time']}] {item['speaker_name']}: {item['text']}"
                for item in all_segments
                if item.get("text")
            ]
        )

        return {
            "audio_files": [str(file_path) for file_path, _ in audio_files],
            "duration": total_duration,
            "utterances": all_segments,
            "transcript": transcript_text,
            "raw_text": "\n".join(combined_texts).strip(),
            "usage": usage,
        }

    def _extract_audio_chunks(self, video_path: str, audio_dir: Path):
        clip = VideoFileClip(video_path)
        duration = float(clip.duration or 0.0)
        audio = clip.audio
        if audio is None:
            clip.close()
            raise ValueError("视频中未检测到音频轨道")

        full_audio_path = audio_dir / "meeting_audio.mp3"
        audio.write_audiofile(
            str(full_audio_path),
            fps=16000,
            bitrate="32k",
            ffmpeg_params=["-ac", "1"],
            logger=None,
        )

        if full_audio_path.stat().st_size <= self.MAX_AUDIO_FILE_SIZE:
            clip.close()
            return [(full_audio_path, 0.0)], duration

        chunk_seconds = self._estimate_chunk_seconds(full_audio_path.stat().st_size, duration)
        audio_files = []
        chunk_count = max(1, math.ceil(duration / chunk_seconds))

        for chunk_index in range(chunk_count):
            start = chunk_index * chunk_seconds
            end = min(duration, (chunk_index + 1) * chunk_seconds)
            subclip = clip.subclipped(start, end)
            chunk_path = audio_dir / f"meeting_audio_part_{chunk_index + 1:03d}.mp3"
            subclip.audio.write_audiofile(
                str(chunk_path),
                fps=16000,
                bitrate="32k",
                ffmpeg_params=["-ac", "1"],
                logger=None,
            )
            subclip.close()
            audio_files.append((chunk_path, start))

        clip.close()
        if full_audio_path.exists():
            os.remove(full_audio_path)
        return audio_files, duration

    def _estimate_chunk_seconds(self, file_size: int, duration: float) -> int:
        if duration <= 0:
            return self.DEFAULT_CHUNK_SECONDS
        safe_ratio = self.MAX_AUDIO_FILE_SIZE / max(file_size, 1)
        estimated = int(duration * safe_ratio * 0.9)
        return max(5 * 60, min(self.DEFAULT_CHUNK_SECONDS, estimated))

    def _transcribe_file(self, file_path: Path) -> Dict:
        with open(file_path, "rb") as audio_file:
            response = self.client.audio.transcriptions.create(
                file=audio_file,
                model="gpt-4o-transcribe-diarize",
                language="zh",
                response_format="diarized_json",
                chunking_strategy="auto",
            )

        if hasattr(response, "model_dump"):
            return response.model_dump()
        if isinstance(response, str):
            return json.loads(response)
        return dict(response)

    def _format_time(self, seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
