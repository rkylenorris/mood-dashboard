from sql_cmds import create_db_conn, read_sql_view_to_df
import streamlit as st
import plotly.express as px

view = "v_sleep_main_per_day"

df = read_sql_view_to_df(create_db_conn(), view)
st.title("Sleep Timeline")

fig_bar = px.bar(
    df,
    x="date",
    y="duration_hours",
    hover_data=["sleep_quality_label"],
    title="Sleep Duration by Date (Non-Nap Only)",
    labels={"duration_hours": "Hours Slept", "date": "Sleep Date"}
)
fig_bar.update_layout(xaxis_title="Date", yaxis_title="Sleep Duration (Hours)")

# --- Pie chart: Proportion of sleep quality ---
quality_counts = df["sleep_quality_label"].value_counts().reset_index()
quality_counts.columns = ["sleep_quality_label", "count"]

fig_pie = px.pie(
    quality_counts,
    values="count",
    names="sleep_quality_label",
    title="Proportion of Sleep Quality (By Label)",
    hole=0.4  # Donut chart
)

st.title("Sleep Dashboard")

bar_col, pie_col = st.columns(2)
bar_col.header("Sleep Duration by Date")
pie_col.header("Proportion of Sleep Quality")
with bar_col:
    st.write("This bar chart shows the total hours slept each day, excluding naps.")
    st.plotly_chart(fig_bar, use_container_width=True)

with pie_col:
    st.write("This pie chart shows the proportion of different sleep quality labels.")
    st.plotly_chart(fig_pie, use_container_width=True)
