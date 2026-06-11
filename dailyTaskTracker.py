import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import time

# ---------------- CONFIG ----------------
st.set_page_config(page_title="AI Task Tracker", layout="wide")

FILE = "tasks.csv"

# ---------------- DATA HANDLER ----------------
def init_data():
    if not os.path.exists(FILE):
        df = pd.DataFrame(columns=[
            "Task", "Category", "Priority",
            "Deadline", "Status", "Time_Spent",
            "Created_At", "Completed_At"
        ])
        df.to_csv(FILE, index=False)

def load_data():
    return pd.read_csv(FILE)

def save_data(df):
    df.to_csv(FILE, index=False)

def add_task(task, category, priority, deadline):
    df = load_data()
    new_task = {
        "Task": task,
        "Category": category,
        "Priority": priority,
        "Deadline": deadline,
        "Status": "Pending",
        "Time_Spent": 0,
        "Created_At": datetime.now(),
        "Completed_At": None
    }
    df = pd.concat([df, pd.DataFrame([new_task])], ignore_index=True)
    save_data(df)

def update_task(index, status, time_spent):
    df = load_data()
    df.at[index, "Status"] = status
    df.at[index, "Time_Spent"] = time_spent

    if status == "Completed":
        df.at[index, "Completed_At"] = datetime.now()

    save_data(df)

def delete_task(index):
    df = load_data()
    df = df.drop(index)
    save_data(df)

# ---------------- ANALYTICS ----------------
def preprocess(df):
    df["Deadline"] = pd.to_datetime(df["Deadline"], errors='coerce')
    df["Completed_At"] = pd.to_datetime(df["Completed_At"], errors='coerce')
    df["Created_At"] = pd.to_datetime(df["Created_At"], errors='coerce')
    return df

def completion_rate(df):
    return (df["Status"] == "Completed").mean() * 100 if len(df) else 0

def avg_time(df):
    return df["Time_Spent"].mean() if len(df) else 0

def productive_hours(df):
    completed = df[df["Status"] == "Completed"]
    if completed.empty:
        return "Not enough data"

    completed["Hour"] = completed["Completed_At"].dt.hour
    peak = completed["Hour"].mode()[0]
    return f"{peak}:00 - {peak+1}:00"

def delayed_tasks(df):
    now = pd.Timestamp.now()
    return df[(df["Deadline"] < now) & (df["Status"] != "Completed")]

def productivity_score(df):
    if len(df) == 0:
        return 0

    completed = (df["Status"] == "Completed").sum()
    total = len(df)

    deadline_met = (
        (df["Completed_At"] <= df["Deadline"]) &
        (df["Status"] == "Completed")
    ).sum()

    score = (
        (completed / total) * 50 +
        (deadline_met / total) * 30 +
        (1 / (df["Time_Spent"].mean() + 1)) * 20
    )

    return round(score, 2)

# ---------------- AI INSIGHTS ----------------
def generate_insights(df):
    insights = []

    if df.empty:
        return ["Start adding tasks to get insights."]

    rate = completion_rate(df)

    if rate < 50:
        insights.append("⚠️ Low completion rate — reduce overload.")
    else:
        insights.append("✅ Strong completion performance!")

    high_delay = df[
        (df["Priority"] == "High") &
        (df["Status"] != "Completed") &
        (df["Deadline"] < pd.Timestamp.now())
    ]

    if len(high_delay) > 0:
        insights.append("🚨 High-priority tasks are being delayed!")

    delayed = delayed_tasks(df)
    if len(delayed) > len(df) * 0.3:
        insights.append("⏳ Frequent deadline misses detected (procrastination).")

    insights.append(f"🧠 Peak productivity: {productive_hours(df)}")

    if len(df) > 5:
        insights.append("📉 Work consistency fluctuates — stabilize routine.")

    return insights

# ---------------- BONUS FEATURES ----------------
def streak_tracker(df):
    df = df[df["Status"] == "Completed"]
    df["Date"] = df["Completed_At"].dt.date

    unique_days = sorted(df["Date"].dropna().unique())

    streak = 0
    prev = None

    for day in unique_days[::-1]:
        if prev is None:
            streak = 1
        elif prev - timedelta(days=1) == day:
            streak += 1
        else:
            break
        prev = day

    return streak

def focus_timer(minutes):
    st.subheader("⏳ Focus Mode")

    total_seconds = minutes * 60
    progress = st.progress(0)

    for i in range(total_seconds):
        time.sleep(1)
        progress.progress((i + 1) / total_seconds)

    st.success("✅ Focus session complete!")

# ---------------- INIT ----------------
init_data()

st.title("🚀 AI-Powered Daily Task Tracker")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Add Task", "View Tasks", "Dashboard", "AI Insights", "Focus Mode"]
)

df = load_data()
df = preprocess(df)

# ---------------- ADD TASK ----------------
if menu == "Add Task":
    st.header("➕ Add Task")

    task = st.text_input("Task Name")
    category = st.selectbox("Category", ["Study", "Work", "Health", "Personal"])
    priority = st.selectbox("Priority", ["Low", "Medium", "High"])
    deadline = st.datetime_input("Deadline")

    if st.button("Add"):
        add_task(task, category, priority, str(deadline))
        st.success("Task added!")

# ---------------- VIEW TASK ----------------
elif menu == "View Tasks":
    st.header("📋 Tasks")

    if not df.empty:
        for i, row in df.iterrows():
            st.markdown(f"### {row['Task']}")
            st.write(row)

            col1, col2, col3 = st.columns(3)

            status = col1.selectbox("Status", ["Pending", "Completed"], key=f"s{i}")
            time_spent = col2.number_input("Time", min_value=0, key=f"t{i}")

            if col3.button("Update", key=f"u{i}"):
                update_task(i, status, time_spent)
                st.success("Updated!")

            if st.button("Delete", key=f"d{i}"):
                delete_task(i)
                st.warning("Deleted!")
    else:
        st.info("No tasks yet")

# ---------------- DASHBOARD ----------------
elif menu == "Dashboard":
    st.header("📊 Dashboard")

    if not df.empty:
        st.metric("Completion Rate", f"{completion_rate(df):.2f}%")
        st.metric("Avg Time", f"{avg_time(df):.2f} hrs")
        score = productivity_score(df)
        st.metric("Productivity Score", score)

        st.progress(score / 100)

        st.subheader("Category Distribution")
        st.bar_chart(df["Category"].value_counts())

        st.subheader("Task Status")
        st.bar_chart(df["Status"].value_counts())

        st.subheader("Daily Completion Trend")
        trend = df[df["Status"] == "Completed"]
        trend["Date"] = trend["Completed_At"].dt.date
        st.line_chart(trend["Date"].value_counts().sort_index())

        st.subheader("🔥 Streak")
        st.write(f"{streak_tracker(df)} days")
    else:
        st.info("No data available")

# ---------------- AI INSIGHTS ----------------
elif menu == "AI Insights":
    st.header("🧠 AI Insights")

    insights = generate_insights(df)

    for ins in insights:
        st.write(ins)

# ---------------- FOCUS MODE ----------------
elif menu == "Focus Mode":
    minutes = st.slider("Focus Time (minutes)", 1, 60, 25)

    if st.button("Start Focus"):
        focus_timer(minutes)

# ---------------- EXPORT ----------------
st.sidebar.download_button(
    "📥 Export Data",
    data=df.to_csv(index=False),
    file_name="tasks_export.csv",
    mime="text/csv"
)