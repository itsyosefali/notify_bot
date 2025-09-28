import pymysql
import os
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

class Database:
    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', 'sqlite:///exams.db')
        self.init_database()
    
    def get_connection(self):
        """Get database connection based on URL"""
        if self.database_url.startswith('mysql://') or self.database_url.startswith('mariadb://'):
            # Parse MySQL/MariaDB URL
            parsed = urlparse(self.database_url)
            return pymysql.connect(
                host=parsed.hostname,
                port=parsed.port or 3306,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],  # Remove leading slash
                charset='utf8mb4'
            )
        else:
            # Fallback to SQLite for local development
            import sqlite3
            db_path = self.database_url.replace('sqlite:///', '')
            return sqlite3.connect(db_path)
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.database_url.startswith('mysql://') or self.database_url.startswith('mariadb://'):
            # MySQL/MariaDB schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exams (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    chat_id BIGINT NOT NULL,
                    exam_date DATE NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_group_exam BOOLEAN DEFAULT FALSE
                )
            ''')
        else:
            # SQLite schema
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    exam_date TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_group_exam BOOLEAN DEFAULT FALSE
                )
            ''')
        
        conn.commit()
        conn.close()
    
    def add_exam(self, user_id: int, chat_id: int, exam_date: str, title: str, 
                 description: str = "", is_group_exam: bool = False) -> int:
        """Add a new exam to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.database_url.startswith('mysql://') or self.database_url.startswith('mariadb://'):
            cursor.execute('''
                INSERT INTO exams (user_id, chat_id, exam_date, title, description, is_group_exam)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (user_id, chat_id, exam_date, title, description, is_group_exam))
            exam_id = cursor.lastrowid
        else:
            cursor.execute('''
                INSERT INTO exams (user_id, chat_id, exam_date, title, description, is_group_exam)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, chat_id, exam_date, title, description, is_group_exam))
            exam_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        
        return exam_id
    
    def get_exams_for_user(self, user_id: int, chat_id: int) -> List[Dict]:
        """Get all exams for a specific user in a specific chat"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.database_url.startswith('mysql://') or self.database_url.startswith('mariadb://'):
            cursor.execute('''
                SELECT id, exam_date, title, description, is_group_exam
                FROM exams 
                WHERE user_id = %s AND chat_id = %s
                ORDER BY exam_date ASC
            ''', (user_id, chat_id))
        else:
            cursor.execute('''
                SELECT id, exam_date, title, description, is_group_exam
                FROM exams 
                WHERE user_id = ? AND chat_id = ?
                ORDER BY exam_date ASC
            ''', (user_id, chat_id))
        
        exams = []
        for row in cursor.fetchall():
            exams.append({
                'id': row[0],
                'exam_date': row[1],
                'title': row[2],
                'description': row[3],
                'is_group_exam': bool(row[4])
            })
        
        conn.close()
        return exams
    
    def get_exams_for_group(self, chat_id: int) -> List[Dict]:
        """Get all group exams for a specific chat"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.database_url.startswith('mysql://') or self.database_url.startswith('mariadb://'):
            cursor.execute('''
                SELECT id, exam_date, title, description, user_id
                FROM exams 
                WHERE chat_id = %s AND is_group_exam = TRUE
                ORDER BY exam_date ASC
            ''', (chat_id,))
        else:
            cursor.execute('''
                SELECT id, exam_date, title, description, user_id
                FROM exams 
                WHERE chat_id = ? AND is_group_exam = TRUE
                ORDER BY exam_date ASC
            ''', (chat_id,))
        
        exams = []
        for row in cursor.fetchall():
            exams.append({
                'id': row[0],
                'exam_date': row[1],
                'title': row[2],
                'description': row[3],
                'user_id': row[4]
            })
        
        conn.close()
        return exams
    
    def get_exams_for_notification(self, days_ahead: int = 1) -> List[Dict]:
        """Get exams that need notification (1 day ahead by default)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Calculate target date
        from datetime import datetime, timedelta
        target_date = (datetime.now() + timedelta(days=days_ahead)).strftime('%Y-%m-%d')
        
        if self.database_url.startswith('mysql://') or self.database_url.startswith('mariadb://'):
            cursor.execute('''
                SELECT id, user_id, chat_id, exam_date, title, description, is_group_exam
                FROM exams 
                WHERE exam_date = %s
            ''', (target_date,))
        else:
            cursor.execute('''
                SELECT id, user_id, chat_id, exam_date, title, description, is_group_exam
                FROM exams 
                WHERE exam_date = ?
            ''', (target_date,))
        
        exams = []
        for row in cursor.fetchall():
            exams.append({
                'id': row[0],
                'user_id': row[1],
                'chat_id': row[2],
                'exam_date': row[3],
                'title': row[4],
                'description': row[5],
                'is_group_exam': bool(row[6])
            })
        
        conn.close()
        return exams
    
    def remove_exam(self, exam_id: int, user_id: int) -> bool:
        """Remove an exam (only if user owns it)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.database_url.startswith('mysql://') or self.database_url.startswith('mariadb://'):
            cursor.execute('''
                DELETE FROM exams 
                WHERE id = %s AND user_id = %s
            ''', (exam_id, user_id))
        else:
            cursor.execute('''
                DELETE FROM exams 
                WHERE id = ? AND user_id = ?
            ''', (exam_id, user_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_exam_by_id(self, exam_id: int) -> Optional[Dict]:
        """Get exam details by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if self.database_url.startswith('mysql://') or self.database_url.startswith('mariadb://'):
            cursor.execute('''
                SELECT id, user_id, chat_id, exam_date, title, description, is_group_exam
                FROM exams 
                WHERE id = %s
            ''', (exam_id,))
        else:
            cursor.execute('''
                SELECT id, user_id, chat_id, exam_date, title, description, is_group_exam
                FROM exams 
                WHERE id = ?
            ''', (exam_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'user_id': row[1],
                'chat_id': row[2],
                'exam_date': row[3],
                'title': row[4],
                'description': row[5],
                'is_group_exam': bool(row[6])
            }
        return None
