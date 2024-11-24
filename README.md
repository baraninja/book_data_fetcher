# Bokdatainsamlare med Libris API

Det här skriptet används för att samla in information om böcker från Libris API baserat på en lista med boktitlar och utgivningsår. Informationen kompletteras med data som antal sidor, författare, förlag, ISBN och nyckelord (t.ex. genre).

## Funktionalitet

1. Läser in en CSV-fil med boktitlar och utgivningsår.
2. Söker efter varje bok i Libris API.
3. Hämtar och strukturerar information från API:et, inklusive:
   - Titel
   - Författare
   - Antal sidor
   - Utgivningsår (från API)
   - Förlag
   - ISBN
   - Nyckelord (t.ex. genre)
4. Ignorerar poster som innehåller specifika oönskade nyckelord (t.ex. "E-böcker", "ljudböcker").
5. Gör flera försök om resultaten innehåller oönskade nyckelord.
6. Skapar en ny CSV-fil med samlad information och markeringar för avvikande utgivningsår.

---

## Installationsanvisningar

1. **Krav**:
   - Python 3.7 eller senare
   - Bibliotek: `requests`, `pandas`, `xml.etree.ElementTree`

   Installera nödvändiga bibliotek:
   ```bash
   pip install requests pandas
   ```

2. **Strukturera din data**:
   - Skapa en CSV-fil (t.ex. `bocker.csv`) med följande kolumner:
     ```csv
     Titel;Utgivningsår
     Akrobaten;2022
     Aldrig mer;2018
     All denna vrede;2021
     ```

3. **Kör skriptet**:
   - Kör Python-skriptet:
     ```bash
     python update_books.py
     ```

4. **Output**:
   - En ny CSV-fil (`uppdaterade_bocker.csv`) genereras med följande kolumner:
     ```csv
     Titel;Utgivningsår (Lista);Utgivningsår (API);Antal sidor;Författare;Förlag;ISBN;Nyckelord;Avvikande år
     ```

---

## Filbeskrivning

### `update_books.py`
Det huvudsakliga skriptet som:
1. Läser in boklistan.
2. Söker efter information i Libris API.
3. Ignorerar poster baserat på oönskade nyckelord.
4. Skriver ut resultaten till en CSV-fil.

---

## Hur fungerar processen?

1. **Inläsning av boklista**:
   - Skriptet läser in CSV-filen med titlar och utgivningsår.
   - Decimaler i "Utgivningsår" tas bort för renare representation (t.ex. `2022.0` → `2022`).

2. **API-förfrågningar**:
   - För varje titel görs en sökning i Libris API.
   - Data från API:et struktureras och analyseras.

3. **Ignorering av oönskade resultat**:
   - Resultat som innehåller nyckelord som "E-böcker", "ljudböcker", etc., ignoreras.
   - Skriptet försöker flera gånger (upp till tre) att hitta ett resultat utan oönskade nyckelord.

4. **Generering av ny CSV-fil**:
   - Data skrivs till en ny CSV-fil med kompletterad information.

---

## Anpassning och utveckling

### Lägg till fler nyckelord att ignorera
För att lägga till fler oönskade nyckelord:
1. Öppna skriptet.
2. Hitta listan över nyckelord i funktionen `search_book`:
   ```python
   unwanted_keywords = ["E-böcker", "text och ljud", "organisationspress", 
                        "videorecording", "ljudböcker", "TV-program", 
                        "comic books", "graphic novels"]
   ```
3. Lägg till fler nyckelord i listan, separerade med kommatecken.

### Ändra max antal försök
Om du vill öka antalet försök att ignorera oönskade resultat:
1. Ändra parametern `max_attempts` i funktionen `search_book`:
   ```python
   search_book(title, ignore_unwanted_keywords=True, attempt=attempt + 1, max_attempts=5)
   ```

### Utöka funktionalitet
- **Fler datafält**:
  Lägg till fler fält från API:et genom att anpassa hur data hämtas i `search_book`.
- **Integration med andra API:er**:
  Lägg till stöd för andra bokdatabaser (t.ex. Goodreads) för att komplettera datan.

---

## Exempel på körning

### Input
```csv
Titel;Utgivningsår
Akrobaten;2022
Aldrig mer;2018
All denna vrede;2021
```

### Output
```csv
Titel;Utgivningsår (Lista);Utgivningsår (API);Antal sidor;Författare;Förlag;ISBN;Nyckelord;Avvikande år
Akrobaten;2022;2022;271 s;Sundkvist, Anders;Modernista;9789180237871;Deckare, Roman;Nej
Aldrig mer;2018;2018;430 s;Larsson, Sara;Norstedts;9789113082738;Roman;Nej
All denna vrede;2021;2021;407 s;Hunter, Cara;Louise Bäckelin förlag;9789177992530;novel, Deckare, Romaner;Nej
```

---

## Kontakt

Om du har frågor eller förslag, vänligen kontakta anders.barane@gmail.com.
