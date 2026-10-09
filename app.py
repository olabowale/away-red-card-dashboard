import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st

# ============================================================
# Away Red Card Monitor — Deployment Ready
# ============================================================
# API key:
#   Streamlit Cloud -> Settings -> Secrets
#   API_FOOTBALL_KEY = "YOUR_API_FOOTBALL_KEY"
#
# The dashboard uses API-Football's live fixture feed and filters
# the returned fixtures by competition name. This avoids relying
# on hard-coded league IDs for continental/international events.
# ============================================================

st.set_page_config(
    page_title="Away Red Card Monitor",
    page_icon="🟥",
    layout="wide",
)

API_URL = "https://v3.football.api-sports.io/fixtures"

# ------------------------------------------------------------
# Competition catalogue
# ------------------------------------------------------------
DOMESTIC = {
    "Europe — Domestic Leagues": [
        "Premier League",
        "La Liga",
        "Bundesliga",
        "Serie A",
        "Ligue 1",
        "Primeira Liga",
        "Eredivisie",
        "Jupiler Pro League",
        "Süper Lig",
        "Scottish Premiership",
        "Bundesliga",
        "Super League",
        "Superliga",
        "Eliteserien",
        "Allsvenskan",
        "Super League 1",
        "Ekstraklasa",
        "Czech Liga",
        "Liga I",
        "HNL",
        "Super Liga",
        "NB I",
        "Premier League",
        "First League",
        "Premier Division",
        "Veikkausliiga",
    ],
}

CONTINENTAL_CLUB = {
    "Europe — Continental Clubs": [
        "UEFA Champions League",
        "UEFA Europa League",
        "UEFA Europa Conference League",
        "UEFA Super Cup",
        "UEFA Youth League",
    ],
    "Africa — Continental Clubs": [
        "CAF Champions League",
        "CAF Confederation Cup",
        "CAF Super Cup",
        "African Football League",
        "CECAFA Club Cup",
        "COSAFA Cup",
        "Arab Club Champions Cup",
    ],
    "Asia — Continental Clubs": [
        "AFC Champions League Elite",
        "AFC Champions League Two",
        "AFC Challenge League",
        "AFC Super Cup",
        "AFC Cup",
        "ASEAN Club Championship",
        "AGCFF Gulf Champions League",
    ],
}

INTERNATIONAL = {
    "Europe — National Teams": [
        "Euro Championship",
        "Euro Championship - Qualification",
        "UEFA Nations League",
        "UEFA Nations League - Women",
        "UEFA Championship - Women",
        "UEFA Championship - Women - Qualification",
        "UEFA U21 Championship",
        "UEFA U21 Championship - Qualification",
        "UEFA U19 Championship",
        "UEFA U19 Championship - Qualification",
        "UEFA U17 Championship",
        "UEFA U17 Championship - Qualification",
    ],
    "Africa — National Teams": [
        "Africa Cup of Nations",
        "Africa Cup of Nations - Qualification",
        "African Nations Championship",
        "African Nations Championship - Qualification",
        "Africa U23 Cup of Nations - Qualification",
        "CAF U23 Cup of Nations",
        "CAF Cup of Nations - U17",
    ],
    "Asia — National Teams": [
        "Asian Cup",
        "Asian Cup - Qualification",
        "AFC U23 Asian Cup",
        "AFC U23 Asian Cup - Qualification",
        "AFC U20 Asian Cup",
        "AFC U20 Asian Cup - Qualification",
        "AFC U17 Asian Cup",
        "AFC U17 Asian Cup - Qualification",
        "Gulf Cup of Nations",
        "Arab Cup",
        "ASEAN Championship",
        "CAFA Nations Cup",
        "EAFF E-1 Football Championship",
    ],
    "Americas — National Teams": [
        "Copa America",
        "CONCACAF Gold Cup",
        "CONCACAF Gold Cup - Qualification",
        "CONCACAF Nations League",
        "CONCACAF Nations League - Qualification",
        "CONCACAF U20",
        "CONCACAF U20 - Qualification",
    ],
    "Oceania — National Teams": [
        "OFC Nations Cup",
        "OFC U19 Championship",
    ],
    "World — National Teams": [
        "World Cup",
        "World Cup - Qualification Africa",
        "World Cup - Qualification Asia",
        "World Cup - Qualification CONCACAF",
        "World Cup - Qualification Europe",
        "World Cup - Qualification Intercontinental Play-offs",
        "World Cup - Qualification Oceania",
        "World Cup - Qualification South America",
        "FIFA Series",
        "Olympics Men",
        "Olympics Men - Qualification Concacaf",
    ],
}

