"""Database connection and utilities"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, List, Dict, Any
import logging
from src.config import Config

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    def __init__(self, connection_string: Optional[str] = None):
        self.connection_string = connection_string or Config.DATABASE_URL
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(self.connection_string)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    @contextmanager
    def get_cursor(self, dict_cursor: bool = False):
        """Context manager for database cursor"""
        with self.get_connection() as conn:
            cursor_factory = RealDictCursor if dict_cursor else None
            cur = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cur
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cur.close()
    
    def execute(self, query: str, params: Optional[tuple] = None) -> None:
        """Execute a query without returning results"""
        with self.get_cursor() as cur:
            cur.execute(query, params)
    
    def fetchone(self, query: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """Fetch a single row"""
        with self.get_cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()
    
    def fetchall(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Fetch all rows"""
        with self.get_cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    
    def fetch_dict(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Fetch all rows as dictionaries"""
        with self.get_cursor(dict_cursor=True) as cur:
            cur.execute(query, params)
            return cur.fetchall()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            result = self.fetchone("SELECT 1")
            logger.info("Database connection successful")
            return result is not None
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def get_table_counts(self) -> Dict[str, int]:
        """Get row counts for all tables"""
        tables = ['teams', 'players', 'games', 'bets', 'communities']
        counts = {}
        
        for table in tables:
            try:
                result = self.fetchone(f"SELECT COUNT(*) FROM {table}")
                counts[table] = result[0] if result else 0
            except:
                counts[table] = -1
                
        return counts


# Create global database instance
db = Database()