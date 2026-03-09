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
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_date ON meetings(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_meetings_category ON meetings(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)')
        
        self.conn.commit()
    
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
        duration: float = None
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
            INSERT INTO meetings (title, date, duration, category, summary, video_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title,
            date,
            duration,
            analysis.get('category'),
            analysis.get('summary'),
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
        
        return stats
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
