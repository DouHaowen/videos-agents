"""
统一会议分析流程
供 CLI 和 Web 共用。
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict

import cv2
from dotenv import load_dotenv

from exporters.markdown_exporter import MarkdownExporter
from knowledge.database import MeetingDatabase
from llm_client import build_llm_client
from processors.action_item_extractor import ActionItemExtractor
from processors.audio_transcriber import AudioTranscriber
from processors.decision_detector import DecisionDetector
from processors.meeting_insights import MeetingInsightExtractor
from processors.segmenter import MeetingSegmenter
from processors.speaker_diarizer import SpeakerDiarizer
from processors.structured_transcript import StructuredTranscriptProcessor
from processors.task_tracker import TaskTracker
from timeline_report_generator import TimelineReportGenerator

load_dotenv()


class MeetingAnalysisPipeline:
    """统一会议分析编排器。"""

    def __init__(self):
        self.transcriber = AudioTranscriber(
            api_key=os.getenv("OPENAI_API_KEY"),
            whisper_base_url=os.getenv("WHISPER_API_BASE"),
            whisper_api_token=os.getenv("WHISPER_API_TOKEN"),
            tunnel_config={
                "host": os.getenv("WHISPER_SSH_HOST"),
                "port": os.getenv("WHISPER_SSH_PORT", "22"),
                "user": os.getenv("WHISPER_SSH_USER"),
                "local_port": os.getenv("WHISPER_LOCAL_PORT", "8711"),
                "remote_port": os.getenv("WHISPER_REMOTE_PORT", "8711"),
            },
        )

    def analyze(
        self,
        video_path: str,
        output_root: str = "output",
        mode: str = "complete",
        save_to_db: bool = False,
        analysis_model: str = None,
    ) -> Dict:
        output_dir = Path(output_root)
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_prefix = {
            "deep": "deep_analysis",
            "complete": "complete_analysis",
        }.get(mode, "analysis")
        session_id = f"{session_prefix}_{timestamp}"
        session_dir = output_dir / session_id
        session_dir.mkdir(exist_ok=True)
        llm_client, model_info = build_llm_client(analysis_model)

        video_duration = self._get_video_duration(video_path)

        transcription = self.transcriber.transcribe_video(video_path, session_dir)
        self._write_json(session_dir / "transcription.json", transcription)
        full_transcript_text = (transcription.get("raw_text") or transcription.get("transcript") or "").strip()
        if full_transcript_text:
            with open(session_dir / "full_transcript.txt", "w", encoding="utf-8") as file:
                file.write(full_transcript_text + "\n")

        structured = StructuredTranscriptProcessor(llm_client).analyze_transcript(
            transcription.get("transcript", ""),
            transcription.get("utterances", []),
        )
        transcript = structured.get("transcript", "")
        utterances = structured.get("utterances", [])
        participants = structured.get("participants", [])

        insights = MeetingInsightExtractor(llm_client).extract(transcript, participants, utterances)
        participant_roles = insights.get("participant_roles", participants)

        speaker_map = {item.get("speaker_id"): item for item in participant_roles if item.get("speaker_id")}
        for utterance in utterances:
            participant = speaker_map.get(utterance.get("speaker_id"), {})
            utterance["speaker_name"] = participant.get("speaker_name", utterance.get("speaker_name", "未知"))
            utterance["role"] = participant.get("role", utterance.get("role", "未知"))

        basic_analysis = {
            "title": structured.get("title", "会议分析"),
            "summary": structured.get("summary", ""),
            "key_points": structured.get("key_points", []),
            "category": structured.get("category", "工作"),
            "analysis_model": model_info,
            "transcript": transcript,
            "participants": participant_roles,
            "manager_summary": {
                "boss_messages": insights.get("boss_messages", []),
                "employee_updates": insights.get("employee_updates", []),
                "risks": insights.get("risks", []),
                "next_steps": insights.get("next_steps", []),
            },
        }
        self._write_json(session_dir / "basic_analysis.json", basic_analysis)
        self._write_json(
            session_dir / "structured_transcript.json",
            {
                **structured,
                "utterances": utterances,
                "transcript": transcript,
            },
        )
        self._write_json(session_dir / "participant_roles.json", participant_roles)

        segmenter = MeetingSegmenter(llm_client)
        segments = segmenter.segment_meeting(transcript, video_duration, utterances=utterances)
        self._write_json(session_dir / "segments.json", segments)

        extractor = ActionItemExtractor(llm_client)
        action_items = extractor.extract_action_items(transcript, segments, utterances=utterances)
        self._write_json(session_dir / "action_items.json", action_items)

        diarizer = SpeakerDiarizer(llm_client)
        speakers = diarizer.identify_speakers(
            transcript,
            segments,
            utterances=utterances,
            participant_roles=participant_roles,
        )
        self._write_json(session_dir / "speakers.json", speakers)
        with open(session_dir / "speaker_report.md", "w", encoding="utf-8") as file:
            file.write(diarizer.generate_speaker_report(speakers))

        detector = DecisionDetector(llm_client)
        decisions = detector.detect_decisions(transcript, segments, utterances=utterances)
        self._write_json(session_dir / "decisions.json", decisions)
        with open(session_dir / "decision_report.md", "w", encoding="utf-8") as file:
            file.write(detector.generate_decision_report(decisions))

        meeting_info = {
            "date": datetime.now().strftime("%Y年%m月%d日"),
            "title": basic_analysis.get("title", "会议分析"),
            "duration": MeetingSegmenter.format_time(video_duration),
        }

        markdown_exporter = MarkdownExporter()
        markdown_exporter.export_meeting_minutes(
            basic_analysis,
            segments,
            action_items,
            session_dir,
            meeting_info,
            speakers=speakers,
            decisions=decisions,
        )

        TimelineReportGenerator().generate_timeline_report(
            basic_analysis,
            segments,
            action_items,
            session_dir,
            speakers=speakers,
            decisions=decisions,
        )

        pdf_generated = False
        try:
            from exporters.pdf_exporter import PDFExporter

            PDFExporter().export_meeting_report(
                basic_analysis,
                segments,
                action_items,
                session_dir,
                meeting_info,
                speakers,
                decisions,
            )
            pdf_generated = True
        except Exception as exc:
            with open(session_dir / "pdf_error.log", "w", encoding="utf-8") as file:
                file.write(str(exc))

        if save_to_db:
            db = MeetingDatabase()
            try:
                meeting_id = db.save_meeting(
                    title=meeting_info["title"],
                    date=meeting_info["date"],
                    analysis=basic_analysis,
                    segments=segments,
                    action_items=action_items,
                    video_path=video_path,
                    speakers=speakers,
                    decisions=decisions,
                    duration=video_duration,
                    session_id=session_id,
                    output_dir=str(session_dir),
                )
                existing_tasks = db.list_task_memory(limit=300)
                memory_sync = db.sync_memory(
                    meeting_id=meeting_id,
                    analysis=basic_analysis,
                    action_items=action_items,
                )
                progress_updates = TaskTracker(llm_client).detect_updates(transcript, existing_tasks)
                progress_sync = db.apply_task_progress_updates(meeting_id, progress_updates)
                memory_sync.update(progress_sync)
                memory_sync["task_updates_detected"] = len(progress_updates)
            finally:
                db.close()
        else:
            memory_sync = {
                "tasks_created": 0,
                "tasks_updated": 0,
                "requirements_created": 0,
                "requirements_updated": 0,
                "tasks_progressed": 0,
                "tasks_completed": 0,
                "tasks_blocked": 0,
                "task_updates_detected": 0,
            }

        statistics = {
            "video_duration": video_duration,
            "audio_duration": transcription.get("duration", video_duration),
            "segments_count": len(segments),
            "action_items_count": len(action_items),
            "speakers_count": len(speakers),
            "decisions_count": len(decisions),
            "utterances_count": len(utterances),
            "participants_count": len(participant_roles),
            "boss_messages_count": len(insights.get("boss_messages", [])),
            "transcript_length": len(transcript),
            "pdf_generated": pdf_generated,
            "analysis_model": model_info,
            "transcription_usage": transcription.get("usage", []),
            "memory_sync": memory_sync,
        }
        self._write_json(session_dir / "statistics.json", statistics)

        return {
            "success": True,
            "session_id": session_id,
            "session_dir": str(session_dir),
            "summary": basic_analysis.get("summary"),
            "title": basic_analysis.get("title"),
            "category": basic_analysis.get("category"),
            "analysis_model": model_info,
            "segments_count": len(segments),
            "action_items_count": len(action_items),
            "speakers_count": len(speakers),
            "decisions_count": len(decisions),
            "participants": participant_roles,
            "boss_messages": insights.get("boss_messages", []),
            "employee_updates": insights.get("employee_updates", []),
            "risks": insights.get("risks", []),
            "next_steps": insights.get("next_steps", []),
            "pdf_generated": pdf_generated,
            "memory_sync": memory_sync,
        }

    def _get_video_duration(self, video_path: str) -> float:
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()
        return frame_count / fps if fps > 0 else 0.0

    def _write_json(self, path: Path, payload: Dict):
        with open(path, "w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
