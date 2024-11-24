import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re
from time import sleep

# Funktioner för extraktion och städning
def extract_pages(page_info):
    if page_info and isinstance(page_info, str):
        match = re.search(r'\d+\s*s', page_info)
        if match:
            return match.group()
    return "Okänt"

def extract_year(date_issued):
    if date_issued and isinstance(date_issued, str):
        match = re.search(r'\d{4}', date_issued)
        if match:
            return match.group()
    return "Okänt"

def clean_year(year):
    return str(int(float(year))) if pd.notna(year) else "Okänt"

def extract_keywords(record, namespace):
    genres = record.findall('.//mods:genre', namespaces=namespace)
    keywords = [genre.text for genre in genres if genre.text]
    return ", ".join(keywords) if keywords else "Okänt"

def should_skip_record(keywords, unwanted_keywords):
    """
    Kontrollerar om en post ska hoppas över baserat på dess nyckelord
    """
    keywords_lower = keywords.lower()
    return any(keyword in keywords_lower for keyword in unwanted_keywords)

def search_book(title, attempt=1, max_attempts=5):
    base_url = "https://libris.kb.se/xsearch"
    query = f"tit:({title})"
    
    # Lista med oönskade nyckelord (skiftlägesokänslig)
    unwanted_keywords = [
        "e-böcker", "text och ljud", "video dvd", "organisationspress",
        "videorecording", "ljudböcker", "tv-program", "comic books",
        "graphic novels", "punktskriftsböcker", "talböcker", "photobooks"
    ]
    unwanted_keywords = [keyword.lower() for keyword in unwanted_keywords]

    params = {
        'query': query,
        'format': 'mods',
        'n': 10  # Ökat antal resultat för att ha fler att filtrera bland
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        if 'records="0"' in response.content.decode():
            print(f"Inga resultat hittades för: {title}")
            return None
            
        root = ET.fromstring(response.content)
        namespace = {'mods': 'http://www.loc.gov/mods/v3'}
        
        # Gå igenom alla poster och hitta den första som inte har oönskade nyckelord
        for record in root.findall('.//mods:mods', namespaces=namespace):
            keywords = extract_keywords(record, namespace)
            
            # Hoppa över denna post om den innehåller oönskade nyckelord
            if should_skip_record(keywords, unwanted_keywords):
                print(f"Hoppar över resultat för '{title}' pga oönskade nyckelord: {keywords}")
                continue
                
            # Om vi kommer hit har vi hittat en giltig post
            title_elem = record.find('.//mods:title', namespaces=namespace)
            creator = record.find('.//mods:name/mods:namePart', namespaces=namespace)
            pages = record.find('.//mods:extent', namespaces=namespace)
            date_issued = record.find('.//mods:dateIssued', namespaces=namespace)
            publisher = record.find('.//mods:publisher', namespaces=namespace)
            isbn = record.find('.//mods:identifier[@type="isbn"]', namespaces=namespace)
            
            isbn_cleaned = isbn.text.split(" ")[0] if isbn is not None and isbn.text else "Okänt"
            
            return {
                'Titel': title_elem.text if title_elem is not None else "Okänd titel",
                'Författare': creator.text if creator is not None else "Ingen författare",
                'Antal sidor': extract_pages(pages.text if pages is not None else "Okänt"),
                'Utgivningsår (API)': extract_year(date_issued.text if date_issued is not None else "Okänt"),
                'Förlag': publisher.text if publisher is not None else "Okänt",
                'ISBN': isbn_cleaned,
                'Nyckelord': keywords
            }
            
        # Om vi har gått igenom alla poster utan att hitta en giltig och har försök kvar
        if attempt < max_attempts:
            print(f"Inga giltiga resultat hittades för '{title}', försöker igen... ({attempt}/{max_attempts})")
            sleep(1)  # Vänta lite längre mellan återförsök
            return search_book(title, attempt=attempt + 1, max_attempts=max_attempts)
        else:
            print(f"Max antal försök uppnått för '{title}', inga giltiga resultat hittades")
            return None
            
    except requests.RequestException as e:
        print(f"Fel vid API-förfrågan för '{title}': {e}")
        if attempt < max_attempts:
            print(f"Försöker igen... ({attempt}/{max_attempts})")
            sleep(2)  # Längre väntetid vid fel
            return search_book(title, attempt=attempt + 1, max_attempts=max_attempts)
        return None

# Huvudprogram
def main():
    input_file = 'bocker.csv'
    output_file = 'uppdaterade_bocker.csv'
    
    try:
        books = pd.read_csv(input_file, sep=';', encoding='utf-8')
        updated_books = []
        
        for index, row in books.iterrows():
            title = row['Titel']
            given_year = clean_year(row['Utgivningsår'])
            
            print(f"\nSöker ({index + 1}/{len(books)}): {title}")
            book_info = search_book(title)
            
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
            
            sleep(0.5)
        
        output_df = pd.DataFrame(updated_books)
        output_df.to_csv(output_file, sep=';', index=False, encoding='utf-8')
        print(f"\nResultaten har sparats i {output_file}")
        
    except Exception as e:
        print(f"Ett fel uppstod: {e}")

if __name__ == "__main__":
    main()
