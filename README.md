# Bokdatainsamlare med Libris API

Ett robust Python-skript för att samla in och validera bokinformation från Libris API. Skriptet hanterar duplicerade poster, filtrerar oönskade medietyper och inkluderar omfattande felhantering och loggning.

## Funktionalitet

1. **Datainsamling**:
   - Läser in CSV-fil med boktitlar och utgivningsår
   - Söker i Libris API med smart återförsökslogik
   - Validerar och strukturerar resultaten

2. **Databehandling**:
   - Automatisk dubbletthantering
   - Smart textrensnig och standardisering
   - Validering av årtal och ISBN
   - Omfattande filtrering av oönskade medietyper

3. **Resultat**:
   - Genererar strukturerad CSV med komplett bokinformation
   - Skapar detaljerade loggfiler för felsökning
   - Ger statistik över körningen

4. **Felhantering**:
   - Robust API-felhantering med exponentiell backoff
   - Validering av all indata och utdata
   - Omfattande loggning för felsökning

## Installation

### Systemkrav
- Python 3.7 eller senare
- pip (Python package manager)

### Installera beroenden
```bash
pip install requests pandas
```

### Konfigurera projektet
1. Klona eller ladda ner repository
2. Skapa en `logs`-mapp i projektmappen
3. Placera din indata-CSV i projektmappen

## Användning

### Förbereda indata
Skapa en CSV-fil (`bocker.csv`) med följande struktur:
```csv
Titel;Utgivningsår
Akrobaten;2022
Aldrig mer;2018
```

### Köra skriptet
```bash
python book_search.py
```

### Resultat
Skriptet genererar:
1. `uppdaterade_bocker.csv` med all insamlad data
2. Loggfil i `logs`-mappen med detaljerad körningsinformation
3. Statistik över körningen i konsolen

## Utdataformat

### CSV-struktur
```csv
Titel;Utgivningsår (Lista);Utgivningsår (API);Antal sidor;Författare;Förlag;ISBN;Nyckelord;Avvikande år
```

### Fältbeskrivningar
- **Titel**: Bokens titel
- **Utgivningsår (Lista)**: Ursprungligt år från indatan
- **Utgivningsår (API)**: År från Libris
- **Antal sidor**: Sidantal i format "XXX s"
- **Författare**: Författarens namn
- **Förlag**: Utgivande förlag
- **ISBN**: Rensat och validerat ISBN
- **Nyckelord**: Genre och kategorier
- **Avvikande år**: "Ja"/"Nej" beroende på om årtalen matchar

## Anpassning

### Lägga till filtreringsregler
Redigera `unwanted_keywords`-listan i skriptet:
```python
unwanted_keywords = [
    "e-böcker", "e-bok",
    "ljudböcker", "ljudbok",
    # Lägg till fler nyckelord här
]
```

### Justera API-parametrar
Ändra sökparametrar i `search_book`-funktionen:
```python
params = {
    'query': query,
    'format': 'mods',
    'n': 10  # Antal resultat att hämta
}
```

### Konfigurera loggning
Anpassa loggnivå och format i huvudskriptet:
```python
logging.basicConfig(
    level=logging.INFO,  # Ändra till DEBUG för mer detaljerad loggning
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

## Felhantering

Skriptet hanterar flera typer av fel:
- API-timeout och nätverksfel
- Ogiltig indata
- Dubbletter och inkonsistent data
- Ogiltiga årtal och ISBN

Vid fel:
1. Försöker igen med exponentiell backoff
2. Loggar felet med detaljer
3. Fortsätter med nästa post om möjligt

## Loggning

### Loggfiler
- Skapas i `logs`-mappen
- Namnges med tidsstämpel
- Innehåller detaljerad information om:
  - API-anrop
  - Filterresultat
  - Valideringsresultat
  - Fel och varningar

### Statistik
Efter körning visas:
- Totalt antal processerade böcker
- Antal ej hittade böcker
- Antal böcker med avvikande år
- Antal hanterade dubbletter

## Prestanda och begränsningar

- Väntar 0.5 sekunder mellan API-anrop
- Ökar väntetid exponentiellt vid fel
- Begränsar antal återförsök per bok
- Hanterar upp till 10 resultat per sökning

## Utveckling och bidrag

Förslag på förbättringar välkomnas! Några idéer:
- Parallell processering av API-anrop
- Integration med andra bokdatabaser
- GUI för enklare användning
- Export till andra format

## Kontakt

Vid frågor eller problem, kontakta:
- E-post: anders.barane@gmail.com
