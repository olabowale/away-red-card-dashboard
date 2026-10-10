import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st
import pycountry

# ============================================================
# Away Red Card Monitor — Deployment Ready
# ============================================================
# Streamlit Cloud -> App Settings -> Secrets:
#   API_FOOTBALL_KEY = "YOUR_API_FOOTBALL_KEY"
#   TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
#   TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
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

API_ROOT = "https://v3.football.api-sports.io"
API_URL = f"{API_ROOT}/fixtures"
FIFA_API_ROOT = "https://api.fifa.com/api/v3/rankings/byCountry"

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


# Additional domestic competitions requested: men's second tiers, women's
# second tiers, Japan/South Korea, and Australia-wide/state-level leagues.
MENS_SECOND_DIVISION = {
    "Men — Second-division domestic leagues": [
        # Europe
        "2. Liga", "Challenger Pro League", "Championship", "League One",
        "League Two", "Eerste Divisie", "2. Bundesliga", "3. Liga",
        "Serie B", "Serie C - Girone A", "Serie C - Girone B", "Serie C - Girone C",
        "Ligue 2", "Ligue 3", "LaLiga 2", "Segunda División", "Liga Portugal 2",
        "Super League 2", "Prva Liga", "NB II", "FNL", "I Liga", "Liga II",
        "Persha Liga", "1. Division", "Ykkösliiga", "Ykkönen", "Erovnuli Liga 2",
        "2a Divisió", "First League", "Second League", "Division 1", "Division 2",
        # Africa and Middle East
        "Ligue 2 - Group A", "Ligue 2 - Group B", "Second League",
        "Second League - Group B", "Second League - Group C", "1st Division",
        "Super League", "Division 1", "Second Division",
        # Asia
        "J2 League", "J2/J3 League", "J3 League", "K League 2", "K3 League", "K4 League",
        "China League One", "League One", "League Two", "I-League", "I-League - 2nd Division",
        "Liga 2", "Thai League 2", "V.League 2", "Second Division", "Division 1",
        # Americas and Oceania
        "USL Championship", "USL League One", "USL League Two", "Primera Nacional",
        "Primera B", "Primera B Metropolitana", "Primera C", "Australian Championship",
    ],
}

WOMENS_SECOND_DIVISION = {
    "Women — Second-division domestic leagues": [
        "Women's Championship", "Women’s Championship", "2. Frauen-Bundesliga",
        "2. Frauen Bundesliga", "Feminine Division 2", "Division 2 Féminine",
        "Serie B Women", "Serie B Femminile", "Primera Federación Femenina",
        "Segunda Federación Femenina", "Women's National League", "Women's Premier League",
        "Women's Super League 2", "USL W League", "WPSL",
    ],
}

JAPAN_KOREA_DOMESTIC = {
    "Japan & South Korea — Domestic leagues (men and women)": [
        "J1 League", "J2 League", "J2/J3 League", "J3 League", "Japan Football League",
        "WE League", "Nadeshiko League", "Nadeshiko League 2",
        "K League 1", "K League 2", "K3 League", "K4 League", "WK-League",
    ],
}

AUSTRALIA_DOMESTIC = {
    "Australia — Domestic leagues (men and women)": [
        # National men's competitions
        "A-League", "Australian Championship", "Australia Cup",
        # State/regional men's competitions
        "Brisbane Premier League", "Capital Territory NPL", "Capital Territory NPL 2",
        "NNSW League 1", "New South Wales NPL", "New South Wales NPL 2",
        "Northern NSW NPL", "Northern Territory Premier League", "Npl Nsw U20",
        "Queensland NPL", "Queensland Premier League", "South Australia NPL",
        "South Australia State League 1", "Victoria NPL", "Victoria Premier League",
        "Western Australia NPL", "Tasmania NPL",
        # Women's competitions (coverage varies by state and season)
        "A-League Women", "NPL NSW Women", "New South Wales NPL Women",
        "Queensland NPL Women", "Victoria NPL Women", "South Australia NPL Women",
        "Western Australia NPL Women", "Capital Territory NPL Women",
        "Tasmania NPL Women", "Northern NSW NPL Women", "Brisbane Women's Premier League",
    ],
}


