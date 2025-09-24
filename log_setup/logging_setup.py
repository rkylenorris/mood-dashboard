from __future__ import annotations
import os
import queue
import atexit
import logging
import sqlite3
import threading

from datetime import datetime
from dotenv import load_dotenv

from logging.handlers import QueueHandler, QueueListener

# log_setup/logging_setup.py

load_dotenv()

# --- Config ---
LOG_DB_PATH = os.getenv("DB_PATH", None)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

if (not LOG_DB_PATH) or (not LOG_LEVEL):
    raise ValueError(
        "Both DB_PATH and LOG_LEVEL environment variables must be set")

# --- SQLite writer that lives on ONE thread ---


class _SQLiteWriter:
    def __init__(self, db_path: str):
        # One connection, owned by the listener thread
        self.conn = sqlite3.connect(
            db_path,
            check_same_thread=False,  # allow single conn in this thread
            isolation_level=None,     # autocommit
        )
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA busy_timeout=3000;")
        self._ensure_table()
        self._lock = threading.Lock()

    def _ensure_table(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY,
                created_at TEXT NOT NULL,
                level TEXT NOT NULL,
                logger TEXT NOT NULL,
                message TEXT,
                pathname TEXT,
                lineno INTEGER,
                funcName TEXT,
                process INTEGER,
                thread INTEGER
            )
            """
        )

    def write(self, record: logging.LogRecord):
        # serialize writes just to be extra safe
        with self._lock:
            self.conn.execute(
                """
                INSERT INTO logs (
                    created_at, level, logger, message, pathname, lineno, funcName, process, thread
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.utcfromtimestamp(
                        record.created).isoformat() + "Z",
                    record.levelname,
                    record.name,
                    record.getMessage(),
                    getattr(record, "pathname", None),
                    getattr(record, "lineno", None),
                    getattr(record, "funcName", None),
                    getattr(record, "process", None),
                    getattr(record, "thread", None),
                ),
            )

    def close(self):
        with self._lock:
            try:
                self.conn.close()
            except Exception:
                pass


# --- A small handler that the QueueListener calls to perform the DB write ---
class _SQLiteTargetHandler(logging.Handler):
    def __init__(self, writer: _SQLiteWriter):
        super().__init__()
        self.writer = writer

    def emit(self, record: logging.LogRecord):
        try:
            self.writer.write(record)
        except Exception:
            # Don't break logging on DB issues
            self.handleError(record)


# --- Singleton state to survive Streamlit reruns ---
_queue = None
_listener = None
_sql_writer = None
_configured = False


def _ensure_logging_backend():
    global _queue, _listener, _sql_writer, _configured
    if _configured:
        return

    # Set up the shared queue and writer/listener once
    _queue = queue.Queue(-1)
    _sql_writer = _SQLiteWriter(LOG_DB_PATH)
    target = _SQLiteTargetHandler(_sql_writer)
    _listener = QueueListener(_queue, target, respect_handler_level=True)
    _listener.start()

    # Make sure we stop cleanly when the process exits
    def _shutdown():
        try:
            if _listener:
                _listener.stop()
        finally:
            if _sql_writer:
                _sql_writer.close()

    atexit.register(_shutdown)
    _configured = True


def get_logger(name: str = "mood_dash") -> logging.Logger:
    """
    Get a configured logger that writes to:
      - the SQLite DB (via QueueHandler -> QueueListener -> SQLiteWriter)
      - the console (nice during development)
    Safe to call many times (Streamlit reruns).
    """
    _ensure_logging_backend()

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Avoid duplicate handlers across reruns
    if not any(isinstance(h, QueueHandler) for h in logger.handlers):
        logger.addHandler(QueueHandler(_queue))

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        ch.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        logger.addHandler(ch)

    # Optional: don't propagate to root to avoid double prints
    logger.propagate = False
    return logger