# API-Football can use slightly different spellings for some domestic
# competitions. Aliases let the dashboard match those names.
ALIASES = {
    "Jupiler Pro League": {"Jupiler Pro League", "Pro League"},
    "Süper Lig": {"Süper Lig", "Super Lig"},
    "Scottish Premiership": {"Scottish Premiership"},
    "Super League 1": {"Super League 1", "Super League"},
    "Superliga": {"Superliga", "Superligaen"},
    "Czech Liga": {"Czech Liga", "Czech First League"},
    "First League": {"First League", "Parva Liga"},
    "Premier Division": {"Premier Division"},
    "UEFA Champions League": {"UEFA Champions League", "Champions League"},
    "UEFA Europa League": {"UEFA Europa League", "Europa League"},
    "UEFA Europa Conference League": {
        "UEFA Europa Conference League",
        "Europa Conference League",
    },
    "AFC Champions League Elite": {
        "AFC Champions League Elite",
        "AFC Champions League",
    },
    "AFC Champions League Two": {
        "AFC Champions League Two",
        "AFC Champions League 2",
    },
    "AFC Challenge League": {"AFC Challenge League"},
    "Africa Cup of Nations": {"Africa Cup of Nations", "AFCON"},
    "Asian Cup": {"Asian Cup"},
    "Copa America": {"Copa America"},
    "CONCACAF Gold Cup": {"CONCACAF Gold Cup", "Gold Cup"},
    "World Cup": {"World Cup"},
}


def normalize_name(value):
    return " ".join(str(value).strip().lower().split())


def names_for_selection(selected):
    names = set()
    for item in selected:
        names.update(ALIASES.get(item, {item}))
    return {normalize_name(x) for x in names}


# ------------------------------------------------------------
# Secure API key
# ------------------------------------------------------------
def get_api_key():
    try:
        key = st.secrets.get("API_FOOTBALL_KEY", "")
    except Exception:
        key = ""
    if not key:
        key = os.getenv("API_FOOTBALL_KEY", "")
    return str(key).strip()


API_KEY = get_api_key()


# ------------------------------------------------------------
# API
# ------------------------------------------------------------
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
        payload = response.json()

        if payload.get("errors"):
            return None, str(payload["errors"])

        return payload.get("response", []), None

    except requests.RequestException as exc:
        return None, f"API request failed: {exc}"
    except ValueError:
        return None, "API returned invalid JSON."


def get_match_minute(fixture):
    elapsed = fixture.get("fixture", {}).get("status", {}).get("elapsed")
    return int(elapsed) if isinstance(elapsed, int) else 0


RED_CARD_DETAILS = {
    "red card",
    "yellow-red card",
    "second yellow",
    "second yellow card",
}


def get_away_red_cards(fixture):
    away_id = fixture.get("teams", {}).get("away", {}).get("id")
    results = []

    for event in fixture.get("events", []) or []:
        if event.get("type") != "Card":
            continue

        detail = normalize_name(event.get("detail", ""))
        if detail not in RED_CARD_DETAILS:
            continue

        if event.get("team", {}).get("id") != away_id:
            continue

        minute = event.get("time", {}).get("elapsed")
        extra = event.get("time", {}).get("extra")
        minute_text = str(minute) if minute is not None else "?"
        if extra:
            minute_text += f"+{extra}"

        results.append({
            "minute": minute_text,
            "player": event.get("player", {}).get("name") or "Unknown player",
            "detail": event.get("detail", "Red Card"),
        })

    return results


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

    reds = get_away_red_cards(fixture)

    return {
        "Fixture ID": fixture_info.get("id"),
        "League": league.get("name", "Unknown"),
        "League Country": league.get("country", ""),
        "Home Team": home.get("name", "Unknown"),
        "Away Team": away.get("name", "Unknown"),
        "Score": f"{home_score} - {away_score}",
        "Minute": get_match_minute(fixture),
        "Total Goals": home_score + away_score,
        "Away Red": bool(reds),
        "Away Red Count": len(reds),
        "Away Red Details": "; ".join(
            f"{r['minute']}' {r['player']} ({r['detail']})"
            for r in reds
        ),
        "Status": fixture_info.get("status", {}).get("long", ""),
    }


