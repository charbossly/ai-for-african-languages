"""
Scraper final pour Common Voice - combine API + HTML scraping avec gestion d'erreurs.
"""

import requests
import pandas as pd
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime

def get_common_voice_languages_from_api():
    """
    Récupère la liste des langues depuis l'API Common Voice.
    """
    print("[*] Récupération des langues depuis l'API Common Voice...")
    
    try:
        response = requests.get(
            "https://commonvoice.mozilla.org/api/v1/languages",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=10
        )
        
        if response.status_code == 200:
            languages = response.json()
            print(f"[+] {len(languages)} langues trouvées via l'API.")
            return languages
    except Exception as e:
        print(f"[-] Erreur API : {e}")
    
    return []


def scrape_common_voice_stats_from_html():
    """
    Scrape les statistiques détaillées (heures, locuteurs) depuis le HTML.
    """
    print("[*] Scraping des statistiques depuis le HTML Common Voice...")
    
    url = "https://commonvoice.mozilla.org/en/languages"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        
        languages_stats = {}
        
        # Chercher tous les h3 qui contiennent les noms de langues
        for h3 in soup.find_all('h3'):
            lang_name = h3.get_text(strip=True).strip()
            
            if not lang_name or len(lang_name) > 50:
                continue
            
            # Chercher le conteneur parent
            parent = h3.find_parent('div')
            if not parent:
                continue
            
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
            
            # Garder seulement les langues avec des données
            if hours > 0 or speakers > 0 or sentences > 0:
                languages_stats[lang_name] = {
                    'hours': hours,
                    'speakers': speakers,
                    'validation_progress': validation,
                    'sentences': sentences
                }
        
        print(f"[+] Statistiques extraites pour {len(languages_stats)} langues.")
        return languages_stats
    
    except Exception as e:
        print(f"[-] Erreur scraping HTML : {e}")
        return {}


def merge_common_voice_data(api_languages, html_stats):
    """
    Fusionne les données de l'API et du HTML.
    """
    print("[*] Fusion des données API et HTML...")
    
    merged_data = []
    
    for lang in api_languages:
        english_name = lang.get('english_name', '')
        
        # Chercher les statistiques correspondantes dans le HTML
        stats = html_stats.get(english_name, {})
        
        merged_data.append({
            'language_code': lang.get('name'),
            'language': english_name,
            'native_name': lang.get('native_name', ''),
            'hours': stats.get('hours', 0),
            'speakers': stats.get('speakers', 0),
            'validation_progress': stats.get('validation_progress', 0),
            'sentences': stats.get('sentences', 0),
            'is_contributable': lang.get('is_contributable', 0),
            'is_translated': lang.get('is_translated', 0)
        })
    
    return merged_data


def get_african_languages_mapping():
    """Mapping complet des langues africaines aux pays."""
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


def filter_african_languages(df):
    """Filtre et enrichit les données pour les langues africaines."""
    print("[*] Filtrage des langues africaines...")
    
    african_mapping = get_african_languages_mapping()
    
    df['is_african'] = df['language'].isin(african_mapping.keys())
    df['african_countries'] = df['language'].map(lambda x: african_mapping.get(x, []))
    
    df_african = df[df['is_african']].copy()
    
    print(f"[+] {len(df_african)} langues africaines trouvées sur Common Voice.")
    return df_african, african_mapping


if __name__ == "__main__":
    print("=" * 70)
    print("SCRAPING COMPLET COMMON VOICE - DONNÉES EN TEMPS RÉEL")
    print("=" * 70)
    
    # Étape 1 : Récupérer les langues depuis l'API
    api_languages = get_common_voice_languages_from_api()
    
    if not api_languages:
        print("[-] Impossible de récupérer les données. Vérifiez votre connexion.")
        exit(1)
    
    # Étape 2 : Scraper les statistiques depuis le HTML
    html_stats = scrape_common_voice_stats_from_html()
    
    # Étape 3 : Fusionner les données
    merged_data = merge_common_voice_data(api_languages, html_stats)
    df_cv = pd.DataFrame(merged_data)
    
    # Étape 4 : Filtrer les langues africaines
    df_african, mapping = filter_african_languages(df_cv)
    
    # Étape 5 : Sauvegarder
    df_cv.to_csv('./common_voice_all_languages.csv', index=False)
    df_african.to_csv('./common_voice_african_languages.csv', index=False)
    
    print(f"\n[+] {len(df_cv)} langues au total.")
    print(f"[+] {len(df_african)} langues africaines.")
    print("\n[+] Fichiers sauvegardés :")
    print("    - common_voice_all_languages.csv")
    print("    - common_voice_african_languages.csv")
    
    print("\n[*] Top 10 des langues africaines sur Common Voice :")
    print(df_african[['language', 'hours', 'speakers', 'validation_progress']].sort_values('hours', ascending=False).head(10).to_string())
    
    # Sauvegarder aussi en JSON pour faciliter l'intégration
    df_cv.to_json('./common_voice_all_languages.json', orient='records', indent=2)
    df_african.to_json('./common_voice_african_languages.json', orient='records', indent=2)
    
    print("\n[+] Fichiers JSON également générés.")
