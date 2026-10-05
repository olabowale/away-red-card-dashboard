# Away Red Card Dashboard

This is the browser dashboard companion to the Telegram away-red-card
monitor.

## Install

    pip install -r requirements.txt

Set the API key:

Linux/macOS:
    export API_FOOTBALL_KEY="YOUR_API_KEY"

Windows PowerShell:
    $env:API_FOOTBALL_KEY="YOUR_API_KEY"

Run:

    streamlit run app.py

The browser will open the dashboard.

## Dashboard filters

- Leagues
- Minimum match minute
- Maximum total goals
- Low-score-only
- Away-red-only
- Refresh interval

## Recommended initial configuration

For the low-scoring match workflow:

    Minimum minute: 55
    Maximum total goals: 2
    Low-score-only: ON
    Away-red-only: OFF

Then turn Away-red-only ON when you want to see only matches where the
away team has already been dismissed.

## Important

This dashboard is an event-monitoring interface. It does not place bets
and does not guarantee that a data provider will capture every event
instantly or for every competition.
