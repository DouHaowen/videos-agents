"""
会议数据库模块
使用 SQLite 存储会议记录
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class MeetingDatabase:
    """会议数据库管理器"""
    
    def __init__(self, db_path: str = "knowledge/meetings.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        
        # 会议表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                date TEXT NOT NULL,
                duration REAL,
                category TEXT,
                summary TEXT,
                manager_summary TEXT,
                session_id TEXT,
                output_dir TEXT,
                video_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        
        # 议题表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                segment_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                start_time REAL,
                end_time REAL,
                duration REAL,
                summary TEXT,
                transcript TEXT,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')
        
        # 待办事项表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                task TEXT NOT NULL,
                owner TEXT,
                deadline TEXT,
                priority TEXT,
                status TEXT DEFAULT '待开始',
                context TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')
        
        # 发言人表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS speakers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                speaker_id TEXT NOT NULL,
                speaker_name TEXT,
                role TEXT,
                word_count INTEGER,
                participation_rate REAL,
                total_duration REAL,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                speaker_id TEXT NOT NULL,
                speaker_name TEXT,
                role TEXT,
                is_manager INTEGER DEFAULT 0,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')
        
        # 决策点表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                decision_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                rationale TEXT,
                impact TEXT,
                segment_id INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')
        
        # 关键词表（用于搜索）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                meeting_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                normalized_title TEXT NOT NULL,
                title TEXT NOT NULL,
                owner TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                priority TEXT,
                deadline TEXT,
                project_name TEXT,
                created_from_meeting_id INTEGER,
                created_from_meeting_title TEXT,
                created_from_meeting_date TEXT,
                last_seen_meeting_id INTEGER,
                last_seen_meeting_title TEXT,
                last_seen_meeting_date TEXT,
                completed_in_meeting_id INTEGER,
                completed_in_meeting_title TEXT,
                completed_in_meeting_date TEXT,
                occurrence_count INTEGER DEFAULT 1,
                latest_summary TEXT,
                latest_context TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                meeting_id INTEGER NOT NULL,
                update_type TEXT NOT NULL,
                summary TEXT,
                owner TEXT,
                status TEXT,
                priority TEXT,
                deadline TEXT,
                source_context TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (task_id) REFERENCES task_memory (id),
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requirement_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                normalized_text TEXT NOT NULL,
                requirement_text TEXT NOT NULL,
                source_type TEXT NOT NULL DEFAULT 'boss_message',
                status TEXT NOT NULL DEFAULT 'active',
                first_meeting_id INTEGER,
                last_seen_meeting_id INTEGER,
                occurrence_count INTEGER DEFAULT 1,
                latest_summary TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requirement_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                requirement_id INTEGER NOT NULL,
                meeting_id INTEGER NOT NULL,
                update_type TEXT NOT NULL,
                summary TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (requirement_id) REFERENCES requirement_memory (id),
                FOREIGN KEY (meeting_id) REFERENCES meetings (id)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_category ON meetings(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_memory_normalized_title ON task_memory(normalized_title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_requirement_memory_normalized_text ON requirement_memory(normalized_text)')
        
        self._ensure_column("meetings", "manager_summary", "TEXT")
        self._ensure_column("meetings", "session_id", "TEXT")
        self._ensure_column("meetings", "output_dir", "TEXT")
        self._ensure_column("task_memory", "created_from_meeting_title", "TEXT")
        self._ensure_column("task_memory", "created_from_meeting_date", "TEXT")
        self._ensure_column("task_memory", "last_seen_meeting_title", "TEXT")
        self._ensure_column("task_memory", "last_seen_meeting_date", "TEXT")
        self._ensure_column("task_memory", "completed_in_meeting_id", "INTEGER")
        self._ensure_column("task_memory", "completed_in_meeting_title", "TEXT")
        self._ensure_column("task_memory", "completed_in_meeting_date", "TEXT")
        self.conn.commit()

    def _ensure_column(self, table_name: str, column_name: str, column_type: str):
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row["name"] for row in cursor.fetchall()}
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
    
    def save_meeting(
        self,
        title: str,
        date: str,
        analysis: Dict,
        segments: List[Dict],
        action_items: List[Dict],
        video_path: str = None,
        speakers: List[Dict] = None,
        decisions: List[Dict] = None,
        duration: float = None,
        session_id: str = None,
        output_dir: str = None,
    ) -> int:
        """
        保存完整的会议记录
        
        Args:
            title: 会议标题
            date: 会议日期
            analysis: 基础分析结果
            segments: 分段信息
            action_items: 待办事项
            video_path: 视频文件路径
            speakers: 发言人信息
            decisions: 决策点信息
            duration: 会议时长
        
        Returns:
            会议ID
        """
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        # 插入会议记录
        cursor.execute('''
            INSERT INTO meetings (title, date, duration, category, summary, manager_summary, session_id, output_dir, video_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title,
            date,
            duration,
            analysis.get('category'),
            analysis.get('summary'),
            json.dumps(analysis.get('manager_summary', {}), ensure_ascii=False),
            session_id,
            output_dir,
            video_path,
            now,
            now
        ))
        
        meeting_id = cursor.lastrowid
        
        # 插入议题
        for seg in segments:
            cursor.execute('''
                INSERT INTO segments (meeting_id, segment_id, title, start_time, end_time, duration, summary, transcript)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                meeting_id,
                seg.get('segment_id'),
                seg.get('title'),
                seg.get('start_time'),
                seg.get('end_time'),
                seg.get('duration'),
                seg.get('summary'),
                seg.get('transcript')
            ))
        
        # 插入待办事项
        for item in action_items:
            cursor.execute('''
                INSERT INTO action_items (meeting_id, task, owner, deadline, priority, status, context, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                meeting_id,
                item.get('task'),
                item.get('owner'),
                item.get('deadline'),
                item.get('priority'),
                item.get('status', '待开始'),
                item.get('context'),
                now
            ))
        
        # 插入发言人
        if speakers:
            for speaker in speakers:
                cursor.execute('''
                    INSERT INTO speakers (meeting_id, speaker_id, speaker_name, role, word_count, participation_rate, total_duration)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    meeting_id,
                    speaker.get('speaker_id'),
                    speaker.get('speaker_name'),
                    speaker.get('role'),
                    speaker.get('word_count'),
                    speaker.get('participation_rate'),
                    speaker.get('total_duration')
                ))

        for participant in analysis.get('participants', []):
            cursor.execute('''
                INSERT INTO participants (meeting_id, speaker_id, speaker_name, role, is_manager)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                meeting_id,
                participant.get('speaker_id'),
                participant.get('speaker_name'),
                participant.get('role'),
                1 if participant.get('is_manager') else 0
            ))
        
        # 插入决策点
        if decisions:
            for decision in decisions:
                cursor.execute('''
                    INSERT INTO decisions (meeting_id, decision_id, title, description, rationale, impact, segment_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    meeting_id,
                    decision.get('decision_id'),
                    decision.get('title'),
                    decision.get('description'),
                    decision.get('rationale'),
                    decision.get('impact'),
                    decision.get('segment_id'),
                    now
                ))
        
        self.conn.commit()
        return meeting_id

    def sync_memory(
        self,
        meeting_id: int,
        analysis: Dict,
        action_items: List[Dict],
    ) -> Dict:
        """将单次会议结果同步到长期任务和要求记忆。"""
        now = datetime.now().isoformat()
        meeting_meta = self._get_meeting_meta(meeting_id)
        tasks_created = 0
        tasks_updated = 0
        requirements_created = 0
        requirements_updated = 0

        for item in action_items:
            normalized_title = self._normalize_text(item.get("task", ""))
            if not normalized_title:
                continue

            existing = self._find_task_memory(normalized_title, item.get("owner"))
            update_type = self._classify_task_update(item)
            if existing:
                self._update_task_memory(existing["id"], meeting_id, item, now)
                self._touch_task_meeting_metadata(existing["id"], meeting_meta)
                self._create_task_update(existing["id"], meeting_id, update_type, item, now)
                tasks_updated += 1
            else:
                task_id = self._create_task_memory(meeting_id, normalized_title, item, now, meeting_meta)
                self._create_task_update(task_id, meeting_id, "created", item, now)
                tasks_created += 1

        boss_messages = analysis.get("manager_summary", {}).get("boss_messages", [])
        for message in boss_messages:
            normalized_text = self._normalize_text(message)
            if not normalized_text:
                continue

            existing = self._find_requirement_memory(normalized_text)
            if existing:
                self._update_requirement_memory(existing["id"], meeting_id, message, now)
                self._create_requirement_update(existing["id"], meeting_id, "mentioned", message, now)
                requirements_updated += 1
            else:
                requirement_id = self._create_requirement_memory(meeting_id, normalized_text, message, now)
                self._create_requirement_update(requirement_id, meeting_id, "created", message, now)
                requirements_created += 1

        self.conn.commit()
        return {
            "tasks_created": tasks_created,
            "tasks_updated": tasks_updated,
            "requirements_created": requirements_created,
            "requirements_updated": requirements_updated,
        }

    def apply_task_progress_updates(self, meeting_id: int, updates: List[Dict]) -> Dict:
        """将会议中识别出的任务进展回写到任务总表。"""
        if not updates:
            return {"tasks_progressed": 0, "tasks_completed": 0, "tasks_blocked": 0}

        meeting_meta = self._get_meeting_meta(meeting_id)
        now = datetime.now().isoformat()
        progressed = 0
        completed = 0
        blocked = 0

        for item in updates:
            task_id = item.get("task_id")
            if not task_id:
                continue

            update_type = item.get("update_type", "progress")
            summary = item.get("summary", "")
            task = self.get_task_memory(task_id)
            if not task:
                continue

            new_status = {
                "completed": "completed",
                "blocked": "blocked",
                "progress": "in_progress",
                "reopened": "open",
            }.get(update_type, task.get("status", "open"))

            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE task_memory
                SET status = ?, last_seen_meeting_id = ?, last_seen_meeting_title = ?, last_seen_meeting_date = ?,
                    latest_summary = ?, updated_at = ?,
                    completed_in_meeting_id = CASE WHEN ? = 'completed' THEN ? ELSE completed_in_meeting_id END,
                    completed_in_meeting_title = CASE WHEN ? = 'completed' THEN ? ELSE completed_in_meeting_title END,
                    completed_in_meeting_date = CASE WHEN ? = 'completed' THEN ? ELSE completed_in_meeting_date END
                WHERE id = ?
            ''', (
                new_status,
                meeting_id,
                meeting_meta["title"],
                meeting_meta["date"],
                summary or task.get("latest_summary"),
                now,
                update_type,
                meeting_id,
                update_type,
                meeting_meta["title"],
                update_type,
                meeting_meta["date"],
                task_id,
            ))
            self._create_task_update(
                task_id,
                meeting_id,
                update_type,
                {
                    "task": summary or task.get("title"),
                    "owner": task.get("owner"),
                    "status": new_status,
                    "priority": task.get("priority"),
                    "deadline": task.get("deadline"),
                    "context": item.get("source_context"),
                },
                now,
            )

            if update_type == "completed":
                completed += 1
            elif update_type == "blocked":
                blocked += 1
            else:
                progressed += 1

        self.conn.commit()
        return {
            "tasks_progressed": progressed,
            "tasks_completed": completed,
            "tasks_blocked": blocked,
        }
    
    def get_meeting(self, meeting_id: int) -> Optional[Dict]:
        """获取会议详情"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        meeting = dict(row)
        
        # 获取议题
        cursor.execute('SELECT * FROM segments WHERE meeting_id = ? ORDER BY segment_id', (meeting_id,))
        meeting['segments'] = [dict(row) for row in cursor.fetchall()]
        
        # 获取待办事项
        cursor.execute('SELECT * FROM action_items WHERE meeting_id = ?', (meeting_id,))
        meeting['action_items'] = [dict(row) for row in cursor.fetchall()]
        
        # 获取发言人
        cursor.execute('SELECT * FROM speakers WHERE meeting_id = ?', (meeting_id,))
        meeting['speakers'] = [dict(row) for row in cursor.fetchall()]

        cursor.execute('SELECT * FROM participants WHERE meeting_id = ?', (meeting_id,))
        meeting['participants'] = [dict(row) for row in cursor.fetchall()]
        
        # 获取决策点
        cursor.execute('SELECT * FROM decisions WHERE meeting_id = ?', (meeting_id,))
        meeting['decisions'] = [dict(row) for row in cursor.fetchall()]
        
        return meeting
    
    def list_meetings(
        self,
        category: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """列出会议记录"""
        cursor = self.conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT * FROM meetings 
                WHERE category = ? 
                ORDER BY date DESC 
                LIMIT ? OFFSET ?
            ''', (category, limit, offset))
        else:
            cursor.execute('''
                SELECT * FROM meetings 
                ORDER BY date DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        return [dict(row) for row in cursor.fetchall()]

    def backfill_memory(self) -> Dict:
        """根据已有会议记录重建长期记忆层。"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM task_updates')
        cursor.execute('DELETE FROM task_memory')
        cursor.execute('DELETE FROM requirement_updates')
        cursor.execute('DELETE FROM requirement_memory')
        self.conn.commit()

        cursor.execute('SELECT id, manager_summary FROM meetings ORDER BY id ASC')
        meetings = [dict(row) for row in cursor.fetchall()]

        rebuilt_tasks = 0
        rebuilt_requirements = 0
        for meeting in meetings:
            meeting_id = meeting['id']

            cursor.execute('SELECT * FROM action_items WHERE meeting_id = ?', (meeting_id,))
            action_items = [dict(row) for row in cursor.fetchall()]

            manager_summary = {}
            raw_summary = meeting.get('manager_summary')
            if raw_summary:
                try:
                    manager_summary = json.loads(raw_summary)
                except json.JSONDecodeError:
                    manager_summary = {}

            result = self.sync_memory(
                meeting_id=meeting_id,
                analysis={"manager_summary": manager_summary},
                action_items=action_items,
            )
            rebuilt_tasks += result['tasks_created'] + result['tasks_updated']
            rebuilt_requirements += result['requirements_created'] + result['requirements_updated']

        return {
            "meetings_processed": len(meetings),
            "task_events": rebuilt_tasks,
            "requirement_events": rebuilt_requirements,
        }
    
    def search_meetings(self, keyword: str) -> List[Dict]:
        """搜索会议"""
        cursor = self.conn.cursor()
        keyword_pattern = f'%{keyword}%'
        
        cursor.execute('''
            SELECT DISTINCT m.* FROM meetings m
            LEFT JOIN segments s ON m.id = s.meeting_id
            LEFT JOIN action_items a ON m.id = a.meeting_id
            WHERE m.title LIKE ? 
               OR m.summary LIKE ?
               OR s.title LIKE ?
               OR s.summary LIKE ?
               OR a.task LIKE ?
            ORDER BY m.date DESC
        ''', (keyword_pattern, keyword_pattern, keyword_pattern, keyword_pattern, keyword_pattern))
        
        return [dict(row) for row in cursor.fetchall()]

    def get_meeting_by_session_id(self, session_id: str) -> Optional[Dict]:
        """按 session_id 获取会议。"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM meetings WHERE session_id = ? ORDER BY id DESC LIMIT 1', (session_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_meeting_by_session_id(self, session_id: str) -> int:
        """按 session_id 删除会议及关联数据。"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM meetings WHERE session_id = ?', (session_id,))
        meeting_ids = [row['id'] for row in cursor.fetchall()]

        if not meeting_ids:
            return 0

        for meeting_id in meeting_ids:
            cursor.execute('DELETE FROM segments WHERE meeting_id = ?', (meeting_id,))
            cursor.execute('DELETE FROM action_items WHERE meeting_id = ?', (meeting_id,))
            cursor.execute('DELETE FROM speakers WHERE meeting_id = ?', (meeting_id,))
            cursor.execute('DELETE FROM participants WHERE meeting_id = ?', (meeting_id,))
            cursor.execute('DELETE FROM decisions WHERE meeting_id = ?', (meeting_id,))
            cursor.execute('DELETE FROM keywords WHERE meeting_id = ?', (meeting_id,))
            cursor.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))

        self.conn.commit()
        return len(meeting_ids)
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # 总会议数
        cursor.execute('SELECT COUNT(*) as count FROM meetings')
        stats['total_meetings'] = cursor.fetchone()['count']
        
        # 总待办事项
        cursor.execute('SELECT COUNT(*) as count FROM action_items')
        stats['total_action_items'] = cursor.fetchone()['count']
        
        # 待办事项状态分布
        cursor.execute('SELECT status, COUNT(*) as count FROM action_items GROUP BY status')
        stats['action_items_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # 按分类统计
        cursor.execute('SELECT category, COUNT(*) as count FROM meetings GROUP BY category')
        stats['meetings_by_category'] = {row['category']: row['count'] for row in cursor.fetchall()}

        cursor.execute('SELECT COUNT(*) as count FROM task_memory')
        stats['memory_tasks'] = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM requirement_memory')
        stats['memory_requirements'] = cursor.fetchone()['count']
        
        return stats

    def list_task_memory(self, limit: int = 200) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM task_memory
            ORDER BY updated_at DESC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_task_memory(self, task_id: int) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM task_memory WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_task_updates(self, task_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT tu.*, m.title as meeting_title, m.date as meeting_date
            FROM task_updates tu
            LEFT JOIN meetings m ON tu.meeting_id = m.id
            WHERE tu.task_id = ?
            ORDER BY created_at DESC
        ''', (task_id,))
        return [dict(row) for row in cursor.fetchall()]

    def list_requirement_memory(self, limit: int = 200) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM requirement_memory
            ORDER BY updated_at DESC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def get_requirement_updates(self, requirement_id: int) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM requirement_updates
            WHERE requirement_id = ?
            ORDER BY created_at DESC
        ''', (requirement_id,))
        return [dict(row) for row in cursor.fetchall()]

    def _find_task_memory(self, normalized_title: str, owner: str = None):
        cursor = self.conn.cursor()
        if owner and owner != '待分配':
            cursor.execute('''
                SELECT * FROM task_memory
                WHERE normalized_title = ? AND (owner = ? OR owner IS NULL OR owner = '')
                ORDER BY updated_at DESC
                LIMIT 1
            ''', (normalized_title, owner))
            row = cursor.fetchone()
            if row:
                return dict(row)

        cursor.execute('''
            SELECT * FROM task_memory
            WHERE normalized_title = ?
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (normalized_title,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def _create_task_memory(self, meeting_id: int, normalized_title: str, item: Dict, now: str, meeting_meta: Dict) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO task_memory (
                normalized_title, title, owner, status, priority, deadline, project_name,
                created_from_meeting_id, created_from_meeting_title, created_from_meeting_date,
                last_seen_meeting_id, last_seen_meeting_title, last_seen_meeting_date,
                occurrence_count, latest_summary, latest_context, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            normalized_title,
            item.get('task', ''),
            item.get('owner'),
            self._map_task_status(item.get('status')),
            item.get('priority'),
            item.get('deadline'),
            item.get('project_name'),
            meeting_id,
            meeting_meta["title"],
            meeting_meta["date"],
            meeting_id,
            meeting_meta["title"],
            meeting_meta["date"],
            1,
            item.get('task', ''),
            item.get('context'),
            now,
            now,
        ))
        return cursor.lastrowid

    def _update_task_memory(self, task_id: int, meeting_id: int, item: Dict, now: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE task_memory
            SET title = ?, owner = COALESCE(?, owner), status = ?, priority = COALESCE(?, priority),
                deadline = COALESCE(?, deadline), last_seen_meeting_id = ?, occurrence_count = occurrence_count + 1,
                latest_summary = ?, latest_context = ?, updated_at = ?
            WHERE id = ?
        ''', (
            item.get('task', ''),
            item.get('owner'),
            self._map_task_status(item.get('status')),
            item.get('priority'),
            item.get('deadline'),
            meeting_id,
            item.get('task', ''),
            item.get('context'),
            now,
            task_id,
        ))
        if self._map_task_status(item.get('status')) == 'completed':
            meeting_meta = self._get_meeting_meta(meeting_id)
            cursor.execute('''
                UPDATE task_memory
                SET completed_in_meeting_id = ?, completed_in_meeting_title = ?, completed_in_meeting_date = ?
                WHERE id = ?
            ''', (
                meeting_id,
                meeting_meta["title"],
                meeting_meta["date"],
                task_id,
            ))

    def _touch_task_meeting_metadata(self, task_id: int, meeting_meta: Dict):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE task_memory
            SET last_seen_meeting_title = ?, last_seen_meeting_date = ?, updated_at = ?
            WHERE id = ?
        ''', (
            meeting_meta["title"],
            meeting_meta["date"],
            datetime.now().isoformat(),
            task_id,
        ))

    def _create_task_update(self, task_id: int, meeting_id: int, update_type: str, item: Dict, now: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO task_updates (
                task_id, meeting_id, update_type, summary, owner, status, priority, deadline, source_context, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_id,
            meeting_id,
            update_type,
            item.get('task', ''),
            item.get('owner'),
            self._map_task_status(item.get('status')),
            item.get('priority'),
            item.get('deadline'),
            item.get('context'),
            now,
        ))

    def _find_requirement_memory(self, normalized_text: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM requirement_memory
            WHERE normalized_text = ?
            ORDER BY updated_at DESC
            LIMIT 1
        ''', (normalized_text,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def _create_requirement_memory(self, meeting_id: int, normalized_text: str, text: str, now: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO requirement_memory (
                normalized_text, requirement_text, source_type, status, first_meeting_id, last_seen_meeting_id,
                occurrence_count, latest_summary, created_at, updated_at
            ) VALUES (?, ?, 'boss_message', 'active', ?, ?, 1, ?, ?, ?)
        ''', (
            normalized_text,
            text,
            meeting_id,
            meeting_id,
            text,
            now,
            now,
        ))
        return cursor.lastrowid

    def _update_requirement_memory(self, requirement_id: int, meeting_id: int, text: str, now: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE requirement_memory
            SET requirement_text = ?, last_seen_meeting_id = ?, occurrence_count = occurrence_count + 1,
                latest_summary = ?, updated_at = ?
            WHERE id = ?
        ''', (
            text,
            meeting_id,
            text,
            now,
            requirement_id,
        ))

    def _create_requirement_update(self, requirement_id: int, meeting_id: int, update_type: str, summary: str, now: str):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO requirement_updates (
                requirement_id, meeting_id, update_type, summary, created_at
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            requirement_id,
            meeting_id,
            update_type,
            summary,
            now,
        ))

    def _normalize_text(self, text: str) -> str:
        normalized = ''.join(str(text or '').strip().lower().split())
        return normalized[:255]

    def _map_task_status(self, status: str = None) -> str:
        value = (status or '').strip()
        if value in {'已完成', '完成', 'done', 'completed'}:
            return 'completed'
        if value in {'进行中', '处理中', 'in_progress'}:
            return 'in_progress'
        if value in {'阻塞', 'blocked'}:
            return 'blocked'
        return 'open'

    def _classify_task_update(self, item: Dict) -> str:
        status = self._map_task_status(item.get('status'))
        if status == 'completed':
            return 'completed'
        if status == 'blocked':
            return 'blocked'
        if status == 'in_progress':
            return 'progress'
        return 'mentioned'

    def _get_meeting_meta(self, meeting_id: int) -> Dict:
        cursor = self.conn.cursor()
        cursor.execute('SELECT title, date FROM meetings WHERE id = ?', (meeting_id,))
        row = cursor.fetchone()
        if not row:
            return {"title": "", "date": ""}
        return {"title": row["title"], "date": row["date"]}
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
