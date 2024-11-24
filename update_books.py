import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re
from time import sleep

# Funktioner för extraktion och städning
def extract_pages(page_info):
    if page_info and isinstance(page_info, str):
        match = re.search(r'\d+\s*s', page_info)  # Matchar "271 s"
        if match:
            return match.group()  # Returnerar "271 s"
    return "Okänt"

def extract_year(date_issued):
    if date_issued and isinstance(date_issued, str):
        match = re.search(r'\d{4}', date_issued)  # Matchar "2022"
        if match:
            return match.group()  # Returnerar "2022"
    return "Okänt"

def clean_year(year):
    # Tar bort decimaler från år
    return str(int(float(year))) if pd.notna(year) else "Okänt"

def extract_keywords(record, namespace):
    # Extrahera alla <genre>-element
    genres = record.findall('.//mods:genre', namespaces=namespace)
    keywords = [genre.text for genre in genres if genre.text]
    return ", ".join(keywords) if keywords else "Okänt"

# Funktion för att söka efter bokinformation
def search_book(title, ignore_unwanted_keywords=False, attempt=1, max_attempts=3):
    base_url = "https://libris.kb.se/xsearch"
    query = f"tit:({title})"

    params = {
        'query': query,
        'format': 'mods',
        'n': 5  # Hämta upp till 5 alternativ
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        if 'records="0"' in response.content.decode():
            return None
        root = ET.fromstring(response.content)
        namespace = {'mods': 'http://www.loc.gov/mods/v3'}

        for record in root.findall('.//mods:mods', namespaces=namespace):
            title = record.find('.//mods:title', namespaces=namespace)
            creator = record.find('.//mods:name/mods:namePart', namespaces=namespace)
            pages = record.find('.//mods:extent', namespaces=namespace)
            date_issued = record.find('.//mods:dateIssued', namespaces=namespace)
            publisher = record.find('.//mods:publisher', namespaces=namespace)
            isbn = record.find('.//mods:identifier[@type="isbn"]', namespaces=namespace)
            keywords = extract_keywords(record, namespace)

            # Lista med oönskade nyckelord
            unwanted_keywords = ["E-böcker", "text och ljud", "organisationspress", 
                                 "videorecording", "ljudböcker", "TV-program", 
                                 "comic books", "graphic novels"]
            
            # Kontrollera oönskade nyckelord
            if ignore_unwanted_keywords and any(keyword in keywords for keyword in unwanted_keywords):
                print(f"Resultat innehåller oönskade nyckelord ({keywords}). Försöker igen...")
                if attempt < max_attempts:
                    return search_book(title, ignore_unwanted_keywords=True, attempt=attempt + 1, max_attempts=max_attempts)
                else:
                    print(f"Max försök uppnått för {title}.")
                    return None

            isbn_cleaned = isbn.text.split(" ")[0] if isbn is not None and isbn.text else "Okänt"

            return {
                'Titel': title.text if title is not None else "Okänd titel",
                'Författare': creator.text if creator is not None else "Ingen författare",
                'Antal sidor': extract_pages(pages.text if pages is not None else "Okänt"),
                'Utgivningsår (API)': extract_year(date_issued.text if date_issued is not None else "Okänt"),
                'Förlag': publisher.text if publisher is not None else "Okänt",
                'ISBN': isbn_cleaned,
                'Nyckelord': keywords
            }
        return None
    else:
        print(f"Fel vid API-förfrågan: {response.status_code}")
        return None

# Läs in och bearbeta CSV
input_file = 'bocker.csv'  # Byt till din fil
output_file = 'uppdaterade_bocker.csv'

books = pd.read_csv(input_file, sep=';', encoding='utf-8')

# Lista för att lagra resultaten
updated_books = []

# Iterera över varje bok
for index, row in books.iterrows():
    title = row['Titel']
    given_year = clean_year(row['Utgivningsår'])

    print(f"Söker: {title}")
    book_info = search_book(title)

    # Lägg till resultaten
    updated_books.append({
        'Titel': title,
        'Utgivningsår (Lista)': given_year,
        'Utgivningsår (API)': book_info.get('Utgivningsår (API)', 'Ej hittad') if book_info else 'Ej hittad',
        'Antal sidor': book_info.get('Antal sidor', 'Ej hittad') if book_info else 'Ej hittad',
        'Författare': book_info.get('Författare', 'Ej hittad') if book_info else 'Ej hittad',
        'Förlag': book_info.get('Förlag', 'Ej hittad') if book_info else 'Ej hittad',
        'ISBN': book_info.get('ISBN', 'Ej hittad') if book_info else 'Ej hittad',
        'Nyckelord': book_info.get('Nyckelord', 'Ej hittad') if book_info else 'Ej hittad',
        'Avvikande år': 'Ja' if book_info and given_year != book_info.get('Utgivningsår (API)', 'Ej hittad') else 'Nej'
    })

    # Undvik att spamma API:et
    sleep(0.5)

# Spara resultaten i en ny CSV-fil
output_df = pd.DataFrame(updated_books)
output_df.to_csv(output_file, sep=';', index=False, encoding='utf-8')

print(f"Resultaten har sparats i {output_file}")
