"""
Flask Web 应用
提供视频上传、完整会议分析和报告查看能力。
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
import sqlite3

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename

from meeting_pipeline import MeetingAnalysisPipeline
from knowledge.database import MeetingDatabase

load_dotenv()

if os.getenv("HTTP_PROXY"):
    os.environ["http_proxy"] = os.getenv("HTTP_PROXY")
    os.environ["https_proxy"] = os.getenv("HTTPS_PROXY", os.getenv("HTTP_PROXY"))


def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024
    project_root = Path(__file__).resolve().parent.parent
    app.config["UPLOAD_FOLDER"] = Path(os.getenv("UPLOAD_FOLDER", str(project_root / "uploads"))).resolve()
    app.config["OUTPUT_FOLDER"] = Path(os.getenv("OUTPUT_FOLDER", str(project_root / "output"))).resolve()
    app.config["VIDEO_LIBRARY_ROOT"] = Path(
        os.getenv("VIDEO_LIBRARY_ROOT", str(app.config["UPLOAD_FOLDER"]))
    ).resolve()
    app.config["VIDEO_LIBRARY_DB"] = Path(
        os.getenv("VIDEO_LIBRARY_DB", str(project_root / "knowledge" / "meetings.db"))
    ).resolve()
    app.config["UPLOAD_FOLDER"].mkdir(exist_ok=True)
    app.config["OUTPUT_FOLDER"].mkdir(exist_ok=True)

    pipeline = MeetingAnalysisPipeline()

    def load_session_payload(session_id):
        session_dir = app.config["OUTPUT_FOLDER"] / session_id
        if not session_dir.exists():
            return None

        results = {"session_id": session_id}
        for filename, key in {
            "basic_analysis.json": "basic_analysis",
            "structured_transcript.json": "structured_transcript",
            "segments.json": "segments",
            "action_items.json": "action_items",
            "speakers.json": "speakers",
            "decisions.json": "decisions",
            "statistics.json": "statistics",
            "participant_roles.json": "participant_roles",
        }.items():
            path = session_dir / filename
            if path.exists():
                with open(path, "r", encoding="utf-8") as file:
                    results[key] = json.load(file)

        basic = results.get("basic_analysis", {})
        results["summary_card"] = {
            "title": basic.get("title", session_id),
            "summary": basic.get("summary", ""),
            "category": basic.get("category", "未分类"),
            "date": _infer_date(session_id),
            "boss_messages_count": len(basic.get("manager_summary", {}).get("boss_messages", [])),
            "action_items_count": len(results.get("action_items", [])),
            "segments_count": len(results.get("segments", [])),
        }
        return results

    def build_history():
        history = []
        seen = set()

        db_path = Path("knowledge/meetings.db")
        if db_path.exists():
            db = MeetingDatabase(str(db_path))
            try:
                for row in db.list_meetings(limit=100):
                    session_id = row.get("session_id")
                    if not session_id or session_id in seen:
                        continue
                    seen.add(session_id)
                    history.append(
                        {
                            "session_id": session_id,
                            "title": row.get("title") or session_id,
                            "date": row.get("date"),
                            "category": row.get("category") or "未分类",
                            "summary": row.get("summary") or "",
                            "output_dir": row.get("output_dir") or str(app.config["OUTPUT_FOLDER"] / session_id),
                        }
                    )
            finally:
                db.close()

        for session_dir in sorted(app.config["OUTPUT_FOLDER"].iterdir(), reverse=True):
            if not session_dir.is_dir():
                continue
            session_id = session_dir.name
            if session_id in seen:
                continue

            payload = load_session_payload(session_id)
            if not payload:
                continue

            summary_card = payload.get("summary_card", {})
            history.append(
                {
                    "session_id": session_id,
                    "title": summary_card.get("title", session_id),
                    "date": summary_card.get("date"),
                    "category": summary_card.get("category", "未分类"),
                    "summary": summary_card.get("summary", ""),
                    "output_dir": str(session_dir),
                }
            )
        return history

    def load_memory():
        db_path = project_root / "knowledge" / "meetings.db"
        if not db_path.exists():
            return {"tasks": [], "requirements": [], "stats": {}}

        db = MeetingDatabase(str(db_path))
        try:
            tasks = db.list_task_memory(limit=300)
            requirements = db.list_requirement_memory(limit=300)
            for task in tasks:
                task["updates"] = db.get_task_updates(task["id"])[:8]
            for requirement in requirements:
                requirement["updates"] = db.get_requirement_updates(requirement["id"])[:8]
            stats = db.get_statistics()
            return {"tasks": tasks, "requirements": requirements, "stats": stats}
        finally:
            db.close()

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/upload", methods=["POST"])
    def upload_video():
        if "video" not in request.files:
            return jsonify({"error": "没有上传文件"}), 400

        file = request.files["video"]
        if not file.filename:
            return jsonify({"error": "文件名为空"}), 400

        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        filepath = (app.config["UPLOAD_FOLDER"] / safe_filename).resolve()
        file.save(filepath)

        return jsonify(
            {
                "success": True,
                "filename": safe_filename,
                "filepath": str(filepath),
            }
        )

    @app.route("/api/library/videos")
    def list_library_videos():
        library_root = app.config["VIDEO_LIBRARY_ROOT"]
        if not library_root.exists() or not library_root.is_dir():
            return jsonify({"items": [], "root": str(library_root)})

        name_map = {}
        metadata_db = app.config["VIDEO_LIBRARY_DB"]
        if metadata_db.exists():
            conn = sqlite3.connect(metadata_db)
            try:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT saved_name, display_name, original_name, owner_name, project_name, created_at
                    FROM stored_files
                    """
                )
                for saved_name, display_name, original_name, owner_name, project_name, created_at in cur.fetchall():
                    name_map[saved_name] = {
                        "display_name": display_name or original_name or saved_name,
                        "original_name": original_name or display_name or saved_name,
                        "owner_name": owner_name or "",
                        "project_name": project_name or "",
                        "created_at": created_at or "",
                    }
            finally:
                conn.close()

        items = []
        for path in sorted(library_root.iterdir(), reverse=True):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".mp4", ".mov", ".avi", ".mkv", ".m4v"}:
                continue

            stat = path.stat()
            metadata = name_map.get(path.name, {})
            items.append(
                {
                    "name": path.name,
                    "display_name": metadata.get("display_name", path.name),
                    "original_name": metadata.get("original_name", path.name),
                    "filepath": str(path.resolve()),
                    "size": stat.st_size,
                    "owner_name": metadata.get("owner_name", ""),
                    "project_name": metadata.get("project_name", ""),
                    "created_at": metadata.get("created_at", ""),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return jsonify({"items": items, "root": str(library_root)})

    @app.route("/api/analyze", methods=["POST"])
    def analyze_video():
        data = request.json or {}
        filepath = data.get("filepath")
        save_to_db = data.get("save_to_db", True)

        if not filepath or not Path(filepath).exists():
            return jsonify({"error": "文件不存在"}), 400

        try:
            result = pipeline.analyze(
                video_path=filepath,
                output_root=str(app.config["OUTPUT_FOLDER"]),
                mode="complete",
                save_to_db=save_to_db,
            )
            return jsonify(result)
        except Exception as exc:
            return jsonify({"error": str(exc)}), 500

    @app.route("/api/results/<session_id>")
    def get_results(session_id):
        payload = load_session_payload(session_id)
        if not payload:
            return jsonify({"error": "结果不存在"}), 404
        return jsonify(payload)

    @app.route("/api/history")
    def history_list():
        return jsonify({"items": build_history()})

    @app.route("/api/memory")
    def memory_overview():
        return jsonify(load_memory())

    @app.route("/api/history/<session_id>")
    def history_detail(session_id):
        payload = load_session_payload(session_id)
        if not payload:
            return jsonify({"error": "历史记录不存在"}), 404
        return jsonify(payload)

    @app.route("/api/history/<session_id>", methods=["DELETE"])
    def delete_history(session_id):
        removed_db = 0
        db_path = project_root / "knowledge" / "meetings.db"
        if db_path.exists():
            db = MeetingDatabase(str(db_path))
            try:
                removed_db = db.delete_meeting_by_session_id(session_id)
            finally:
                db.close()

        session_dir = (app.config["OUTPUT_FOLDER"] / session_id).resolve()
        removed_files = False
        if session_dir.exists() and session_dir.is_dir():
            shutil.rmtree(session_dir)
            removed_files = True

        if not removed_db and not removed_files:
            return jsonify({"error": "历史记录不存在"}), 404

        return jsonify({
            "success": True,
            "session_id": session_id,
            "removed_db": removed_db,
            "removed_files": removed_files,
        })

    @app.route("/api/download/<session_id>/<file_type>")
    def download_file(session_id, file_type):
        session_dir = app.config["OUTPUT_FOLDER"] / session_id
        file_map = {
            "markdown": "meeting_minutes.md",
            "timeline": "timeline_report.html",
            "json": "basic_analysis.json",
            "pdf": "meeting_report.pdf",
            "speakers": "speaker_report.md",
            "decisions": "decision_report.md",
            "structured": "structured_transcript.json",
        }
        filename = file_map.get(file_type)
        if not filename:
            return jsonify({"error": "不支持的文件类型"}), 400

        filepath = (session_dir / filename).resolve()
        if not filepath.exists():
            return jsonify({"error": "文件不存在"}), 404

        return send_file(filepath, as_attachment=True)

    @app.route("/view/<session_id>")
    def view_report(session_id):
        report_path = (app.config["OUTPUT_FOLDER"] / session_id / "timeline_report.html").resolve()
        if not report_path.exists():
            return "报告不存在", 404

        with open(report_path, "r", encoding="utf-8") as file:
            return file.read()

    return app


def _infer_date(session_id: str) -> str:
    try:
        raw = session_id.rsplit("_", 2)
        stamp = f"{raw[-2]}_{raw[-1]}"
        return datetime.strptime(stamp, "%Y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return ""


if __name__ == "__main__":
    create_app().run(debug=True, host="0.0.0.0", port=5000)
