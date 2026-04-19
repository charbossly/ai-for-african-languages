"""
Module de scraping pour Common Voice utilisant une approche plus robuste.
Utilise l'API interne de Common Voice si disponible, sinon parse le HTML directement.
"""

import requests
import pandas as pd
import json
import re
from datetime import datetime

def get_common_voice_data_from_api():
    """
    Essayer de récupérer les données depuis l'API interne de Common Voice.
    """
    print("[*] Tentative d'accès à l'API Common Voice...")
    
    # Common Voice expose certaines données via une API
    api_urls = [
        "https://commonvoice.mozilla.org/api/v1/languages",
        "https://commonvoice.mozilla.org/api/languages",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for api_url in api_urls:
        try:
            response = requests.get(api_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"[+] API trouvée : {api_url}")
                return data
        except:
            continue
    
    print("[-] API Common Voice non accessible.")
    return None


def scrape_common_voice_html_improved():
    """
    Scrape la page HTML complète de Common Voice avec une meilleure extraction.
    """
    print("[*] Scraping HTML de Common Voice...")
    
    url = "https://commonvoice.mozilla.org/en/languages"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        # Chercher les données JSON imbriquées dans le HTML (Common Voice utilise React)
        # Chercher les patterns de données structurées
        text = response.text
        
        # Pattern 1 : Chercher les données JSON dans les scripts
        script_pattern = r'<script[^>]*>.*?({.*?"language".*?})</script>'
        matches = re.findall(script_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            print(f"[+] Données JSON trouvées dans les scripts.")
            try:
                data = json.loads(matches[0])
                return data
            except:
                pass
        
        # Pattern 2 : Chercher les données dans le contenu textuel structuré
        # Extraire les sections et les langues
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        languages = []
        
        # Chercher les h3 qui contiennent les noms de langues
        for h3 in soup.find_all('h3'):
            lang_name = h3.get_text(strip=True)
            
            # Chercher le conteneur parent (généralement un div)
            parent = h3.find_parent('div')
            if parent:
                parent_text = parent.get_text()
                
                # Extraire les statistiques
                hours_match = re.search(r'Hours?\s*(\d+(?:,\d+)?)', parent_text)
                speakers_match = re.search(r'Speakers?\s*(\d+(?:,\d+)?)', parent_text)
                validation_match = re.search(r'Validation\s*Progress?\s*(\d+)%', parent_text)
                sentences_match = re.search(r'Sentences?\s*(\d+(?:,\d+)?)', parent_text)
                
                hours = int(hours_match.group(1).replace(',', '')) if hours_match else 0
                speakers = int(speakers_match.group(1).replace(',', '')) if speakers_match else 0
                validation = int(validation_match.group(1)) if validation_match else 0
                sentences = int(sentences_match.group(1).replace(',', '')) if sentences_match else 0
                
                if hours > 0 or speakers > 0:
                    languages.append({
                        'language': lang_name,
                        'hours': hours,
                        'speakers': speakers,
                        'validation_progress': validation / 100 if validation > 0 else 0,
                        'sentences': sentences
                    })
        
        if languages:
            print(f"[+] {len(languages)} langues extraites du HTML.")
            return languages
        
        return None
    
    except Exception as e:
        print(f"[-] Erreur lors du scraping : {e}")
        return None


def get_african_languages_mapping():
    """Mapping des langues africaines aux pays."""
    return {
        'Kinyarwanda': ['Rwanda', 'Uganda', 'Democratic Republic of the Congo'],
        'Luganda': ['Uganda'],
        'Swahili': ['Tanzania', 'Kenya', 'Uganda', 'Rwanda', 'Burundi', 'Democratic Republic of the Congo'],
        'Kabyle': ['Algeria'],
        'Dholuo': ['Kenya', 'Tanzania'],
        'Yoruba': ['Nigeria', 'Benin', 'Togo'],
        'Hausa': ['Nigeria', 'Niger', 'Ghana', 'Cameroon'],
        'Igbo': ['Nigeria'],
        'Amharic': ['Ethiopia'],
        'Oromo': ['Ethiopia', 'Kenya'],
        'Somali': ['Somalia', 'Ethiopia', 'Djibouti', 'Kenya'],
        'Wolof': ['Senegal', 'Gambia', 'Mauritania'],
        'Bambara': ['Mali'],
        'Twi': ['Ghana'],
        'Kalenjin': ['Kenya'],
        'Arabic': ['Algeria', 'Egypt', 'Sudan', 'Libya', 'Tunisia', 'Morocco'],
        'Fulani': ['Nigeria', 'Niger', 'Cameroon', 'Guinea', 'Mali', 'Senegal'],
        'Manding': ['Mali', 'Guinea', 'Senegal'],
        'Acholi': ['Uganda'],
        'Kikuyu': ['Kenya'],
        'Shona': ['Zimbabwe'],
        'Xhosa': ['South Africa'],
        'Zulu': ['South Africa'],
        'Sotho': ['South Africa', 'Lesotho'],
        'Tswana': ['Botswana', 'South Africa'],
        'Afrikaans': ['South Africa', 'Namibia'],
    }


def process_common_voice_data(cv_data):
    """
    Traite les données Common Voice et crée un DataFrame.
    """
    if not cv_data:
        return pd.DataFrame()
    
    # Si c'est une liste de dictionnaires
    if isinstance(cv_data, list):
        df = pd.DataFrame(cv_data)
    # Si c'est un dictionnaire avec une clé 'languages'
    elif isinstance(cv_data, dict) and 'languages' in cv_data:
        df = pd.DataFrame(cv_data['languages'])
    else:
        return pd.DataFrame()
    
    # Ajouter les informations sur les pays africains
    african_mapping = get_african_languages_mapping()
    df['is_african'] = df['language'].isin(african_mapping.keys())
    df['african_countries'] = df['language'].map(lambda x: african_mapping.get(x, []))
    
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("SCRAPING COMMON VOICE (APPROCHE AMÉLIORÉE)")
    print("=" * 60)
    
    # Essayer l'API d'abord
    cv_data = get_common_voice_data_from_api()
    
    # Si l'API ne fonctionne pas, scraper le HTML
    if not cv_data:
        cv_data = scrape_common_voice_html_improved()
    
    if cv_data:
        # Traiter les données
        df_cv = process_common_voice_data(cv_data)
        
        if not df_cv.empty:
            # Sauvegarder toutes les langues
            df_cv.to_csv('./common_voice_all_languages.csv', index=False)
            
            # Sauvegarder seulement les langues africaines
            df_african = df_cv[df_cv['is_african']]
            df_african.to_csv('./common_voice_african_languages.csv', index=False)
            
            print(f"\n[+] {len(df_cv)} langues trouvées au total.")
            print(f"[+] {len(df_african)} langues africaines trouvées.")
            print("\nTop 10 des langues africaines sur Common Voice :")
            print(df_african[['language', 'hours', 'speakers', 'validation_progress']].sort_values('hours', ascending=False).head(10))
        else:
            print("[-] Impossible de traiter les données.")
    else:
        print("[-] Impossible de récupérer les données Common Voice.")
