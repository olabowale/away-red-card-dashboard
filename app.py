import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Away Red Card Monitor",
    page_icon="🟥",
    layout="wide",
)

API_URL = "https://v3.football.api-sports.io/fixtures"

LEAGUES = {
    39: "England - Premier League",
    140: "Spain - La Liga",
    78: "Germany - Bundesliga",
    135: "Italy - Serie A",
    61: "France - Ligue 1",
    94: "Portugal - Primeira Liga",
    88: "Netherlands - Eredivisie",
    144: "Belgium - Jupiler Pro League",
    203: "Turkey - Süper Lig",
    179: "Scotland - Premiership",
    218: "Austria - Bundesliga",
    207: "Switzerland - Super League",
    119: "Denmark - Superliga",
    103: "Norway - Eliteserien",
    113: "Sweden - Allsvenskan",
    197: "Greece - Super League",
    106: "Poland - Ekstraklasa",
    345: "Czech Republic - First League",
    283: "Romania - Liga I",
    210: "Croatia - HNL",
    286: "Serbia - Super Liga",
    271: "Hungary - NB I",
    333: "Ukraine - Premier League",
    172: "Bulgaria - First League",
    357: "Ireland - Premier Division",
    244: "Finland - Veikkausliiga",
}

CARD_DETAILS = {
    "red card",
    "yellow-red card",
    "second yellow",
    "second yellow card",
}


def get_api_key():
    """Read the API key from Streamlit Secrets, with a local env fallback."""
    try:
        key = st.secrets.get("API_FOOTBALL_KEY", "")
    except Exception:
        key = ""
    return str(key or os.getenv("API_FOOTBALL_KEY", "")).strip()


API_KEY = get_api_key()


