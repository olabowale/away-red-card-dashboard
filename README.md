# Away Red Card Monitor — Streamlit Cloud Deployment

## Deploy

1. Upload `app.py` and `requirements.txt` to a GitHub repository.
2. Create a Streamlit Community Cloud app using `app.py` as the main file.
3. Open the app's **Settings → Secrets**.
4. Add:

```toml
API_FOOTBALL_KEY = "YOUR_API_FOOTBALL_KEY"
```

Do not commit the API key to GitHub.

The app reads the key from Streamlit Secrets and falls back to the
`API_FOOTBALL_KEY` environment variable for local use.
