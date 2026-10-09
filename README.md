# Away Red Card Monitor — Expanded Competition Edition

This Streamlit dashboard monitors live football matches from API-Football.

## Competition coverage

The filter now includes:

### European continental clubs
- UEFA Champions League
- UEFA Europa League
- UEFA Europa Conference League
- UEFA Super Cup
- UEFA Youth League

### African continental clubs
- CAF Champions League
- CAF Confederation Cup
- CAF Super Cup
- African Football League
- CECAFA Club Cup
- COSAFA Cup
- Arab Club Champions Cup

### Asian continental clubs
- AFC Champions League Elite
- AFC Champions League Two
- AFC Challenge League
- AFC Super Cup
- AFC Cup
- ASEAN Club Championship
- AGCFF Gulf Champions League

### International national-team competitions
- World Cup and qualifying competitions
- UEFA European Championship and qualifiers
- UEFA Nations League
- Africa Cup of Nations and qualifiers
- African Nations Championship
- Asian Cup and qualifiers
- Copa America
- CONCACAF Gold Cup
- CONCACAF Nations League
- OFC Nations Cup
- Arab Cup
- Gulf Cup
- ASEAN Championship
- other selected international competitions

The dashboard also retains the previously included European domestic leagues.

## API key

For Streamlit Community Cloud, open:

**App Settings → Secrets**

and add:

```toml
API_FOOTBALL_KEY = "YOUR_API_FOOTBALL_KEY"
```

Do NOT commit the API key to GitHub.

## Important

The dashboard uses the live API-Football fixture feed and filters the returned
fixtures by competition name. This means the competition filter does not depend
on a hard-coded league-ID list and can accommodate API-Football naming changes
through the alias table in `app.py`.

API-Football's coverage catalogue should be consulted when adding further
competitions because coverage varies by competition and season.