# Women's competitions are separate selectable groups so users can monitor
# women's football without mixing it into the men's competition list.
WOMENS_DOMESTIC = {
    "Europe — Women's Domestic Leagues": [
        "Women’s Super League", "Women's Super League", "WSL",
        "Women's Championship", "Frauen Bundesliga", "Frauenliga",
        "Primera División Femenina", "Primera Division Femenina",
        "Feminine Division 1", "Serie A Women", "Serie A Femminile",
        "Eredivisie Women", "Liga BPI", "Campeonato Nacional Feminino",
        "Scottish Women's Premier League", "Damallsvenskan", "Toppserien",
        "Kvindeliga", "Kansallinen Liiga", "AXA Women's Super League",
        "Ekstraliga Women", "Liga 1 Feminin", "Premiership Women",
        "B-Liga Women",
    ],
    "Africa — Women's Domestic Leagues": [
        "Super League Women", "NWFL Premiership", "Nigeria Women Football League",
    ],
    "Asia — Women's Domestic Leagues": [
        "WK-League", "Women's Super League", "Japan Women's WE League",
        "A-League Women",
    ],
    "Americas — Women's Domestic Leagues": [
        "NWSL", "Liga MX Femenil", "Brasileiro Women", "National Women's Soccer League",
    ],
    "Oceania — Women's Domestic Leagues": [
        "A-League Women", "New Zealand Women's National League",
    ],
}

WOMENS_CONTINENTAL_CLUB = {
    "Europe — Women's Continental Clubs": [
        "UEFA Champions League Women", "UEFA Europa Cup - Women",
    ],
    "Africa — Women's Continental Clubs": [
        "CAF Women's Champions League",
    ],
    "Asia — Women's Continental Clubs": [
        "AFC Women's Champions League",
    ],
    "Americas — Women's Continental Clubs": [
        "CONCACAF W Champions Cup", "CONMEBOL Libertadores Femenina",
    ],
    "World — Women's Club Competitions": [
        "FIFA Women Champions Cup", "International Champions Cup - Women",
    ],
}

