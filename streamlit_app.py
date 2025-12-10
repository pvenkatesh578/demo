import streamlit as st
import pandas as pd
from datetime import date, timedelta
import os

# ---------------------------
# PAGE CONFIG / BEAUTIFY
# ---------------------------
st.set_page_config(page_title="Daily Habit Tracker", layout="centered")

st.markdown("""
    <style>
        .big-title { font-size: 36px; font-weight: 700; text-align: center; color: #5A2EA6; }
        .section-title { font-size: 26px; font-weight: 600; margin-top: 30px; color: #333; }
        .winner-box {
            padding: 12px;
            background-color: #E5D7FF;
            border-left: 6px solid #5A2EA6;
            border-radius: 6px;
            font-size: 18px;
            font-weight: 600;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='big-title'>🏆 Daily Habit Score Tracker</div>", unsafe_allow_html=True)

# ---------------------------
# CONFIG
# ---------------------------
NAMES = ["Theju", "Udaya", "Teju", "Tushara", "Kavya"]
DATA_FILE = "scores.csv"

# ---------------------------
# LOAD / INITIALIZE DATA
# ---------------------------
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["name", "date", "break", "diet", "workout", "social", "diet_penalty", "score"])
    df.to_csv(DATA_FILE, index=False)

# ---------------------------
# INPUT SECTION
# ---------------------------
st.markdown("<div class='section-title'>Submit Today's Update</div>", unsafe_allow_html=True)

name = st.selectbox("👤 Select Name", NAMES)

diet = st.selectbox("🍽️ Diet", ["Yes", "No"])
workout = st.selectbox("💪 Workout", ["Yes", "No"])
social = st.selectbox("📱 Social Media", ["Yes", "No"])

# -----------------------------------
# BREAK OPTION ONLY IF WORKOUT = NO
# -----------------------------------
if workout == "No":
    take_break = st.selectbox("🛑 Break Today?", ["No", "Yes"])
else:
    take_break = "No"  # hide & force No break

# ---------------------------
# SCORING LOGIC
# ---------------------------
if take_break == "Yes":
    st.info("Break Day Selected → No Negative Points. Score = 0")
    diet_penalty = 0
    score = 0
else:
    diet_penalty = 1
    if diet == "No":
        diet_penalty = st.number_input("How many diet mistakes?", min_value=1, max_value=10, value=1)

    score = 0
    score += 1 if diet == "Yes" else -diet_penalty
    score += 1 if workout == "Yes" else -1
    score += 1 if social == "Yes" else 0

st.subheader(f"⭐ Today's Score: {score}")

# ---------------------------
# SUBMIT LOGIC (REPLACE ENTRY IF EXISTS)
# ---------------------------
if st.button("Submit"):
    today = str(date.today())

    # Remove any existing entry for same person + date
    df = df[~((df["name"] == name) & (df["date"] == today))]

    new_row = {
        "name": name,
        "date": today,
        "break": take_break,
        "diet": diet,
        "workout": workout,
        "social": social,
        "diet_penalty": diet_penalty,
        "score": score
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

    st.success("✅ Your update has been submitted!")

# ---------------------------
# FORMAT DATE
# ---------------------------
df["date"] = pd.to_datetime(df["date"]).dt.date
today = date.today()

# ---------------------------
# DAILY SUMMARY
# ---------------------------
st.markdown("<div class='section-title'>📅 Daily Summary</div>", unsafe_allow_html=True)

daily_df = df[df["date"] == today]

if len(daily_df) == 0:
    st.info("No entries today yet.")
else:
    st.dataframe(daily_df[["name", "break", "diet", "workout", "social", "score"]])

# ---------------------------
# WEEKLY SUMMARY (Calendar Week – Mon to Sun)
# ---------------------------
st.markdown("<div class='section-title'>📅 Weekly Summary (Calendar Week)</div>", unsafe_allow_html=True)

monday = today - timedelta(days=today.weekday())
sunday = monday + timedelta(days=6)

weekly_df = df[(df["date"] >= monday) & (df["date"] <= sunday)]
weekly_scores = weekly_df.groupby("name")["score"].sum().reset_index().sort_values("score", ascending=False)

st.markdown(f"**Week Range:** {monday} → {sunday}")
st.dataframe(weekly_scores)

if len(weekly_scores) > 0:
    w = weekly_scores.iloc[0]
    st.markdown(f"<div class='winner-box'>🏆 Weekly Winner: {w['name']} ({w['score']} points)</div>",
                unsafe_allow_html=True)

# ---------------------------
# MONTHLY SUMMARY (Last 28 Days)
# ---------------------------
st.markdown("<div class='section-title'>📆 Monthly Summary (Last 28 Days)</div>", unsafe_allow_html=True)

month_start = today - timedelta(days=27)
monthly_df = df[(df["date"] >= month_start) & (df["date"] <= today)]

monthly_scores = monthly_df.groupby("name")["score"].sum().reset_index().sort_values("score", ascending=False)

st.markdown(f"**28-Day Range:** {month_start} → {today}")
st.dataframe(monthly_scores)

if len(monthly_scores) > 0:
    mw = monthly_scores.iloc[0]
    st.markdown(
        f"<div class='winner-box'>🏆 Monthly Winner: {mw['name']} ({mw['score']} points)</div>",
        unsafe_allow_html=True
    )
