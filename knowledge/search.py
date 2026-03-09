"""
会议搜索引擎
提供全文搜索和语义搜索功能
"""

import sqlite3
from pathlib import Path
from typing import List, Dict
from .database import MeetingDatabase


class MeetingSearchEngine:
    """会议搜索引擎"""
    
    def __init__(self, db: MeetingDatabase):
        """
        初始化搜索引擎
        
        Args:
            db: 数据库实例
        """
        self.db = db
    
    def search(
        self,
        query: str,
        search_type: str = "full_text",
        filters: Dict = None
    ) -> List[Dict]:
        """
        搜索会议
        
        Args:
            query: 搜索关键词
            search_type: 搜索类型（full_text/semantic）
            filters: 过滤条件（category, date_from, date_to等）
        
        Returns:
            搜索结果列表
        """
        if search_type == "full_text":
            return self._full_text_search(query, filters)
        elif search_type == "semantic":
            return self._semantic_search(query, filters)
        else:
            raise ValueError(f"不支持的搜索类型: {search_type}")
    
    def _full_text_search(self, query: str, filters: Dict = None) -> List[Dict]:
        """全文搜索"""
        cursor = self.db.conn.cursor()
        keyword_pattern = f'%{query}%'
        
        # 构建基础查询
        sql = '''
            SELECT DISTINCT 
                m.*,
                GROUP_CONCAT(DISTINCT s.title) as segment_titles,
                GROUP_CONCAT(DISTINCT a.task) as action_tasks
            FROM meetings m
            LEFT JOIN segments s ON m.id = s.meeting_id
            LEFT JOIN action_items a ON m.id = a.meeting_id
            WHERE (
                m.title LIKE ? 
                OR m.summary LIKE ?
                OR s.title LIKE ?
                OR s.summary LIKE ?
                OR s.transcript LIKE ?
                OR a.task LIKE ?
            )
        '''
        
        params = [keyword_pattern] * 6
        
        # 添加过滤条件
        if filters:
            if filters.get('category'):
                sql += ' AND m.category = ?'
                params.append(filters['category'])
            
            if filters.get('date_from'):
                sql += ' AND m.date >= ?'
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                sql += ' AND m.date <= ?'
                params.append(filters['date_to'])
        
        sql += ' GROUP BY m.id ORDER BY m.date DESC'
        
        cursor.execute(sql, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # 为每个结果添加匹配详情
        for result in results:
            result['match_details'] = self._get_match_details(result['id'], query)
        
        return results
    
    def _semantic_search(self, query: str, filters: Dict = None) -> List[Dict]:
        """
        语义搜索（简化版）
        使用关键词匹配和相关性评分
        """
        # 简化实现：使用全文搜索 + 相关性评分
        results = self._full_text_search(query, filters)
        
        # 计算相关性评分
        for result in results:
            score = 0
            query_lower = query.lower()
            
            # 标题匹配权重最高
            if query_lower in result.get('title', '').lower():
                score += 10
            
            # 摘要匹配
            if query_lower in result.get('summary', '').lower():
                score += 5
            
            # 议题匹配
            if result.get('segment_titles') and query_lower in result['segment_titles'].lower():
                score += 3
            
            # 待办事项匹配
            if result.get('action_tasks') and query_lower in result['action_tasks'].lower():
                score += 2
            
            result['relevance_score'] = score
        
        # 按相关性排序
        results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return results
    
    def _get_match_details(self, meeting_id: int, query: str) -> Dict:
        """获取匹配详情"""
        cursor = self.db.conn.cursor()
        query_lower = query.lower()
        
        details = {
            'matched_segments': [],
            'matched_actions': [],
            'match_count': 0
        }
        
        # 查找匹配的议题
        cursor.execute('''
            SELECT segment_id, title, summary 
            FROM segments 
            WHERE meeting_id = ? 
            AND (title LIKE ? OR summary LIKE ? OR transcript LIKE ?)
        ''', (meeting_id, f'%{query}%', f'%{query}%', f'%{query}%'))
        
        for row in cursor.fetchall():
            details['matched_segments'].append({
                'segment_id': row['segment_id'],
                'title': row['title'],
                'summary': row['summary']
            })
            details['match_count'] += 1
        
        # 查找匹配的待办事项
        cursor.execute('''
            SELECT task, owner 
            FROM action_items 
            WHERE meeting_id = ? 
            AND task LIKE ?
        ''', (meeting_id, f'%{query}%'))
        
        for row in cursor.fetchall():
            details['matched_actions'].append({
                'task': row['task'],
                'owner': row['owner']
            })
            details['match_count'] += 1
        
        return details
    
    def search_by_date_range(
        self,
        date_from: str,
        date_to: str,
        category: str = None
    ) -> List[Dict]:
        """按日期范围搜索"""
        cursor = self.db.conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT * FROM meetings 
                WHERE date >= ? AND date <= ? AND category = ?
                ORDER BY date DESC
            ''', (date_from, date_to, category))
        else:
            cursor.execute('''
                SELECT * FROM meetings 
                WHERE date >= ? AND date <= ?
                ORDER BY date DESC
            ''', (date_from, date_to))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_action_items(
        self,
        owner: str = None,
        status: str = None,
        priority: str = None
    ) -> List[Dict]:
        """搜索待办事项"""
        cursor = self.db.conn.cursor()
        
        sql = '''
            SELECT a.*, m.title as meeting_title, m.date as meeting_date
            FROM action_items a
            JOIN meetings m ON a.meeting_id = m.id
            WHERE 1=1
        '''
        params = []
        
        if owner:
            sql += ' AND a.owner LIKE ?'
            params.append(f'%{owner}%')
        
        if status:
            sql += ' AND a.status = ?'
            params.append(status)
        
        if priority:
            sql += ' AND a.priority = ?'
            params.append(priority)
        
        sql += ' ORDER BY a.created_at DESC'
        
        cursor.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_related_meetings(self, meeting_id: int, limit: int = 5) -> List[Dict]:
        """
        获取相关会议
        基于分类和关键词相似度
        """
        cursor = self.db.conn.cursor()
        
        # 获取当前会议信息
        cursor.execute('SELECT category, summary FROM meetings WHERE id = ?', (meeting_id,))
        current = cursor.fetchone()
        
        if not current:
            return []
        
        # 查找同类别的其他会议
        cursor.execute('''
            SELECT * FROM meetings 
            WHERE category = ? AND id != ?
            ORDER BY date DESC
            LIMIT ?
        ''', (current['category'], meeting_id, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_trending_topics(self, days: int = 30) -> List[Dict]:
        """
        获取热门话题
        基于最近N天的会议关键词
        """
        cursor = self.db.conn.cursor()
        
        # 简化实现：统计最近会议的分类分布
        cursor.execute('''
            SELECT 
                category,
                COUNT(*) as count,
                GROUP_CONCAT(title, '; ') as titles
            FROM meetings
            WHERE date >= date('now', '-' || ? || ' days')
            GROUP BY category
            ORDER BY count DESC
        ''', (days,))
        
        return [dict(row) for row in cursor.fetchall()]
