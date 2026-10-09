# Away Red Card Monitor — Expanded Men’s and Women’s Edition

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

The dashboard also includes selectable women's football competitions, separated from the men's/general catalogue:

### Women's domestic leagues
- Europe: Women's Super League, Women's Championship, Frauen-Bundesliga/Frauenliga, Spain's Primera División Femenina, France's Feminine Division 1, Italy's Serie A Women, Netherlands' Eredivisie Women, Scotland, Sweden, Norway, Denmark, Finland, Switzerland, Poland, Romania and other listed competitions.
- Africa: women's domestic competitions including South Africa's Super League Women; Nigeria's NWFL names are included where available in the API.
- Asia, Americas and Oceania: selected women's domestic leagues such as WK-League, NWSL, Liga MX Femenil and A-League Women.

### Women's continental club competitions
- Europe: UEFA Champions League Women and UEFA Europa Cup - Women.
- Africa: CAF Women's Champions League.
- Asia: AFC Women's Champions League.
- Americas: CONCACAF W Champions Cup and CONMEBOL Libertadores Femenina.
- World: FIFA Women Champions Cup and selected women's club invitationals.

### Women's international national teams
- Europe: UEFA Women's Championship, Nations League and youth competitions.
- Africa: Africa Cup of Nations - Women and other listed women's events.
- Asia: Asian Cup Women, Asian Games Women, youth events and regional championships.
- Americas: Copa America Femenina, CONCACAF Gold Cup - Women, CONCACAF women's youth events and SheBelieves Cup.
- World: Women's World Cup and qualifiers, U17/U20 World Cups, Olympics Women, and women's friendlies.

Use the three women's group options in the sidebar to include or exclude women's football independently. Competition names and coverage vary by season, and some listed competitions may not have live fixtures at a given time.

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
fixtures by competition name. Men's/general and women's competitions can be selected separately. This means the competition filter does not depend
on a hard-coded league-ID list and can accommodate API-Football naming changes
through the alias table in `app.py`.

API-Football's coverage catalogue should be consulted when adding further
competitions because coverage varies by competition and season.
