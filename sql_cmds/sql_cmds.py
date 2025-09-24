import sqlite3
from pathlib import Path
import pandas as pd
from log_setup import get_logger
from dotenv import load_dotenv
import os

logger = get_logger(__name__)

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "daylio_data.db")


def create_db_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    """
    creates a new database connection to the SQLite database
    :return:
    """
    return sqlite3.connect(db_path)


def execute_sql_command(conn: sqlite3.Connection, command: str, commit: bool = True, *args):
    with conn:
        cursor = conn.cursor()
        if args:
            cursor.execute(command, *args)
            # if len(*args) == 1:
            #     cursor.execute(command, args)
            # else:
            #     cursor.execute(command, *args)
        else:
            cursor.execute(command)

        if commit:
            conn.commit()
        else:
            return cursor.fetchall()


def execute_sql_script(conn: sqlite3.Connection, script_path: str, commit: bool = True):
    with conn:
        script = Path(script_path)
        if not script.exists():
            logger.error(f"SQL script {script_path} does not exist.")
            return
        logger.info(f"Executing script: {script.name}")
        cursor = conn.cursor()
        script_text = script.read_text()
        cursor.executescript(script_text)
        if commit:
            conn.commit()
        else:
            return cursor.fetchall()


def read_sql_view_to_df(conn: sqlite3.Connection, view_name: str) -> pd.DataFrame:
    logger.info(f"Retrieving data from view {view_name}...")
    query = f"SELECT * FROM {view_name}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
