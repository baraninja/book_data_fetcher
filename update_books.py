import requests
import pandas as pd
import xml.etree.ElementTree as ET
import re
from time import sleep
import logging
from datetime import datetime
import os

# Konfigurera loggning
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'{log_directory}/book_search_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

class ValidationError(Exception):
    """Custom exception för valideringsfel"""
    pass

def clean_text(text):
    """
    Rensa och standardisera text
    """
    if pd.isna(text) or not text:
        return None
    # Ta bort specialtecken och överflödiga mellanslag
    cleaned = re.sub(r'[^\w\såäöÅÄÖ]', ' ', str(text))
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()

def validate_year(year_str):
    """
    Validera att året är rimligt
    """
    try:
        if year_str and year_str.isdigit():
            year = int(year_str)
            current_year = datetime.now().year
            if 1800 <= year <= current_year:
                return True
            else:
                logging.warning(f"Ogiltigt år: {year}")
                return False
    except (ValueError, TypeError):
        return False
    return False

def extract_pages(page_info):
    """
    Extrahera sidantal från textstring
    """
    if page_info and isinstance(page_info, str):
        # Matcha olika sidformater (t.ex. "271 s", "271s", "271 sidor")
        match = re.search(r'(\d+)\s*s(?:idor)?', page_info)
        if match:
            return f"{match.group(1)} s"
    return "Okänt"

def extract_year(date_issued):
    """
    Extrahera år från datumstring
    """
    if date_issued and isinstance(date_issued, str):
        match = re.search(r'\d{4}', date_issued)
        if match:
            year = match.group()
            if validate_year(year):
                return year
    return "Okänt"

def clean_year(year):
    """
    Standardisera årsformat
    """
    try:
        if pd.notna(year) and str(year).replace('.', '').isdigit():
            year_int = int(float(year))
            if validate_year(str(year_int)):
                return str(year_int)
    except (ValueError, TypeError):
        pass
    return "Okänt"

def extract_keywords(record, namespace):
    """
    Extrahera och rensa nyckelord från XML
    """
    genres = record.findall('.//mods:genre', namespaces=namespace)
    keywords = [genre.text.strip() for genre in genres if genre.text]
    return ", ".join(keywords) if keywords else "Okänt"

def should_skip_record(keywords, unwanted_keywords):
    """
    Kontrollera om en post ska filtreras bort baserat på nyckelord
    """
    if not keywords:
        return False
        
    keywords_lower = keywords.lower()
    
    # Kontrollera exakta matchningar
    for keyword in unwanted_keywords:
        if keyword in keywords_lower:
            logging.info(f"Filtrerar bort post med nyckelord: {keyword}")
            return True
            
    return False

def clean_isbn(isbn_text):
    """
    Rensa och validera ISBN
    """
    if not isbn_text or isbn_text == "Okänt":
        return "Okänt"
        
    # Ta endast första ISBN om det finns flera
    isbn = isbn_text.split()[0]
    
    # Ta bort alla icke-alfanumeriska tecken
    isbn = re.sub(r'[^0-9X]', '', isbn.upper())
    
    # Validera längd (ISBN-10 eller ISBN-13)
    if len(isbn) not in [10, 13]:
        return "Okänt"
        
    return isbn

