

def main():
    import pandas as pd
    import altair as alt
    import streamlit as st

    from datetime import datetime
    from log_setup import logger
    from sql_cmds import create_db_conn

    logger.info("Starting Streamlit app...")

    st.set_page_config(page_title="Mood Dashboard",
                       page_icon="📈", layout="centered")

    if "user" not in st.session_state or st.session_state["user"] is None:
        st.warning("Please log in from the Login page.")
        st.switch_page("pages/0_Login.py")
        st.stop()

    logger.info("Generating dashboard...")
    st.title("📈 Mood Dashboard")

    with create_db_conn() as db_conn:
        last_update = pd.read_sql(
            "SELECT MAX(LAST_ENTRY_CREATION_TIME) from prefs", db_conn).iloc[0, 0]
    last_update_date = datetime.strptime(
        str(last_update), "%Y-%m-%d %H:%M:%S.%f")

    st.subheader(
        f"Last Mood Data Update: {last_update_date.strftime('%Y-%m-%d %H:%M:%S')}")

    st.subheader("📈 Daily Mood Average (Last 90 Days)")
    logger.info("Loading daily mood averages from database...")
    with create_db_conn() as db_conn:
        df_avg = pd.read_sql("SELECT * FROM v_daily_avgs", db_conn)
    df_avg['day'] = pd.to_datetime(df_avg['day'])

    # Altair chart with trend line
    logger.info("Creating Altair chart for daily mood averages...")
    chart = alt.Chart(df_avg).mark_line(point=True).encode(
        x='day:T',
        y='avg_mood_value:Q'
    ).properties(
        width=700,
        height=300
    )

    trend = chart.transform_regression(
        'day', 'avg_mood_value', method='linear'
    ).mark_line(color='red', strokeDash=[4, 2])

    st.altair_chart(chart + trend, use_container_width=True)

    if st.checkbox("Show Mood Entries"):
        logger.info("Loading mood entries from database...")
        query = "SELECT * from v_entry_details where date(day) > date('now', '-14 days') order by entry_datetime desc"
        with create_db_conn() as conn:
            df_moods = pd.read_sql(query, conn)

        df_moods['day'] = pd.to_datetime(df_moods['day'])
        st.subheader("📅 Mood Entries (Last 14 Days)")
        logger.info("Displaying mood entries in Streamlit table...")
        st.table(df_moods)

    st.subheader("🏷️ Top Activities (Interactive Drilldown)")
    logger.info("Loading activity summary from database...")
    with create_db_conn() as conn:
        df_acts = pd.read_sql("SELECT * FROM v_activity_summary", conn)

    # Altair requires no NaNs in category columns
    logger.info("Creating interactive activity drilldown...")
    df_acts = df_acts.dropna(subset=["group", "activity"])

    # Step 1: Dropdown to select group
    group_list = df_acts["group"].unique().tolist()
    selected_group = st.selectbox("Select Activity Group", group_list)

    # Step 2: Filter for that group
    filtered_df = df_acts[df_acts["group"] == selected_group]

    # Step 3: Plot
    chart = alt.Chart(filtered_df).mark_bar().encode(
        x=alt.X("count:Q", title="Frequency"),
        y=alt.Y("activity:N", sort="-x", title="Activity"),
        tooltip=["activity", "count"]
    ).properties(
        width=600,
        height=400,
        title=f"Top Activities in '{selected_group}' Group"
    )

    st.altair_chart(chart, use_container_width=True)


if __name__ == "__main__":
    main()
