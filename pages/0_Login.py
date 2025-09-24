import streamlit as st
import bcrypt
from sql_cmds import create_db_conn, execute_sql_command
from log_setup import get_logger
from dotenv import load_dotenv
import os

logger = get_logger(__name__)
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "daylio_data.db")


st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")

# Clear session to force login on fresh open
if "user" not in st.session_state:
    st.session_state["user"] = None

st.title("🔐 Login")

username = st.text_input("Username")
password = st.text_input("Password", type="password")


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate user against the database.
    :param username: Username to authenticate
    :param password: Password to authenticate
    :return: True if authentication is successful, False otherwise
    """
    print(type(username), type(password))
    with create_db_conn(DB_PATH) as conn:
        query = "SELECT password_hash FROM users WHERE username = ?"
        result = execute_sql_command(conn, query, False, (username,))

        if result:
            stored_password = result[0][0]
            return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
        else:
            return False


if st.button("Login"):
    if username and password:
        if authenticate_user(username, password):
            st.session_state["user"] = username
            st.success("Login successful!")
            logger.info(f"User {username} logged in successfully.")
            st.switch_page("main.py")
        else:
            st.error("Invalid username or password.")
            logger.warning(f"Failed login attempt for user {username}.")
    else:
        st.error("Please enter both username and password.")
