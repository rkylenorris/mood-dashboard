import streamlit as st
from datetime import datetime
from sql_cmds import create_db_conn, execute_sql_command

st.title("📝 Topics to Discuss")

# form for adding new topic
with st.form("add_topic"):
    new_topic = st.text_input("Topic (short description)")
    new_details = st.text_area("Details (optional)")
    if st.form_submit_button("Add Topic") and new_topic.strip():
        conn = create_db_conn()
        execute_sql_command(conn, "INSERT INTO topics (topic, details) VALUES (?, ?)",
                            True, *(new_topic.strip(), new_details.strip() or None))
        st.success("Topic added!")

# View selection
view = st.radio("View:", ["Open Topics", "Covered Topics"])

if view == "Open Topics":
    conn = create_db_conn()
    rows = execute_sql_command(
        conn, "SELECT id, topic, details, created_at FROM topics WHERE covered = 0 ORDER BY created_at DESC", False)
else:
    conn = create_db_conn()
    rows = execute_sql_command(
        conn, "SELECT id, topic, details, covered_at FROM topics WHERE covered = 1 ORDER BY covered_at DESC", False)

# Display topics
if rows:
    for row in rows:
        tid, topic, details, date = row
        with st.expander(f"{topic} ({date[:10]})"):
            new_details = st.text_area(
                "Details", value=details or "", key=f"details_{tid}")
            col1, col2 = st.columns([1, 1])

            with col1:
                if st.button("💾 Save Details", key=f"save_{tid}"):
                    execute_sql_command(create_db_conn(
                    ), "UPDATE topics SET details = ? WHERE id = ?", True, (new_details.strip(), tid))
                    st.success("Details updated.")

            with col2:
                if view == "Open Topics":
                    if st.button("✅ Mark as Covered", key=f"cover_{tid}"):
                        execute_sql_command(create_db_conn(
                        ), "UPDATE topics SET covered = 1, covered_at = ? WHERE id = ?", True, (datetime.now().isoformat(), tid))
else:
    st.info("No topics to show.")
