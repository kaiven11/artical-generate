"""
Database configuration and session management.
"""

import sqlite3
import os
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# SQLAlchemy setup
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # For SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Simple database connection for legacy code
def get_db_connection():
    """Get SQLite database connection with timeout and retry."""
    # Ensure data directory exists
    db_path = settings.database_url.replace("sqlite:///", "")
    db_dir = os.path.dirname(db_path)
    if db_dir:
        Path(db_dir).mkdir(parents=True, exist_ok=True)

    # Add timeout and other connection parameters to handle locking
    conn = sqlite3.connect(
        db_path,
        timeout=30.0,  # 30 second timeout
        check_same_thread=False,
        isolation_level=None  # Enable autocommit mode
    )
    conn.row_factory = sqlite3.Row  # Enable dict-like access

    # Configure SQLite for better concurrency
    conn.execute("PRAGMA busy_timeout=30000")  # 30 second busy timeout
    conn.execute("PRAGMA journal_mode=DELETE")  # Use DELETE mode instead of WAL
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=1000")
    conn.execute("PRAGMA temp_store=memory")

    return conn

def get_db():
    """Get SQLAlchemy database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Create basic tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                source_url TEXT NOT NULL UNIQUE,
                source_platform TEXT NOT NULL,
                author TEXT,
                publish_date DATETIME,
                content_original TEXT NOT NULL,
                content_translated TEXT,
                content_optimized TEXT,
                content_final TEXT,
                status TEXT DEFAULT 'pending',
                ai_detection_score REAL,
                quality_score REAL,
                processing_attempts INTEGER DEFAULT 0,
                last_error TEXT,
                word_count INTEGER,
                estimated_reading_time INTEGER,
                tags TEXT,
                category TEXT,
                url_hash TEXT,
                content_hash TEXT,
                published_url TEXT,
                published_platform TEXT,
                published_at DATETIME,
                creation_type TEXT DEFAULT 'url_import',
                topic TEXT,
                keywords TEXT,
                selected_creation_prompt_id INTEGER,
                selected_model_id INTEGER,
                creation_requirements TEXT,
                is_featured BOOLEAN DEFAULT 0,
                is_archived BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Add missing columns if they don't exist (for existing databases)
        missing_columns = [
            ('author', 'TEXT'),
            ('publish_date', 'DATETIME'),
            ('ai_detection_score', 'REAL'),
            ('quality_score', 'REAL'),
            ('processing_attempts', 'INTEGER DEFAULT 0'),
            ('last_error', 'TEXT'),
            ('word_count', 'INTEGER'),
            ('estimated_reading_time', 'INTEGER'),
            ('tags', 'TEXT'),
            ('category', 'TEXT'),
            ('url_hash', 'TEXT'),
            ('content_hash', 'TEXT'),
            ('published_url', 'TEXT'),
            ('published_platform', 'TEXT'),
            ('published_at', 'DATETIME'),
            ('is_featured', 'BOOLEAN DEFAULT 0'),
            ('is_archived', 'BOOLEAN DEFAULT 0'),
            ('target_length', 'TEXT DEFAULT "medium"'),  # 添加目标长度字段
            ('writing_style', 'TEXT')  # 添加写作风格字段
        ]

        for column_name, column_type in missing_columns:
            try:
                cursor.execute(f'ALTER TABLE articles ADD COLUMN {column_name} {column_type}')
                logger.info(f"Added missing column: {column_name}")
            except Exception as e:
                # Column already exists or other error
                if "duplicate column name" not in str(e).lower():
                    logger.debug(f"Could not add column {column_name}: {e}")
                pass

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompt_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                type TEXT NOT NULL,
                template TEXT NOT NULL,
                variables TEXT,
                version TEXT DEFAULT '1.0',
                language TEXT DEFAULT 'zh-CN',
                success_rate REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                average_quality_score REAL DEFAULT 0.0,
                parameters TEXT,
                is_active BOOLEAN DEFAULT 1,
                is_default BOOLEAN DEFAULT 0,
                priority INTEGER DEFAULT 0,
                test_group TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used_at DATETIME,
                created_by TEXT DEFAULT 'system'
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detection_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                detection_type TEXT NOT NULL,
                platform TEXT NOT NULL,
                score REAL,
                is_passed BOOLEAN NOT NULL,
                detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                progress REAL DEFAULT 0.0,
                article_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                started_at DATETIME,
                completed_at DATETIME,
                current_step TEXT DEFAULT 'pending',
                FOREIGN KEY (article_id) REFERENCES articles (id)
            )
        ''')

        # Create API configuration tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                description TEXT,
                provider_type TEXT NOT NULL,
                api_key TEXT NOT NULL,
                api_url TEXT NOT NULL,
                api_version TEXT,
                is_enabled BOOLEAN DEFAULT 1,
                is_default BOOLEAN DEFAULT 0,
                weight INTEGER DEFAULT 1,
                max_requests_per_minute INTEGER DEFAULT 60,
                max_requests_per_hour INTEGER DEFAULT 1000,
                max_concurrent_requests INTEGER DEFAULT 5,
                cost_per_1k_tokens_input REAL DEFAULT 0.0,
                cost_per_1k_tokens_output REAL DEFAULT 0.0,
                monthly_budget REAL DEFAULT 0.0,
                extra_config TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                display_name TEXT NOT NULL,
                model_type TEXT DEFAULT 'text',
                max_tokens INTEGER DEFAULT 4096,
                temperature REAL DEFAULT 0.7,
                top_p REAL DEFAULT 0.9,
                frequency_penalty REAL DEFAULT 0.0,
                presence_penalty REAL DEFAULT 0.0,
                timeout_seconds INTEGER DEFAULT 30,
                use_cases TEXT,
                is_enabled BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (provider_id) REFERENCES api_providers (id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                description TEXT,
                config_type TEXT DEFAULT 'string',
                is_encrypted BOOLEAN DEFAULT 0,
                is_system BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Run migrations to add missing columns
        migrate_database(conn)

        conn.commit()
        conn.close()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


def migrate_database(conn):
    """Apply database migrations to add missing columns."""
    cursor = conn.cursor()

    try:
        # Migrate tasks table
        cursor.execute("PRAGMA table_info(tasks)")
        task_columns = [column[1] for column in cursor.fetchall()]

        # Add missing columns to tasks table if they don't exist
        if 'progress' not in task_columns:
            logger.info("Adding progress column to tasks table")
            cursor.execute("ALTER TABLE tasks ADD COLUMN progress REAL DEFAULT 0.0")

        if 'started_at' not in task_columns:
            logger.info("Adding started_at column to tasks table")
            cursor.execute("ALTER TABLE tasks ADD COLUMN started_at DATETIME")

        if 'completed_at' not in task_columns:
            logger.info("Adding completed_at column to tasks table")
            cursor.execute("ALTER TABLE tasks ADD COLUMN completed_at DATETIME")

        if 'current_step' not in task_columns:
            logger.info("Adding current_step column to tasks table")
            cursor.execute("ALTER TABLE tasks ADD COLUMN current_step TEXT DEFAULT 'pending'")

        # Migrate detection_results table
        cursor.execute("PRAGMA table_info(detection_results)")
        detection_columns = [column[1] for column in cursor.fetchall()]

        # Add missing columns to detection_results table if they don't exist
        if 'detected_at' not in detection_columns:
            logger.info("Adding detected_at column to detection_results table")
            cursor.execute("ALTER TABLE detection_results ADD COLUMN detected_at DATETIME DEFAULT CURRENT_TIMESTAMP")

        # Migrate articles table
        cursor.execute("PRAGMA table_info(articles)")
        article_columns = [column[1] for column in cursor.fetchall()]

        # Add missing columns to articles table if they don't exist
        if 'author' not in article_columns:
            logger.info("Adding author column to articles table")
            cursor.execute("ALTER TABLE articles ADD COLUMN author TEXT")

        if 'word_count' not in article_columns:
            logger.info("Adding word_count column to articles table")
            cursor.execute("ALTER TABLE articles ADD COLUMN word_count INTEGER")

        if 'estimated_reading_time' not in article_columns:
            logger.info("Adding estimated_reading_time column to articles table")
            cursor.execute("ALTER TABLE articles ADD COLUMN estimated_reading_time INTEGER")

        if 'publish_date' not in article_columns:
            logger.info("Adding publish_date column to articles table")
            cursor.execute("ALTER TABLE articles ADD COLUMN publish_date DATETIME")

        if 'url_hash' not in article_columns:
            logger.info("Adding url_hash column to articles table")
            cursor.execute("ALTER TABLE articles ADD COLUMN url_hash TEXT")

        # Migrate prompt_templates table
        cursor.execute("PRAGMA table_info(prompt_templates)")
        prompt_columns = [column[1] for column in cursor.fetchall()]

        # Add missing columns to prompt_templates table
        new_prompt_columns = [
            ('display_name', 'TEXT NOT NULL DEFAULT ""'),
            ('description', 'TEXT'),
            ('variables', 'TEXT'),
            ('version', 'TEXT DEFAULT "1.0"'),
            ('language', 'TEXT DEFAULT "zh-CN"'),
            ('success_rate', 'REAL DEFAULT 0.0'),
            ('usage_count', 'INTEGER DEFAULT 0'),
            ('average_quality_score', 'REAL DEFAULT 0.0'),
            ('parameters', 'TEXT'),
            ('is_default', 'BOOLEAN DEFAULT 0'),
            ('priority', 'INTEGER DEFAULT 0'),
            ('test_group', 'TEXT'),
            ('updated_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP'),
            ('last_used_at', 'DATETIME'),
            ('created_by', 'TEXT DEFAULT "system"')
        ]

        for column_name, column_def in new_prompt_columns:
            if column_name not in prompt_columns:
                logger.info(f"Adding {column_name} column to prompt_templates table")
                cursor.execute(f"ALTER TABLE prompt_templates ADD COLUMN {column_name} {column_def}")

        # Update display_name for existing records if empty
        cursor.execute("UPDATE prompt_templates SET display_name = name WHERE display_name = '' OR display_name IS NULL")

        logger.info("Database migration completed successfully")

    except Exception as e:
        logger.error(f"Failed to migrate database: {e}")
        # Don't raise here as this might be expected for new databases


def drop_tables():
    """Drop all database tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS tasks")
        cursor.execute("DROP TABLE IF EXISTS detection_results")
        cursor.execute("DROP TABLE IF EXISTS prompt_templates")
        cursor.execute("DROP TABLE IF EXISTS articles")

        conn.commit()
        conn.close()
        logger.info("Database tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise


def init_db():
    """Initialize database with tables and default data."""
    try:
        create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


class DatabaseManager:
    """Database management utilities."""
    
    @staticmethod
    def backup_database(backup_path: str) -> bool:
        """
        Backup database to specified path.
        
        Args:
            backup_path: Path to save backup file
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            import shutil
            import os
            
            # Extract database file path from URL
            db_path = settings.database_url.replace("sqlite:///", "")
            
            if os.path.exists(db_path):
                shutil.copy2(db_path, backup_path)
                logger.info(f"Database backed up to {backup_path}")
                return True
            else:
                logger.warning(f"Database file not found: {db_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return False
    
    @staticmethod
    def restore_database(backup_path: str) -> bool:
        """
        Restore database from backup file.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            bool: True if restore successful, False otherwise
        """
        try:
            import shutil
            import os
            
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Extract database file path from URL
            db_path = settings.database_url.replace("sqlite:///", "")
            
            # Close all connections before restore
            # Note: No engine to dispose in simplified version
            
            # Restore backup
            shutil.copy2(backup_path, db_path)
            logger.info(f"Database restored from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False
    
    @staticmethod
    def get_database_info() -> dict:
        """
        Get database information.
        
        Returns:
            dict: Database information
        """
        try:
            import os
            
            db_path = settings.database_url.replace("sqlite:///", "")
            
            if os.path.exists(db_path):
                stat = os.stat(db_path)
                return {
                    "path": db_path,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "exists": True
                }
            else:
                return {
                    "path": db_path,
                    "exists": False
                }
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}


# Mock async session for compatibility
class AsyncSession:
    """Mock async session for compatibility with async code."""

    def __init__(self):
        self.conn = None

    async def __aenter__(self):
        self.conn = get_db_connection()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def execute(self, query, params=None):
        """Execute a query."""
        if params:
            return self.conn.execute(query, params)
        return self.conn.execute(query)

    def commit(self):
        """Commit transaction."""
        self.conn.commit()

    def rollback(self):
        """Rollback transaction."""
        self.conn.rollback()

    def merge(self, obj):
        """Mock merge method for compatibility."""
        # For SQLite, we don't need to do anything special for merge
        # This is just for compatibility with SQLAlchemy-style code
        return obj

    def query(self, model):
        """Mock query method for compatibility."""
        # This is a placeholder - actual implementation would depend on the model
        return None


def get_db_session():
    """Get async database session for compatibility."""
    return AsyncSession()


# Global database manager instance
db_manager = DatabaseManager()
