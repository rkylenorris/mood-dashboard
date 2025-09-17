import logging
import sqlite3
from datetime import datetime
from logging import Handler, LogRecord


class SQLiteHandler(Handler):
    def __init__(self, db_path='etl_logs.db'):
        super().__init__()
        self.conn = sqlite3.connect(db_path)
        self._ensure_table()

    def _ensure_table(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created TEXT,
                level TEXT,
                message TEXT,
                pathname TEXT,
                lineno INTEGER,
                funcname TEXT
            )
        ''')
        self.conn.commit()

    def emit(self, record: LogRecord):
        try:
            # only gets message, not full metadata unless included in formatter
            msg = self.format(record)
            self.conn.execute('''
                INSERT INTO logs (created, level, message, pathname, lineno, funcname)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.fromtimestamp(record.created).isoformat(),
                record.levelname,
                record.getMessage(),
                record.pathname,
                record.lineno,
                record.funcName
            ))
            self.conn.commit()
        except Exception:
            self.handleError(record)


def setup_logger(name="daylio_dashboard", db_path='daylio_dashboard_logs.db'):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()  # Avoid duplicates on reruns in Streamlit

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(filename)s: %(message)s'))

    # SQLite Handler
    sqlite_handler = SQLiteHandler(db_path=db_path)
    sqlite_handler.setFormatter(logging.Formatter(
        '%(message)s'))  # Store only the message in DB

    logger.addHandler(console_handler)
    logger.addHandler(sqlite_handler)

    return logger