@st.cache_data(ttl=15, show_spinner=False)
def get_live_fixtures(api_key):
    if not api_key:
        return None, "API-Football key is not configured."

    try:
        response = requests.get(
            API_URL,
            headers={"x-apisports-key": api_key},
            params={"live": "all"},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("errors"):
            return None, str(data["errors"])

        return data.get("response", []), None

    except requests.RequestException as exc:
        return None, f"API request failed: {exc}"
    except ValueError:
        return None, "API returned invalid JSON."


def get_match_minute(fixture):
    elapsed = fixture.get("fixture", {}).get("status", {}).get("elapsed")
    return int(elapsed) if isinstance(elapsed, int) else 0


def get_card_events(fixture):
    away_id = fixture.get("teams", {}).get("away", {}).get("id")
    cards = []

    for event in fixture.get("events", []) or []:
        if event.get("type") != "Card":
            continue

        detail = str(event.get("detail", "")).strip().lower()
        if detail not in CARD_DETAILS:
            continue

        if event.get("team", {}).get("id") != away_id:
            continue

        minute = event.get("time", {}).get("elapsed")
        extra = event.get("time", {}).get("extra")
        minute_text = str(minute) if minute is not None else "?"
        if extra:
            minute_text += f"+{extra}"

        cards.append({
            "minute": minute_text,
            "player": event.get("player", {}).get("name") or "Unknown player",
            "detail": event.get("detail", "Red Card"),
        })

    return cards


def fixture_to_row(fixture):
    fixture_info = fixture.get("fixture", {})
    teams = fixture.get("teams", {})
    goals = fixture.get("goals", {})
    league = fixture.get("league", {})

    home = teams.get("home", {})
    away = teams.get("away", {})

    home_goals = goals.get("home")
    away_goals = goals.get("away")

    home_score = home_goals if isinstance(home_goals, int) else 0
    away_score = away_goals if isinstance(away_goals, int) else 0
    away_cards = get_card_events(fixture)

    return {
        "Fixture ID": fixture_info.get("id"),
        "League": league.get("name", "Unknown"),
        "League ID": league.get("id"),
        "Home Team": home.get("name", "Unknown"),
        "Away Team": away.get("name", "Unknown"),
        "Score": f"{home_score} - {away_score}",
        "Minute": get_match_minute(fixture),
        "Total Goals": home_score + away_score,
        "Away Red": bool(away_cards),
        "Away Red Details": "; ".join(
            f"{c['minute']}' {c['player']} ({c['detail']})"
            for c in away_cards
        ),
        "Away Red Count": len(away_cards),
        "Status": fixture_info.get("status", {}).get("long", ""),
    }


st.sidebar.title("⚙️ Filters")

selected_leagues = st.sidebar.multiselect(
    "Leagues",
    options=list(LEAGUES.keys()),
    default=list(LEAGUES.keys()),
    format_func=lambda x: LEAGUES[x],
)

min_minute = st.sidebar.number_input(
    "Minimum match minute",
    min_value=0,
    max_value=130,
    value=15,
    step=1,
)

max_total_goals = st.sidebar.number_input(
    "Maximum total goals",
    min_value=0,
    max_value=15,
    value=4,
    step=1,
)

low_score_only = st.sidebar.checkbox("Low-score matches only", value=False)
away_red_only = st.sidebar.checkbox("Away red card only", value=False)

refresh_seconds = st.sidebar.selectbox(
    "Refresh interval",
    options=[60, 120],
    index=1,
    format_func=lambda x: f"{x} seconds",
)

st.title("🟥 Away Red Card Monitor")
st.caption(
    "Live football dashboard using API-Football. "
    "Highlights matches where the away team has received a red card."
)

if not API_KEY:
    st.error("API-Football key is not configured.")
    st.info("On Streamlit Cloud, open Settings → Secrets and add:")
    st.code('API_FOOTBALL_KEY = "YOUR_API_FOOTBALL_KEY"', language="toml")
    st.stop()

with st.spinner("Loading live fixtures..."):
    fixtures, error = get_live_fixtures(API_KEY)

if error:
    st.error(error)
    st.stop()

if not fixtures:
    st.info("No live fixtures are currently available.")
    st.stop()

df = pd.DataFrame([fixture_to_row(f) for f in fixtures])

if selected_leagues:
    df = df[df["League ID"].isin(selected_leagues)]

df = df[df["Minute"] >= min_minute]
df = df[df["Total Goals"] <= max_total_goals]

if low_score_only:
    df = df[df["Total Goals"] <= 2]

if away_red_only:
    df = df[df["Away Red"]]

df = df.sort_values(
    by=["Away Red", "Minute", "League"],
    ascending=[False, False, True],
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Live matches", len(df))

with col2:
    st.metric("Away red-card matches", int(df["Away Red"].sum()) if not df.empty else 0)

with col3:
    st.metric(
        "Matches ≤ 2 goals",
        int((df["Total Goals"] <= 2).sum()) if not df.empty else 0,
    )

with col4:
    st.metric("Highest match minute", int(df["Minute"].max()) if not df.empty else 0)

st.divider()
st.subheader("⚽ Live Matches")

if df.empty:
    st.warning("No matches currently satisfy the selected filters.")
else:
    display_df = df[
        [
            "League",
            "Home Team",
            "Away Team",
            "Score",
            "Minute",
            "Total Goals",
            "Away Red",
            "Away Red Count",
            "Away Red Details",
            "Status",
        ]
    ].copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Away Red": st.column_config.CheckboxColumn(
                "Away Red",
                help="Whether the away team has received a red card.",
            ),
            "Minute": st.column_config.NumberColumn("Min", format="%d"),
            "Total Goals": st.column_config.NumberColumn("Goals", format="%d"),
            "Away Red Count": st.column_config.NumberColumn("Away Reds", format="%d"),
        },
    )

st.divider()
st.subheader("🚨 Away Red-Card Alerts")

red_df = df[df["Away Red"]].copy()

if red_df.empty:
    st.success("No away-team red cards match the current filters.")
else:
    for _, row in red_df.iterrows():
        st.warning(
            f"**{row['Away Team']}** received a red card against "
            f"**{row['Home Team']}** — {row['Score']} ({row['Minute']}' min). "
            f"{row['Away Red Details']}"
        )

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
st.caption(
    f"Last successful API refresh: {now} · "
    f"Next refresh target: {refresh_seconds}s"
)

time.sleep(refresh_seconds)
st.rerun()
