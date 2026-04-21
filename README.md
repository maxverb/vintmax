# Vintmax

Vinden van Vinted-listings waar "max" (of maximaal/maximum/maximal/maximize)
daadwerkelijk als los woord in titel of merknaam staat.

Twee manieren om te gebruiken:

## 1. Lokaal script

Zero-dependency Python, stdlib only.

```bash
python3 vintmax.py                       # 3 paginas zoeken op "max"
python3 vintmax.py --pages 10            # meer resultaten
python3 vintmax.py --query maxi          # andere zoekterm
python3 vintmax.py --html out.html       # klikbare HTML-galerij
python3 vintmax.py --json docs/data.json # JSON voor de webapp
python3 vintmax.py --no-filter           # alle ruwe resultaten, geen whole-word filter
```

## 2. Webapp op GitHub Pages

Statische site in `docs/`, data wordt ververst door een GitHub Action.

### Eenmalig opzetten

1. **Settings → Pages**: zet "Source" op **GitHub Actions**.
2. **Settings → Actions → General → Workflow permissions**: zet op
   **Read and write permissions** (nodig zodat de refresh-action `data.json`
   terug kan committen).
3. Ga naar **Actions → "Refresh Vinted data" → Run workflow** om de eerste
   dataset te genereren. Daarna draait 'ie elke dag om 07:00 UTC, en je kunt
   'm altijd handmatig triggeren met een andere query.
4. De "Deploy Pages"-workflow publiceert automatisch na elke commit in
   `docs/`.

### Gebruik

- Ga naar `https://<user>.github.io/vintmax/`.
- Filter binnen resultaten op tekst, maat en sorteer op prijs/titel.
- Voor een nieuwe zoekopdracht: Actions → Refresh → Run workflow → vul
  `query` in.

## Hoe het werkt

1. Script haalt `https://www.vinted.nl/` op om session-cookies te krijgen.
2. Roept `/api/v2/catalog/items?search_text=<query>` per pagina aan.
3. Filtert lokaal op whole-word match (`\bmax(imaal|imum|imize|imal)?\b`) zodat
   woorden als productcode-ruis geen false positives opleveren.
4. Schrijft JSON / HTML / terminal-output.

## Beperkingen

- Vinted's API is ongedocumenteerd en kan zonder waarschuwing wijzigen.
- Filtering gebeurt op titel + merknaam. De beschrijving zit niet in de
  zoekresultaten-response.
- GitHub Pages is statisch: live zoeken vanuit de browser kan niet door
  CORS, vandaar de Action-flow.
- Alleen vinted.nl; andere tweedehands-sites kunnen later als extra
  `SourceAdapter` toegevoegd worden.