def search_book(title, attempt=1, max_attempts=5):
    """
    Sök efter bok med förbättrad felhantering och filtrering
    """
    if not title or pd.isna(title):
        logging.warning("Tomt titelfält, hoppar över")
        return None
        
    base_url = "https://libris.kb.se/xsearch"
    cleaned_title = clean_text(title)
    
    if not cleaned_title:
        logging.warning(f"Ogiltig titel efter rensning: {title}")
        return None
        
    query = f"tit:({cleaned_title})"
    
    params = {
        'query': query,
        'format': 'mods',
        'n': 10  # Ökat antal resultat för bättre filtrering
    }
    
    # Lista över oönskade nyckelord (skiftlägesokänslig)
    unwanted_keywords = [
        "e-böcker", "e-bok", "text och ljud", "video dvd", "organisationspress",
        "videorecording", "ljudböcker", "ljudbok", "tv-program", "comic books",
        "graphic novels", "punktskriftsböcker", "talböcker", "photobooks",
        "periodical", "tidskrift", "tidning", "film", "motion picture",
        "daisy", "utställningskataloger", "kartor", "radio", "television",
        "storstilsbok", "lättläst", "läromedel", "seriealbum", "faktabok"
    ]
    unwanted_keywords = [keyword.lower() for keyword in unwanted_keywords]

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        
        if 'records="0"' in response.content.decode():
            logging.info(f"Inga resultat för: {title}")
            return None
            
        root = ET.fromstring(response.content)
        namespace = {'mods': 'http://www.loc.gov/mods/v3'}
        
        # Gå igenom alla poster och hitta första giltiga
        for record in root.findall('.//mods:mods', namespaces=namespace):
            keywords = extract_keywords(record, namespace)
            
            if should_skip_record(keywords, unwanted_keywords):
                continue
                
            title_elem = record.find('.//mods:title', namespaces=namespace)
            creator = record.find('.//mods:name/mods:namePart', namespaces=namespace)
            pages = record.find('.//mods:extent', namespaces=namespace)
            date_issued = record.find('.//mods:dateIssued', namespaces=namespace)
            publisher = record.find('.//mods:publisher', namespaces=namespace)
            isbn = record.find('.//mods:identifier[@type="isbn"]', namespaces=namespace)
            
            result = {
                'Titel': clean_text(title_elem.text) if title_elem is not None else "Okänd titel",
                'Författare': clean_text(creator.text) if creator is not None else "Ingen författare",
                'Antal sidor': extract_pages(pages.text if pages is not None else "Okänt"),
                'Utgivningsår (API)': extract_year(date_issued.text if date_issued is not None else "Okänt"),
                'Förlag': clean_text(publisher.text) if publisher is not None else "Okänt",
                'ISBN': clean_isbn(isbn.text if isbn is not None else "Okänt"),
                'Nyckelord': keywords
            }
            
            # Extra validering av resultatet
            if result['Utgivningsår (API)'] == "Okänt" and attempt < max_attempts:
                logging.warning(f"Ogiltig årtal för {title}, försöker igen")
                sleep(1)
                continue
                
            return result
            
        # Om vi inte hittat någon giltig post och har försök kvar
        if attempt < max_attempts:
            logging.info(f"Inga giltiga resultat för '{title}', försöker igen... ({attempt}/{max_attempts})")
            sleep(1)
            return search_book(title, attempt=attempt + 1, max_attempts=max_attempts)
        else:
            logging.warning(f"Max antal försök uppnått för '{title}'")
            return None
            
    except requests.RequestException as e:
        logging.error(f"API-fel för '{title}': {e}")
        if attempt < max_attempts:
            sleep(2 * attempt)  # Exponentiell backoff
            return search_book(title, attempt=attempt + 1, max_attempts=max_attempts)
        return None

def main():
    """
    Huvudfunktion för programmet
    """
    input_file = 'bocker.csv'
    output_file = 'uppdaterade_bocker.csv'
    
    try:
        logging.info(f"Läser in {input_file}")
        books = pd.read_csv(input_file, sep=';', encoding='utf-8')
        
        # Ta bort dubbletter i indatan
        initial_count = len(books)
        books = books.drop_duplicates(subset=['Titel'], keep='first')
        if len(books) < initial_count:
            logging.info(f"Tog bort {initial_count - len(books)} dubbletter från indatan")
        
        updated_books = []
        total_books = len(books)
        
        for index, row in books.iterrows():
            title = row['Titel']
            given_year = clean_year(row['Utgivningsår'])
            
            logging.info(f"Söker ({index + 1}/{total_books}): {title}")
            book_info = search_book(title)
            
            if book_info:
                updated_books.append({
                    'Titel': title,
                    'Utgivningsår (Lista)': given_year,
                    'Utgivningsår (API)': book_info['Utgivningsår (API)'],
                    'Antal sidor': book_info['Antal sidor'],
                    'Författare': book_info['Författare'],
                    'Förlag': book_info['Förlag'],
                    'ISBN': book_info['ISBN'],
                    'Nyckelord': book_info['Nyckelord'],
                    'Avvikande år': 'Ja' if book_info['Utgivningsår (API)'] != "Okänt" 
                                        and given_year != "Okänt" 
                                        and given_year != book_info['Utgivningsår (API)'] else 'Nej'
                })
            else:
                updated_books.append({
                    'Titel': title,
                    'Utgivningsår (Lista)': given_year,
                    'Utgivningsår (API)': 'Ej hittad',
                    'Antal sidor': 'Ej hittad',
                    'Författare': 'Ej hittad',
                    'Förlag': 'Ej hittad',
                    'ISBN': 'Ej hittad',
                    'Nyckelord': 'Ej hittad',
                    'Avvikande år': 'Nej'
                })
            
            sleep(0.5)
        
        # Skapa DataFrame och ta bort eventuella dubbletter i resultatet
        output_df = pd.DataFrame(updated_books)
        output_df = output_df.drop_duplicates(subset=['Titel', 'ISBN'], keep='last')
        
        # Spara resultatet
        output_df.to_csv(output_file, sep=';', index=False, encoding='utf-8')
        logging.info(f"Resultaten har sparats i {output_file}")
        
        # Skriv ut statistik
        total_processed = len(output_df)
        not_found = len(output_df[output_df['Utgivningsår (API)'] == 'Ej hittad'])
        year_mismatch = len(output_df[output_df['Avvikande år'] == 'Ja'])
        
        logging.info(f"""
        Statistik:
        - Totalt antal böcker processerade: {total_processed}
        - Antal böcker ej hittade: {not_found}
        - Antal böcker med avvikande år: {year_mismatch}
        """)
        
    except Exception as e:
        logging.error(f"Ett oväntat fel uppstod: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
