# Away Red Card Monitor — Men's and Women's Football + Telegram Alerts

A Streamlit dashboard that monitors API-Football live fixtures and filters competitions by name. It includes selected men's and women's domestic leagues, continental club competitions, and international tournaments. Competition coverage depends on the API-Football plan and season.

## Files
- `app.py` — dashboard
- `requirements.txt` — Python dependencies

## 1. Configure API-Football

Get an API key from API-Football and add it to Streamlit Community Cloud → your app → Settings → Secrets:

```toml
API_FOOTBALL_KEY = "YOUR_API_FOOTBALL_KEY"
```

## 2. Create a Telegram bot

1. Open Telegram and search for `@BotFather`.
2. Send `/newbot` and follow the prompts.
3. Copy the bot token. Keep it private.
4. Open your new bot and press **Start** or send `/start`.
5. In a browser, open `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates` (replace the placeholder with your token).
6. In the JSON response, find `message` → `chat` → `id`. This is your personal chat ID. For a group, add the bot to the group and retrieve that group's chat ID.

If `getUpdates` returns no messages, send `/start` to the bot and refresh the URL. Do not share the URL because it contains your bot token.

## 3. Add Telegram secrets

In Streamlit Community Cloud, open your app's **Settings → Secrets** and add these alongside your API-Football key:

```toml
API_FOOTBALL_KEY = "YOUR_API_FOOTBALL_KEY"
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"
```

Save the secrets. Do not put tokens in `app.py` or commit them to GitHub.

## 4. Enable and test alerts

1. Reload the dashboard after saving secrets.
2. In the sidebar, find **Telegram alerts**.
3. Confirm **Send away-red-card alerts to Telegram** is enabled.
4. Click **Send test Telegram message**. A successful setup sends a test message to the configured chat.
5. When a red card is detected for the away team in one of the selected competitions, the dashboard sends a Telegram alert containing the competition, teams, score, minute, and card details. The sidebar's minimum-minute and maximum-goal filters affect the table, but do not suppress Telegram notifications.

The app suppresses duplicate alerts for the same card during the current Streamlit session. If the app/session restarts, an alert already seen may be sent again; durable cross-restart deduplication requires a persistent database.

## Important monitoring limitations

- The dashboard polls the live fixtures feed when it reruns. Alerts are not a guaranteed 24/7 service, and Streamlit Community Cloud can sleep or restart apps.
- For reliable always-on alerts, run the polling/notification worker separately on an always-on service or VPS, and use Streamlit for the dashboard.
- Alerts are based on competitions and match filters currently selected in the sidebar.
- API-Football coverage, event availability, and rate limits depend on the API plan.

## Run locally

Install dependencies:

```bash
pip install -r requirements.txt
```

Set environment variables before starting the app:

```text
API_FOOTBALL_KEY=your_api_football_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

Then run:

```bash
streamlit run app.py
```