WOMENS_INTERNATIONAL = {
    "Europe — Women's National Teams": [
        "UEFA Championship - Women", "UEFA Championship - Women - Qualification",
        "UEFA Nations League - Women", "UEFA U17 Championship - Women",
        "UEFA U19 Championship - Women",
    ],
    "Africa — Women's National Teams": [
        "Africa Cup of Nations - Women", "African Nations Championship - Women",
        "All Africa Games Women",
    ],
    "Asia — Women's National Teams": [
        "Asian Cup Women", "Asian Cup Women - Qualification",
        "Asian Games Women", "AFC U17 Asian Cup - Women",
        "AFC U20 Asian Cup - Women", "Asean Championship Women",
        "EAFF E-1 Football Championship - Women",
    ],
    "Americas — Women's National Teams": [
        "Copa America Femenina", "CONCACAF Gold Cup - Women",
        "CONCACAF Gold Cup - Qualification - Women",
        "CONCACAF Nations League - Women", "CONCACAF Women U17",
        "CONCACAF Women U20", "CONMEBOL Nations League Women",
        "CONMEBOL U20 Femenino", "CONMEBOL - U17 Femenino",
        "SheBelieves Cup",
    ],
    "Oceania — Women's National Teams": [
        "OFC Women's Nations Cup", "OFC U19 Championship - Women",
    ],
    "World — Women's National Teams": [
        "World Cup - Women", "World Cup - Women - Qualification Concacaf",
        "World Cup - Women - Qualification Europe", "World Cup - U20 - Women",
        "World Cup - U17 - Women", "Olympics Women",
        "Olympics Women - Qualification Asia", "Olympics Women - Qualification CAF",
        "Friendlies Women", "Olympics Women - Qualification",
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
    "Women’s Super League": {"Women’s Super League", "Women's Super League", "WSL"},
    "Women's Championship": {"Women's Championship", "Women Championship"},
    "UEFA Champions League Women": {"UEFA Champions League Women", "UEFA Women's Champions League"},
    "AFC Women's Champions League": {"AFC Women's Champions League", "AFC Women Champions League"},
    "CAF Women's Champions League": {"CAF Women's Champions League", "CAF Women Champions League"},
    "CONCACAF W Champions Cup": {"CONCACAF W Champions Cup", "CONCACAF Women's Champions Cup"},
    "CONMEBOL Libertadores Femenina": {"CONMEBOL Libertadores Femenina", "Copa Libertadores Femenina"},
    "World Cup - Women": {"World Cup - Women", "Women's World Cup", "FIFA Women's World Cup"},
    "Copa America Femenina": {"Copa America Femenina", "Copa América Femenina"},
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
def get_secret(name):
    """Read a secret from Streamlit secrets, then environment variables."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    if not value:
        value = os.getenv(name, "")
    return str(value).strip()


def get_api_key():
    return get_secret("API_FOOTBALL_KEY")


def send_telegram_message(bot_token, chat_id, message):
    """Send one message through the official Telegram Bot API."""
    if not bot_token or not chat_id:
        return False, "Telegram bot token or chat ID is missing."
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": message, "disable_web_page_preview": True},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        if not payload.get("ok"):
            return False, str(payload.get("description", "Telegram rejected the message."))
        return True, "Telegram message sent."
    except requests.RequestException as exc:
        return False, f"Telegram request failed: {exc}"
    except ValueError:
        return False, "Telegram returned an invalid response."


API_KEY = get_api_key()
TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = get_secret("TELEGRAM_CHAT_ID")


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



@st.cache_data(ttl=3600, show_spinner=False)
def get_standings(api_key, league_id, season):
    """Return team ID -> current competition-table rank, if supported."""
    if not api_key or not league_id or not season:
        return {}
    try:
        response = requests.get(
            f"{API_ROOT}/standings",
            headers={"x-apisports-key": api_key},
            params={"league": int(league_id), "season": int(season)},
            timeout=18,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors") or not payload.get("response"):
            return {}
        result = {}
        for league_obj in payload.get("response", []):
            groups = league_obj.get("league", {}).get("standings", []) or []
            for group in groups:
                for entry in group or []:
                    team_id = (entry.get("team") or {}).get("id")
                    rank = entry.get("rank")
                    if team_id is not None and rank is not None:
                        result[int(team_id)] = int(rank)
        return result
    except (requests.RequestException, ValueError, TypeError):
        return {}


def _extract_match_winner_odds(payload):
    """Extract a bookmaker's Home/Draw/Away odds from common API-Football shapes."""
    if not isinstance(payload, dict) or payload.get("errors"):
        return None
    for item in payload.get("response", []) or []:
        bookmakers = item.get("bookmakers") or item.get("odds") or []
        for bookmaker in bookmakers:
            bets = bookmaker.get("bets") or []
            for bet in bets:
                bet_name = normalize_name(bet.get("name", ""))
                if bet_name not in {"match winner", "1x2", "fulltime result", "winner"}:
                    continue
                values = {}
                for value in bet.get("values", []) or []:
                    label = normalize_name(value.get("value", ""))
                    odd = value.get("odd")
                    if label in {"home", "1"}:
                        values["Home"] = odd
                    elif label in {"draw", "x"}:
                        values["Draw"] = odd
                    elif label in {"away", "2"}:
                        values["Away"] = odd
                if values:
                    book_name = bookmaker.get("name", "Bookmaker")
                    formatted = " | ".join(f"{key}: {values.get(key, '—')}" for key in ("Home", "Draw", "Away"))
                    return f"{book_name}: {formatted}"
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_prematch_odds(api_key, fixture_id):
    """Fetch available pre-match odds for a fixture (not guaranteed to be true opening prices)."""
    if not api_key or not fixture_id:
        return "Unavailable"
    try:
        response = requests.get(
            f"{API_ROOT}/odds",
            headers={"x-apisports-key": api_key},
            params={"fixture": int(fixture_id)},
            timeout=18,
        )
        response.raise_for_status()
        value = _extract_match_winner_odds(response.json())
        return value or "Not supplied"
    except (requests.RequestException, ValueError, TypeError):
        return "Unavailable"


@st.cache_data(ttl=45, show_spinner=False)
def get_all_live_odds(api_key):
    """Fetch the live-odds feed once and index it by fixture ID."""
    if not api_key:
        return {}
    try:
        response = requests.get(
            f"{API_ROOT}/odds/live",
            headers={"x-apisports-key": api_key},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            return {}
        indexed = {}
        for item in payload.get("response", []) or []:
            fixture_id = (item.get("fixture") or {}).get("id")
            if fixture_id is None:
                fixture_id = item.get("fixture_id")
            if fixture_id is None:
                continue
            value = _extract_match_winner_odds({"response": [item]})
            if value:
                indexed[int(fixture_id)] = value
        return indexed
    except (requests.RequestException, ValueError, TypeError):
        return {}


COUNTRY_ALIASES = {
    "korea republic": "KOR", "south korea": "KOR", "north korea": "PRK",
    "iran": "IRN", "ir iran": "IRN", "ivory coast": "CIV", "cote d'ivoire": "CIV",
    "cape verde": "CPV", "cabo verde": "CPV", "turkiye": "TUR", "turkey": "TUR",
    "usa": "USA", "united states": "USA", "united states of america": "USA",
    "england": "ENG", "scotland": "SCO", "wales": "WAL", "northern ireland": "NIR",
    "hong kong": "HKG", "chinese taipei": "TPE", "bolivia": "BOL",
    "venezuela": "VEN", "tanzania": "TZA", "dr congo": "COD", "congo dr": "COD",
    "congo": "CGO", "russia": "RUS", "kosovo": "KVX", "palestine": "PLE",
    "moldova": "MDA", "laos": "LAO", "syria": "SYR", "brunei": "BRU",
    "vietnam": "VIE", "china": "CHN", "chinese pr": "CHN", "macau": "MAC",
    "curacao": "CUW", "aruba": "ARU", "kosovo": "KVX", "faroe islands": "FRO",
}


def country_iso3(country_name):
    name = normalize_name(country_name)
    if name in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[name]
    try:
        return pycountry.countries.lookup(str(country_name)).alpha_3
    except (LookupError, AttributeError):
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def get_fifa_ranking(country_name, gender):
    """Query FIFA's country ranking endpoint. gender is 'men' or 'women'."""
    iso3 = country_iso3(country_name)
    if not iso3:
        return "—"
    gender_id = 1 if gender == "men" else 2
    try:
        response = requests.get(
            f"{FIFA_API_ROOT}/{iso3}",
            params={"gender": gender_id, "language": "en"},
            headers={"User-Agent": "Mozilla/5.0 AwayRedCardMonitor/1.0"},
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        results = payload.get("Results") or payload.get("results") or []
        if not results:
            return "—"
        item = results[0]
        rank = item.get("Rank", item.get("rank"))
        points = item.get("DecimalTotalPoints", item.get("Points", item.get("points")))
        pub_date = item.get("PubDate", item.get("Date", item.get("date", "")))
        if rank is None:
            return "—"
        out = f"#{rank}"
        if points is not None:
            out += f" ({points} pts)"
        if pub_date:
            out += f" · {str(pub_date)[:10]}"
        return out
    except (requests.RequestException, ValueError, TypeError):
        return "—"

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
        "League ID": league.get("id"),
        "Season": league.get("season"),
        "Home Team ID": home.get("id"),
        "Away Team ID": away.get("id"),
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
        "Men's second-division domestic leagues",
        "Women's second-division domestic leagues",
        "Japan and South Korea domestic leagues",
        "Australia domestic leagues",
        "European continental clubs",
        "African continental clubs",
        "Asian continental clubs",
        "International national teams",
        "Women's domestic leagues",
        "Women's continental club competitions",
        "Women's international national teams",
    ],
    default=[
        "Domestic leagues",
        "Men's second-division domestic leagues",
        "Women's second-division domestic leagues",
        "Japan and South Korea domestic leagues",
        "Australia domestic leagues",
        "European continental clubs",
        "African continental clubs",
        "Asian continental clubs",
        "International national teams",
        "Women's domestic leagues",
        "Women's continental club competitions",
        "Women's international national teams",
    ],
)

selected_competitions = []

if "Men's second-division domestic leagues" in competition_groups:
    for competitions in MENS_SECOND_DIVISION.values():
        selected_competitions.extend(competitions)

if "Women's second-division domestic leagues" in competition_groups:
    for competitions in WOMENS_SECOND_DIVISION.values():
        selected_competitions.extend(competitions)

if "Japan and South Korea domestic leagues" in competition_groups:
    for competitions in JAPAN_KOREA_DOMESTIC.values():
        selected_competitions.extend(competitions)

if "Australia domestic leagues" in competition_groups:
    for competitions in AUSTRALIA_DOMESTIC.values():
        selected_competitions.extend(competitions)

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

if "Women's domestic leagues" in competition_groups:
    for competitions in WOMENS_DOMESTIC.values():
        selected_competitions.extend(competitions)

if "Women's continental club competitions" in competition_groups:
    for competitions in WOMENS_CONTINENTAL_CLUB.values():
        selected_competitions.extend(competitions)

if "Women's international national teams" in competition_groups:
    for competitions in WOMENS_INTERNATIONAL.values():
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

st.sidebar.subheader("📊 Odds and rankings")
show_odds = st.sidebar.checkbox(
    "Load starting/pre-match and live odds",
    value=False,
    help="Uses extra API requests for pre-match odds. True opening odds may not be available unless captured before kick-off.",
)
show_rankings = st.sidebar.checkbox(
    "Load domestic table ranks and national-team FIFA ranks",
    value=False,
    help="Standings are cached for one hour; FIFA rankings are cached for one day. Some competitions or country names may not return rankings.",
)

refresh_seconds = st.sidebar.selectbox(
    "Refresh interval",
    options=[15, 30, 60, 120],
    index=1,
    format_func=lambda x: f"{x} seconds",
)

st.sidebar.divider()
st.sidebar.subheader("📲 Telegram alerts")
telegram_ready = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)
telegram_alerts_enabled = st.sidebar.checkbox(
    "Send away-red-card alerts to Telegram",
    value=telegram_ready,
    disabled=not telegram_ready,
    help="Sends a message for an away-team red card in the selected competitions. Display-only minute and goal filters do not suppress Telegram alerts.",
)
if not telegram_ready:
    st.sidebar.caption("Add TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in Streamlit Secrets to enable alerts.")
elif st.sidebar.button("Send test Telegram message", use_container_width=True):
    ok, message = send_telegram_message(
        TELEGRAM_BOT_TOKEN,
        TELEGRAM_CHAT_ID,
        "✅ Away Red Card Monitor: Telegram connection test successful. Alerts are configured.",
    )
    if ok:
        st.sidebar.success(message)
    else:
        st.sidebar.error(message)

# ------------------------------------------------------------
# Main page
# ------------------------------------------------------------
st.title("🟥 Away Red Card Monitor")
st.caption(
    "Live football dashboard using API-Football. "
    "Includes men's and women's domestic leagues, selected second divisions, Japan and South Korea, "
    "Australian national/state competitions, continental clubs and international tournaments. "
    "Availability depends on API-Football coverage and season."
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

# Telegram notifications monitor selected competitions independently of the
# visual minute/goal filters, so those display filters do not hide red cards.
telegram_candidates_df = df.copy()

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

# Optional odds/ranking enrichment. Disabled by default to preserve API quota.
if show_rankings and not df.empty:
    with st.spinner("Loading current competition standings and national-team rankings..."):
        rank_maps = {}
        # A standings request is made once per unique competition/season and cached for an hour.
        unique_leagues = df[["League ID", "Season"]].dropna().drop_duplicates().head(20)
        for _, league_row in unique_leagues.iterrows():
            league_id = int(league_row["League ID"])
            season = int(league_row["Season"])
            rank_maps[(league_id, season)] = get_standings(API_KEY, league_id, season)

        home_ranks, away_ranks = [], []
        for _, row in df.iterrows():
            key = (int(row["League ID"]), int(row["Season"])) if pd.notna(row["League ID"]) and pd.notna(row["Season"]) else None
            ranks = rank_maps.get(key, {}) if key else {}
            home_ranks.append(ranks.get(int(row["Home Team ID"]), "—") if pd.notna(row["Home Team ID"]) else "—")
            away_ranks.append(ranks.get(int(row["Away Team ID"]), "—") if pd.notna(row["Away Team ID"]) else "—")
        df["Home Table Rank"] = home_ranks
        df["Away Table Rank"] = away_ranks

        international_names = []
        for group in list(INTERNATIONAL.values()) + list(WOMENS_INTERNATIONAL.values()):
            international_names.extend(group)
        international_name_set = names_for_selection(international_names)
        df["Home FIFA Rank"] = "—"
        df["Away FIFA Rank"] = "—"
        for idx, row in df.iterrows():
            if normalize_name(row["League"]) not in international_name_set:
                continue
            league_name = normalize_name(row["League"])
            is_womens = ("women" in league_name) or ("women" in normalize_name(row["Home Team"])) or ("women" in normalize_name(row["Away Team"]))
            gender = "women" if is_womens else "men"
            df.at[idx, "Home FIFA Rank"] = get_fifa_ranking(row["Home Team"], gender)
            df.at[idx, "Away FIFA Rank"] = get_fifa_ranking(row["Away Team"], gender)

if show_odds and not df.empty:
    with st.spinner("Loading available pre-match and live odds..."):
        live_odds_map = get_all_live_odds(API_KEY)
        # Keep pre-match calls bounded per refresh; results are cached for one hour.
        odds_indices = list(df.index[:15])
        df["Starting / Pre-match Odds"] = "Not loaded"
        df["Live Odds"] = df["Fixture ID"].map(lambda fixture_id: live_odds_map.get(int(fixture_id), "Not supplied") if pd.notna(fixture_id) else "Not supplied")
        for idx in odds_indices:
            fixture_id = df.at[idx, "Fixture ID"]
            df.at[idx, "Starting / Pre-match Odds"] = get_prematch_odds(API_KEY, int(fixture_id)) if pd.notna(fixture_id) else "Unavailable"
        if len(df) > len(odds_indices):
            st.caption("Pre-match odds are requested for the first 15 matches shown to limit API usage. Live odds use the provider's live feed.")

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
    display_columns = [
        "League", "League Country", "Home Team", "Away Team", "Score",
        "Minute", "Total Goals", "Away Red", "Away Red Count",
        "Away Red Details", "Status",
    ]
    if show_rankings:
        display_columns.extend(["Home Table Rank", "Away Table Rank", "Home FIFA Rank", "Away FIFA Rank"])
    if show_odds:
        display_columns.extend(["Starting / Pre-match Odds", "Live Odds"])
    display_df = df[[column for column in display_columns if column in df.columns]].copy()

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
    if show_odds:
        st.caption("Odds are provider-supplied snapshots and may be unavailable for some matches/bookmakers. The pre-match endpoint does not guarantee the first-ever opening price; exact opening odds require recording them before kick-off. Live odds can be suspended or missing.")
    if show_rankings:
        st.caption("Domestic table positions come from the selected competition's standings endpoint when supported. National-team FIFA ranks are retrieved separately from FIFA's ranking endpoint and may be unavailable for non-standard team names or unsupported responses.")

st.divider()
st.subheader("🚨 Away Red-Card Alerts")

red_df = df[df["Away Red"]].copy()

# Notify once per distinct away-red-card event during this Streamlit session.
# The key includes the fixture ID and card details, so a second red card in the
# same match can trigger a separate message.
if "telegram_sent_alert_keys" not in st.session_state:
    st.session_state["telegram_sent_alert_keys"] = set()

telegram_red_df = telegram_candidates_df[telegram_candidates_df["Away Red"]].copy()
if telegram_alerts_enabled and telegram_ready and not telegram_red_df.empty:
    for _, row in telegram_red_df.iterrows():
        alert_key = f"{row['Fixture ID']}|{row['Away Red Details']}"
        if alert_key in st.session_state["telegram_sent_alert_keys"]:
            continue

        message = (
            "🟥 AWAY TEAM RED CARD\n\n"
            f"Competition: {row['League']} ({row['League Country']})\n"
            f"Match: {row['Home Team']} vs {row['Away Team']}\n"
            f"Score: {row['Score']}\n"
            f"Minute: {row['Minute']}'\n"
            f"Card details: {row['Away Red Details']}\n"
            f"Total goals: {row['Total Goals']}\n\n"
            "Sent by Away Red Card Monitor"
        )
        ok, send_error = send_telegram_message(
            TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message
        )
        if ok:
            st.session_state["telegram_sent_alert_keys"].add(alert_key)
        else:
            st.warning(f"Telegram alert could not be sent: {send_error}")

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
