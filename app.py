import os
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

API_URL = "https://v3.football.api-sports.io"
DATA_DIR = Path("away_red_card_data")
DATA_DIR.mkdir(exist_ok=True)
ALERT_LOG = DATA_DIR / "alerts.csv"

DEFAULT_LEAGUES = {
    39: "Premier League",
    140: "La Liga",
    78: "Bundesliga",
    135: "Serie A",
    61: "Ligue 1",
    94: "Primeira Liga",
    88: "Eredivisie",
    144: "Jupiler Pro League",
    203: "Süper Lig",
    179: "Scottish Premiership",
    218: "Austrian Bundesliga",
    207: "Swiss Super League",
    119: "Danish Superliga",
    103: "Eliteserien",
    113: "Allsvenskan",
    197: "Super League Greece",
    106: "Ekstraklasa",
    345: "Czech First League",
    283: "Liga I",
    210: "HNL",
    286: "Super Liga Serbia",
    271: "NB I",
    333: "Premier League Ukraine",
    172: "First League Bulgaria",
    357: "Premier Division Ireland",
    244: "Veikkausliiga",
}

st.set_page_config(
    page_title="Away Red Card Monitor",
    page_icon="🟥",
    layout="wide",
)

st.title("🟥 Away Red Card Live Monitor")
st.caption(
    "Live football dashboard using API-Football. "
    "Refresh the page to retrieve the latest live data."
)

api_key = os.getenv("API_FOOTBALL_KEY", "")

if not api_key:
    st.error(
        "API_FOOTBALL_KEY is not configured. "
        "Set it as an environment variable before starting the dashboard."
    )
    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.header("Filters")

selected_leagues = st.sidebar.multiselect(
    "Leagues",
    options=list(DEFAULT_LEAGUES.keys()),
    default=list(DEFAULT_LEAGUES.keys()),
    format_func=lambda x: DEFAULT_LEAGUES[x],
)

minute_filter = st.sidebar.slider(
    "Minimum match minute",
    min_value=0,
    max_value=90,
    value=55,
)

max_total_goals = st.sidebar.slider(
    "Maximum total goals",
    min_value=0,
    max_value=8,
    value=2,
)

low_score_only = st.sidebar.checkbox(
    "Only show low-score matches",
    value=False,
)

away_red_only = st.sidebar.checkbox(
    "Only show matches where away team has a red card",
    value=False,
)

refresh_seconds = st.sidebar.slider(
    "Auto-refresh interval (seconds)",
    min_value=15,
    max_value=120,
    value=30,
)

# ---------------- API ----------------
@st.cache_data(ttl=15)
def get_live_fixtures(api_key):
    response = requests.get(
        f"{API_URL}/fixtures",
        params={"live": "all"},
        headers={"x-apisports-key": api_key},
        timeout=20,
    )
    response.raise_for_status()
    return response.json().get("response", [])


def red_cards_for_team(events, team_id):
    result = []

    for event in events:
        if event.get("type") != "Card":
            continue

        detail = (event.get("detail") or "").lower()

        if detail not in {
            "red card",
            "yellow-red card",
            "second yellow",
            "second yellow card",
        }:
            continue

        if event.get("team", {}).get("id") != team_id:
            continue

        result.append(event)

    return result


def minute_text(event):
    elapsed = event.get("time", {}).get("elapsed")
    extra = event.get("time", {}).get("extra")

    if elapsed is None:
        return "?"

    return f"{elapsed}+{extra}'" if extra else f"{elapsed}'"


def process(fixtures):
    rows = []

    for f in fixtures:
        league_id = f.get("league", {}).get("id")

        if selected_leagues and league_id not in selected_leagues:
            continue

        status = f.get("fixture", {}).get("status", {})
        elapsed = status.get("elapsed") or 0

        home = f.get("teams", {}).get("home", {})
        away = f.get("teams", {}).get("away", {})

        home_id = home.get("id")
        away_id = away.get("id")

        home_goals = f.get("goals", {}).get("home") or 0
        away_goals = f.get("goals", {}).get("away") or 0

        total_goals = home_goals + away_goals

        events = f.get("events", [])

        away_reds = red_cards_for_team(
            events,
            away_id
        )

        if elapsed < minute_filter:
            continue

        if low_score_only and total_goals > max_total_goals:
            continue

        if away_red_only and not away_reds:
            continue

        rows.append({
            "League": f.get("league", {}).get("name"),
            "Home": home.get("name"),
            "Score": f"{home_goals}-{away_goals}",
            "Away": away.get("name"),
            "Minute": elapsed,
            "Away Red": len(away_reds),
            "Status": status.get("long"),
            "Fixture ID": f.get("fixture", {}).get("id"),
        })

    return pd.DataFrame(rows)


try:
    fixtures = get_live_fixtures(api_key)
except Exception as exc:
    st.error(f"Could not retrieve live football data: {exc}")
    st.stop()

df = process(fixtures)

# ---------------- SUMMARY ----------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Live matches", len(fixtures))
c2.metric("Matches shown", len(df))

if not df.empty:
    c3.metric(
        "Away-red matches",
        int((df["Away Red"] > 0).sum()),
    )
    c4.metric(
        "Low-score shown",
        int(
            df["Score"].apply(
                lambda x: sum(map(int, x.split("-")))
            ).le(max_total_goals).sum()
        ),
    )
else:
    c3.metric("Away-red matches", 0)
    c4.metric("Low-score shown", 0)

st.divider()

if df.empty:
    st.info("No matches currently meet your selected filters.")
else:
    st.dataframe(
        df.sort_values(
            ["Away Red", "Minute"],
            ascending=[False, False]
        ),
        use_container_width=True,
        hide_index=True,
    )

# ---------------- ALERT SECTION ----------------
red_df = df[df["Away Red"] > 0] if not df.empty else pd.DataFrame()

if not red_df.empty:
    st.subheader("🚨 Away Red Card Matches")

    st.dataframe(
        red_df,
        use_container_width=True,
        hide_index=True,
    )

# ---------------- ALERT HISTORY ----------------
st.subheader("📊 Alert History")

if ALERT_LOG.exists():
    try:
        alerts = pd.read_csv(ALERT_LOG)
        if not alerts.empty:
            st.dataframe(
                alerts.tail(100).iloc[::-1],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No saved alerts yet.")
    except Exception as exc:
        st.warning(f"Could not read alert history: {exc}")
else:
    st.info(
        "No alert history found. Run the Telegram monitor "
        "to populate the alert CSV."
    )

st.caption(
    f"Last dashboard refresh: "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

# Simple automatic refresh
time.sleep(refresh_seconds)
st.rerun()
