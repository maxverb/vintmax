# Vintmax

Quick-and-dirty Python script dat Vinted doorzoekt op listings waar "max" (of
maximaal/maximum/maximize/maximal) daadwerkelijk als los woord in de titel of
merknaam voorkomt. Geen dependencies — alleen Python 3.9+.

## Gebruik

```bash
python3 vintmax.py                       # 3 pagina's zoeken op "max"
python3 vintmax.py --pages 10            # meer resultaten scannen
python3 vintmax.py --query maxi          # andere zoekterm
python3 vintmax.py --html out.html       # klikbare HTML met foto's
python3 vintmax.py --no-filter           # alle ruwe resultaten, geen whole-word filter
```

## Hoe het werkt

1. Haalt eerst `https://www.vinted.nl/` op om session-cookies binnen te halen.
2. Roept `/api/v2/catalog/items` aan met `search_text=<query>` per pagina.
3. Filtert lokaal op whole-word match (`\bmax(imaal|imum|imize|imal)?\b`) zodat
   woorden als "maximize" of productcodes geen ruis geven.
4. Print naar terminal of schrijft een simpele HTML-galerij.

## Beperkingen

- Vinted's API is ongedocumenteerd; als ze 'm wijzigen moet je dit script
  bijwerken.
- Filtering gebeurt op titel + merk. Beschrijvingstekst komt niet in de
  zoekresultaten-response — daarvoor zou je per item `/api/v2/items/<id>` moeten
  aanroepen (nog niet ingebouwd; makkelijk toe te voegen als je er tegenaan
  loopt).
- Alleen vinted.nl; andere sites zitten er nog niet in.
