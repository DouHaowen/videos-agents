"""
说话人识别与角色汇总模块
优先使用结构化转录中的参与者与发言片段。
"""

from typing import Dict, List


class SpeakerDiarizer:
    """说话人识别器。"""

    def __init__(self, client):
        self.client = client

    def identify_speakers(
        self,
        transcript: str,
        segments: List[Dict] = None,
        utterances: List[Dict] = None,
        participant_roles: List[Dict] = None,
    ) -> List[Dict]:
        segments = segments or []
        utterances = utterances or []
        participant_roles = participant_roles or []

        by_speaker = {}
        total_chars = 0

        for item in utterances:
            speaker_id = item.get("speaker_id", "未知")
            text = item.get("text", "")
            total_chars += len(text)
            entry = by_speaker.setdefault(
                speaker_id,
                {
                    "speaker_id": speaker_id,
                    "speaker_name": item.get("speaker_name", "未知"),
                    "role": item.get("role", "未知"),
                    "segments": [],
                    "word_count": 0,
                    "total_duration": 0.0,
                    "is_manager": item.get("role") == "老板",
                },
            )
            entry["segments"].append(
                {
                    "text": text,
                    "start_time": item.get("start_time"),
                    "end_time": item.get("end_time"),
                    "context": self._find_context(item, segments),
                }
            )
            entry["word_count"] += len(text)
            entry["total_duration"] += self._duration(item)

        for role_info in participant_roles:
            speaker_id = role_info.get("speaker_id")
            if not speaker_id:
                continue
            entry = by_speaker.setdefault(
                speaker_id,
                {
                    "speaker_id": speaker_id,
                    "speaker_name": role_info.get("speaker_name", "未知"),
                    "role": role_info.get("role", "未知"),
                    "segments": [],
                    "word_count": 0,
                    "total_duration": 0.0,
                    "is_manager": role_info.get("is_manager", False),
                },
            )
            entry["speaker_name"] = role_info.get("speaker_name", entry["speaker_name"])
            entry["role"] = role_info.get("role", entry["role"])
            entry["is_manager"] = role_info.get("is_manager", entry.get("is_manager", False))

        speakers = list(by_speaker.values())
        for speaker in speakers:
            if total_chars > 0:
                speaker["participation_rate"] = speaker["word_count"] / total_chars * 100
            else:
                speaker["participation_rate"] = 0.0

        speakers.sort(key=lambda item: item.get("participation_rate", 0), reverse=True)
        return speakers

    def generate_speaker_report(self, speakers: List[Dict]) -> str:
        report = "# 发言人分析报告\n\n"
        report += f"## 总览\n\n- 识别到 {len(speakers)} 位发言人\n\n"
        report += "## 发言人详情\n\n"

        for index, speaker in enumerate(speakers, 1):
            report += f"### {index}. {speaker.get('speaker_name', '未知')} ({speaker.get('speaker_id', '未知')})\n\n"
            report += f"- 角色: {speaker.get('role', '未知')}\n"
            report += f"- 是否管理者: {'是' if speaker.get('is_manager') else '否'}\n"
            report += f"- 发言字数: {speaker.get('word_count', 0)}\n"
            report += f"- 参与度: {speaker.get('participation_rate', 0):.1f}%\n"
            report += f"- 发言时长: {speaker.get('total_duration', 0):.1f} 秒\n\n"
            report += "**代表性发言**:\n"
            for seg in speaker.get("segments", [])[:3]:
                report += f"- [{seg.get('start_time', '00:00')}] {seg.get('text', '')[:120]}\n"
            report += "\n"

        return report

    def _find_context(self, utterance: Dict, segments: List[Dict]) -> str:
        start_time = utterance.get("start_time")
        if not start_time:
            return "会议讨论"

        from processors.segmenter import MeetingSegmenter

        start_seconds = MeetingSegmenter.parse_time_to_seconds(start_time)
        for segment in segments:
            if segment.get("start_time", 0) <= start_seconds <= segment.get("end_time", 0):
                return segment.get("title", "会议讨论")
        return "会议讨论"

    def _duration(self, utterance: Dict) -> float:
        from processors.segmenter import MeetingSegmenter

        start = MeetingSegmenter.parse_time_to_seconds(utterance.get("start_time", "00:00:00"))
        end = MeetingSegmenter.parse_time_to_seconds(utterance.get("end_time", utterance.get("start_time", "00:00:00")))
        return max(0.0, end - start)