# ------------------------------------------------------------
# Sidebar — competition filters
# ------------------------------------------------------------
st.sidebar.title("⚙️ Filters")

st.sidebar.subheader("Competition type")

competition_groups = st.sidebar.multiselect(
    "Select competition groups",
    options=[
        "Domestic leagues",
        "European continental clubs",
        "African continental clubs",
        "Asian continental clubs",
        "International national teams",
    ],
    default=[
        "Domestic leagues",
        "European continental clubs",
        "African continental clubs",
        "Asian continental clubs",
        "International national teams",
    ],
)

selected_competitions = []

if "Domestic leagues" in competition_groups:
    selected_competitions.extend(DOMESTIC["Europe — Domestic Leagues"])

if "European continental clubs" in competition_groups:
    selected_competitions.extend(CONTINENTAL_CLUB["Europe — Continental Clubs"])

if "African continental clubs" in competition_groups:
    selected_competitions.extend(CONTINENTAL_CLUB["Africa — Continental Clubs"])

if "Asian continental clubs" in competition_groups:
    selected_competitions.extend(CONTINENTAL_CLUB["Asia — Continental Clubs"])

if "International national teams" in competition_groups:
    for competitions in INTERNATIONAL.values():
        selected_competitions.extend(competitions)

selected_competitions = list(dict.fromkeys(selected_competitions))

specific_competitions = st.sidebar.multiselect(
    "Specific competitions",
    options=selected_competitions,
    default=selected_competitions,
    help="Use this to narrow the dashboard to individual competitions.",
)

st.sidebar.subheader("Match filters")

min_minute = st.sidebar.number_input(
    "Minimum match minute",
    min_value=0,
    max_value=130,
    value=55,
    step=1,
)

max_total_goals = st.sidebar.number_input(
    "Maximum total goals",
    min_value=0,
    max_value=15,
    value=2,
    step=1,
)

low_score_only = st.sidebar.checkbox(
    "Low-score matches only",
    value=False,
)

away_red_only = st.sidebar.checkbox(
    "Away red card only",
    value=False,
)

refresh_seconds = st.sidebar.selectbox(
    "Refresh interval",
    options=[15, 30, 60, 120],
    index=1,
    format_func=lambda x: f"{x} seconds",
)

# ------------------------------------------------------------
# Main page
# ------------------------------------------------------------
st.title("🟥 Away Red Card Monitor")
st.caption(
    "Live football dashboard using API-Football. "
    "Now covering domestic leagues plus European, African and Asian "
    "continental club competitions and international national-team competitions."
)

if not API_KEY:
    st.error("API-Football key is not configured.")
    st.info("Streamlit Cloud: Settings → Secrets")
    st.code('API_FOOTBALL_KEY = "YOUR_API_FOOTBALL_KEY"', language="toml")
    st.stop()

if not specific_competitions:
    st.warning("Select at least one competition.")
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

# ------------------------------------------------------------
# Filter by competition name
# ------------------------------------------------------------
allowed_names = names_for_selection(specific_competitions)

df["_league_normalized"] = df["League"].map(normalize_name)
df = df[df["_league_normalized"].isin(allowed_names)]

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

# ------------------------------------------------------------
# Metrics
# ------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Live matches", len(df))

with col2:
    st.metric(
        "Away red-card matches",
        int(df["Away Red"].sum()) if not df.empty else 0,
    )

with col3:
    st.metric(
        "Matches ≤ 2 goals",
        int((df["Total Goals"] <= 2).sum()) if not df.empty else 0,
    )

with col4:
    st.metric(
        "Highest match minute",
        int(df["Minute"].max()) if not df.empty else 0,
    )

st.divider()
st.subheader("⚽ Live Matches")

if df.empty:
    st.warning(
        "No live matches currently satisfy the selected competition and match filters."
    )
else:
    display_df = df[
        [
            "League",
            "League Country",
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

# ------------------------------------------------------------
# Footer / refresh
# ------------------------------------------------------------
now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
st.caption(
    f"Last API refresh: {now} · Refresh target: {refresh_seconds}s"
)

time.sleep(refresh_seconds)
st.rerun()
