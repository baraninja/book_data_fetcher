# Bokdatainsamlare med Libris API

Ett robust Python-skript för att samla in och validera bokinformation från Libris API. Skriptet är särskilt utformat för att hämta information om tryckta böcker genom att filtrera bort andra medietyper och format.

## Funktionalitet

1. **Datainsamling**:
   - Läser in CSV-fil med boktitlar och utgivningsår
   - Söker i Libris API med smart återförsökslogik
   - Säkerställer att endast tryckta böcker (typeOfResource="text") inkluderas

2. **Databehandling**:
   - Automatisk dubbletthantering
   - Smart textrensnig och standardisering
   - Validering av årtal och ISBN
   - Omfattande filtrering av oönskade medietyper (e-böcker, ljudböcker, etc.)

3. **Validering och Filtrering**:
   - Verifierar att posten är en tryckt bok
   - Filtrerar bort e-böcker, ljudböcker, film etc.
   - Kontrollerar årtalsöverensstämmelse

4. **Felhantering och Loggning**:
   - Robust API-felhantering med exponentiell backoff
   - Detaljerad loggning för felsökning
   - Statistik över körningen

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
Titel;Utgivningsår (Lista);Utgivningsår (API);Antal sidor;Författare;Förlag;ISBN;Avvikande år
```

### Fältbeskrivningar
- **Titel**: Bokens titel
- **Utgivningsår (Lista)**: Ursprungligt år från indatan
- **Utgivningsår (API)**: År från Libris
- **Antal sidor**: Sidantal i format "XXX s"
- **Författare**: Författarens namn
- **Förlag**: Utgivande förlag
- **ISBN**: Rensat och validerat ISBN
- **Avvikande år**: "Ja"/"Nej" beroende på om årtalen matchar

## Filtreringskriterier

Skriptet använder flera metoder för att identifiera och filtrera bort icke-bokposter:

1. **TypeOfResource-kontroll**:
   - Accepterar endast poster med typeOfResource="text"

2. **Format- och medietypsfiltrering**:
   Filtrerar bort poster som innehåller nyckelord som:
   - E-böcker och digitala format
   - Ljudböcker och ljudinspelningar
   - Film och video
   - Tidskrifter och periodika
   - Läromedel och faktaböcker
   - Musikrelaterat material
   - Diverse andra format (kartor, utställningskataloger, etc.)

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
- Innehåller information om:
  - API-anrop och sökningar
  - Filterresultat
  - Valideringsresultat
  - Fel och varningar

### Statistik
Efter körning visas:
- Totalt antal processerade böcker
- Antal ej hittade böcker
- Antal böcker med avvikande år
- Antal hanterade dubbletter

## Prestanda

- Väntar 0.5 sekunder mellan API-anrop
- Ökar väntetid exponentiellt vid fel
- Begränsar antal återförsök per bok
- Möjlighet att använda år i sökningen för bättre träffar

## Kontakt

Vid frågor eller problem, kontakta:
- E-post: anders.barane@gmail.com
