# Frågeassistent

En enkel webbaserad applikation byggd med FastAPI som låter användare registrera sig, logga in, ladda upp frågedokument (PDF eller text), få automatiska sammanfattningar och använda en AI-baserad metod för att besvara valda frågor ur dokumentet.

## Funktioner

- 👤 Skapa konto och logga in med JWT-baserad autentisering.
- 📄 Ladda upp PDF- eller textfiler som innehåller frågor.
- 📝 Automatisk sammanfattning och extrahering av frågor från dokumentet.
- 🤖 AI-driven frågesvar med hjälp av TF-IDF och semantisk likhet.
- 🖥️ En enkel webbklient (HTML/JS) som hanterar hela flödet.

## Kom igång

### Förutsättningar

- Python 3.11+
- Virtuell miljö (rekommenderas)

### Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install --upgrade pip
pip install -r requirements.txt
```

> 💡 **Obs!** I den här utvecklingsmiljön är utgående nätverkstrafik spärrad. Det gör att `pip install -r requirements.txt` misslyckas med felmeddelandet `ProxyError: Tunnel connection failed: 403 Forbidden`. För att installera beroenden behöver du antingen:
>
> - Köra projektet på en maskin med internetåtkomst, eller
> - Tillhandahålla nedladdade Python-hjul/arkiv lokalt (t.ex. via en intern PyPI-spegel) och peka `pip` mot dessa med `--find-links` eller liknande.

### Starta utvecklingsservern

```bash
uvicorn app.main:app --reload
```

Applikationen blir då tillgänglig på `http://127.0.0.1:8000/`.

### Användning

1. Öppna webbsidan och registrera ett konto.
2. Logga in för att få en token (hanteras automatiskt av front-end).
3. Ladda upp ett dokument (PDF eller textfil). Systemet skapar en sammanfattning och extraherar frågor.
4. Välj en fråga och klicka på **Generera svar** för att få ett AI-svar baserat på dokumentinnehållet.

### Databas

Projektet använder SQLite (`app.db`) som lagras i projektroten. Tabellen skapas automatiskt vid uppstart.

## Testning

```bash
python -m compileall app
```

Kommandon som kräver externa paket (t.ex. `pytest` eller lintingverktyg) förutsätter att du först installerat beroendena enligt beskrivningen ovan.

### Vidare utveckling

- Byt ut den enklare TF-IDF-baserade svarsmotorn mot en större språkmodell.
- Lägg till filhistorik och versionering.
- Skicka e-postverifiering eller multifaktorautentisering.

## Licens

MIT
