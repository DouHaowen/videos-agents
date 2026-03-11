"""
音频提取与转录模块
从视频中抽取音频，使用 OpenAI Speech-to-Text 生成带说话人的转录。
"""

import json
import math
import os
import socket
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from moviepy import VideoFileClip
from openai import OpenAI
import requests


class AudioTranscriber:
    """视频音频转录器。"""

    MAX_AUDIO_FILE_SIZE = 24 * 1024 * 1024
    DEFAULT_CHUNK_SECONDS = 20 * 60

    def __init__(
        self,
        api_key: Optional[str] = None,
        whisper_base_url: Optional[str] = None,
        whisper_api_token: Optional[str] = None,
        tunnel_config: Optional[Dict] = None,
    ):
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.whisper_base_url = (whisper_base_url or "").rstrip("/")
        self.whisper_api_token = whisper_api_token
        self.tunnel_config = tunnel_config or {}

        if not self.client and not self.whisper_base_url:
            raise ValueError("未配置可用转录能力，请设置 OPENAI_API_KEY 或 WHISPER_API_BASE")

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
        if self.whisper_base_url:
            try:
                self._ensure_local_whisper_ready()
                return self._transcribe_with_local_whisper(file_path)
            except Exception:
                if not self.client:
                    raise

        if not self.client:
            raise ValueError("本地 Whisper 不可用，且未配置 OPENAI_API_KEY")

        return self._transcribe_with_openai(file_path)

    def _transcribe_with_openai(self, file_path: Path) -> Dict:
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

    def _transcribe_with_local_whisper(self, file_path: Path) -> Dict:
        with open(file_path, "rb") as audio_file:
            response = requests.post(
                f"{self.whisper_base_url}/transcribe",
                files={"file": (file_path.name, audio_file, "audio/mpeg")},
                data={"language": "zh", "task": "transcribe"},
                headers=self._build_whisper_headers(),
                timeout=60 * 60,
            )
        response.raise_for_status()
        payload = response.json()
        return {
            "text": payload.get("text", ""),
            "segments": payload.get("segments", []),
            "usage": None,
            "duration": payload.get("duration"),
            "model": payload.get("model"),
        }

    def _ensure_local_whisper_ready(self):
        if self._local_whisper_healthy():
            return
        self._start_ssh_tunnel_if_needed()

        for _ in range(30):
            if self._local_whisper_healthy():
                return
            time.sleep(1)

        raise RuntimeError("本地 Whisper 服务不可用")

    def _local_whisper_healthy(self) -> bool:
        health_url = f"{self.whisper_base_url}/health"
        try:
            response = requests.get(health_url, headers=self._build_whisper_headers(), timeout=3)
            return response.ok
        except requests.RequestException:
            return False

    def _start_ssh_tunnel_if_needed(self):
        if not self.tunnel_config.get("host") or not self.tunnel_config.get("user"):
            return

        parsed = urlparse(self.whisper_base_url)
        local_host = parsed.hostname or "127.0.0.1"
        local_port = parsed.port or self.tunnel_config.get("local_port") or 8711
        remote_port = self.tunnel_config.get("remote_port") or local_port

        if self._is_port_open(local_host, local_port):
            return

        command = [
            "ssh",
            "-f",
            "-N",
            "-L",
            f"{local_host}:{local_port}:127.0.0.1:{remote_port}",
            "-p",
            str(self.tunnel_config.get("port", 22)),
            f"{self.tunnel_config['user']}@{self.tunnel_config['host']}",
        ]
        subprocess.run(command, check=False, capture_output=True)

    def _is_port_open(self, host: str, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            return sock.connect_ex((host, port)) == 0

    def _build_whisper_headers(self) -> Dict[str, str]:
        if not self.whisper_api_token:
            return {}
        return {"Authorization": f"Bearer {self.whisper_api_token}"}

    def _format_time(self, seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
