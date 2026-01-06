import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests
import base64
from io import StringIO

# ---------------------------
# TIMEZONE → PST
# ---------------------------
PST = pytz.timezone("America/Los_Angeles")

def get_pst_today():
    return datetime.now(PST).date()

today = get_pst_today()

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="Daily Habit Tracker", layout="centered")

st.markdown("""
<style>
.big-title { font-size: 36px; font-weight: 700; text-align: center; color: #5A2EA6; }
.today-date { font-size: 20px; text-align: center; color: #444; margin-bottom: 20px; }
.section-title { font-size: 26px; font-weight: 600; margin-top: 30px; }
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
st.markdown(f"<div class='today-date'>📅 Today (PST): <b>{today}</b></div>", unsafe_allow_html=True)

# ---------------------------
# CONFIG
# ---------------------------
NAMES = ["Theju", "Udaya", "Teju", "Tushara", "Kavya"]

COLUMNS = [
    "name", "date", "break",
    "diet", "workout", "social",
    "diet_penalty", "score"
]

# ---------------------------
# GITHUB HELPERS
# ---------------------------
def github_read_csv():
    url = f"https://api.github.com/repos/{st.secrets.GITHUB_REPO}/contents/{st.secrets.DATA_FILE}"
    headers = {
        "Authorization": f"token {st.secrets.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    r = requests.get(url, headers=headers)

    if r.status_code == 404:
        return pd.DataFrame(columns=COLUMNS)

    r.raise_for_status()
    content = base64.b64decode(r.json()["content"]).decode("utf-8")
    return pd.read_csv(StringIO(content))


def github_write_csv(df, message):
    url = f"https://api.github.com/repos/{st.secrets.GITHUB_REPO}/contents/{st.secrets.DATA_FILE}"
    headers = {
        "Authorization": f"token {st.secrets.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    r = requests.get(url, headers=headers)
    sha = r.json().get("sha") if r.status_code == 200 else None

    csv_bytes = df.to_csv(index=False).encode("utf-8")
    content = base64.b64encode(csv_bytes).decode("utf-8")

    payload = {
        "message": message,
        "content": content,
        "branch": st.secrets.GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=headers, json=payload)
    r.raise_for_status()

# ---------------------------
# LOAD DATA
# ---------------------------
df = github_read_csv()
df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

# ---------------------------
# AVAILABLE DATES (PAST 60 DAYS)
# ---------------------------
START_DATE = today - timedelta(days=60)
all_dates = pd.date_range(START_DATE, today).date.tolist()
all_dates.reverse()

# ---------------------------
# INPUT SECTION
# ---------------------------
st.markdown("<div class='section-title'>Submit Daily Update</div>", unsafe_allow_html=True)

selected_date = st.selectbox(
    "📅 Select Date",
    all_dates,
    index=0,
    format_func=lambda d: d.strftime("%Y-%m-%d")
)

name = st.selectbox("👤 Select Name", NAMES)

# Check existing entry
already_exists = not df[
    (df["name"] == name) & (df["date"] == selected_date)
].empty

if already_exists:
    st.warning(f"⚠️ Entry already exists for {name} on {selected_date}. Submitting will overwrite it.")

diet = st.selectbox("🍽️ Diet", ["Yes", "No"])
workout = st.selectbox("💪 Workout", ["Yes", "No"])
social = st.selectbox("📱 Social Media", ["Yes", "No"])

if workout == "No":
    take_break = st.selectbox("🛑 Break Today?", ["No", "Yes"])
else:
    take_break = "No"

# ---------------------------
# SCORING
# ---------------------------
if take_break == "Yes":
    st.info("Break Day → Score = 0")
    diet_penalty = 0
    score = 0
else:
    diet_penalty = 1
    if diet == "No":
        diet_penalty = st.number_input("Diet mistakes", 1, 10, 1)

    score = 0
    score += 1 if diet == "Yes" else -diet_penalty
    score += 1 if workout == "Yes" else -1
    score += 1 if social == "Yes" else 0

st.subheader(f"⭐ Score for {selected_date}: {score}")

# ---------------------------
# SUBMIT
# ---------------------------
if st.button("Submit Score"):
    df = df[~((df["name"] == name) & (df["date"] == selected_date))]

    new_row = {
        "name": name,
        "date": selected_date,
        "break": take_break,
        "diet": diet,
        "workout": workout,
        "social": social,
        "diet_penalty": diet_penalty,
        "score": score
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    github_write_csv(df, f"Update {name} {selected_date}")
    st.success("✅ Saved to GitHub")

# ---------------------------
# DAILY SUMMARY
# ---------------------------
st.markdown("<div class='section-title'>📅 Daily Summary</div>", unsafe_allow_html=True)

daily_df = df[df["date"] == selected_date]

if daily_df.empty:
    st.info("No entries for this date.")
else:
    st.dataframe(daily_df[["name", "break", "diet", "workout", "social", "score"]])

# ---------------------------
# WEEKLY SUMMARY
# ---------------------------
st.markdown("<div class='section-title'>📅 Weekly Summary</div>", unsafe_allow_html=True)

monday = today - timedelta(days=today.weekday())
sunday = monday + timedelta(days=6)

weekly_df = df[(df["date"] >= monday) & (df["date"] <= sunday)]
weekly_scores = (
    weekly_df.groupby("name")["score"]
    .sum()
    .reset_index()
    .sort_values("score", ascending=False)
)

st.markdown(f"**Week:** {monday} → {sunday}")
st.dataframe(weekly_scores)

if not weekly_scores.empty:
    w = weekly_scores.iloc[0]
    st.markdown(
        f"<div class='winner-box'>🏆 Weekly Winner: {w['name']} ({w['score']} points)</div>",
        unsafe_allow_html=True
    )

# ---------------------------
# MONTHLY SUMMARY
# ---------------------------
st.markdown("<div class='section-title'>📆 Monthly Summary</div>", unsafe_allow_html=True)

month_start = today.replace(day=1)
monthly_df = df[(df["date"] >= month_start) & (df["date"] <= today)]
monthly_scores = (
    monthly_df.groupby("name")["score"]
    .sum()
    .reset_index()
    .sort_values("score", ascending=False)
)

st.markdown(f"**Month:** {month_start} → {today}")
st.dataframe(monthly_scores)

if not monthly_scores.empty:
    mw = monthly_scores.iloc[0]
    st.markdown(
        f"<div class='winner-box'>🏆 Monthly Winner: {mw['name']} ({mw['score']} points)</div>",
        unsafe_allow_html=True
    )

# ---------------------------
# RESET
# ---------------------------
st.markdown("<div class='section-title'>🔄 Reset All Data</div>", unsafe_allow_html=True)

if "confirm_reset" not in st.session_state:
    st.session_state.confirm_reset = False

if st.button("RESET EVERYTHING"):
    st.session_state.confirm_reset = True

if st.session_state.confirm_reset:
    st.warning("⚠️ This will delete ALL data.")
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Yes, delete"):
            df = pd.DataFrame(columns=COLUMNS)
            github_write_csv(df, "Reset all habit data")
            st.success("🔥 All data cleared")
            st.session_state.confirm_reset = False

    with col2:
        if st.button("Cancel"):
            st.session_state.confirm_reset = False
