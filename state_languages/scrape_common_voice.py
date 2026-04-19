"""
Module de scraping pour récupérer les données Common Voice en temps réel.
Source : https://commonvoice.mozilla.org/languages
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime

def scrape_common_voice_languages():
    """
    Scrape la page Common Voice pour extraire toutes les langues et leurs statistiques.
    """
    print("[*] Scraping Common Voice : Langues et statistiques...")
    
    url = "https://commonvoice.mozilla.org/en/languages"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher tous les éléments de langue
        # La structure HTML de Common Voice utilise des sections avec des données imbriquées
        language_data = []
        
        # Chercher les sections de langues lancées et en cours
        sections = soup.find_all('section')
        
        for section in sections:
            # Chercher tous les conteneurs de langues
            language_containers = section.find_all('div', {'class': re.compile(r'language|card', re.I)})
            
            for container in language_containers:
                try:
                    # Extraire le nom de la langue
                    lang_name_elem = container.find('h3') or container.find('h4')
                    if not lang_name_elem:
                        continue
                    
                    lang_name = lang_name_elem.get_text(strip=True)
                    
                    # Extraire les heures
                    hours_text = container.get_text()
                    hours_match = re.search(r'Hours?\s*(\d+(?:,\d+)?)', hours_text, re.I)
                    hours = int(hours_match.group(1).replace(',', '')) if hours_match else 0
                    
                    # Extraire les locuteurs
                    speakers_match = re.search(r'Speakers?\s*(\d+(?:,\d+)?)', hours_text, re.I)
                    speakers = int(speakers_match.group(1).replace(',', '')) if speakers_match else 0
                    
                    # Extraire le progrès de validation
                    validation_match = re.search(r'Validation\s*Progress?\s*(\d+)%', hours_text, re.I)
                    validation = int(validation_match.group(1)) / 100 if validation_match else 0
                    
                    # Extraire les phrases
                    sentences_match = re.search(r'Sentences?\s*(\d+(?:,\d+)?)', hours_text, re.I)
                    sentences = int(sentences_match.group(1).replace(',', '')) if sentences_match else 0
                    
                    if lang_name and hours > 0:  # Garder seulement les langues avec des données
                        language_data.append({
                            'language': lang_name,
                            'hours': hours,
                            'speakers': speakers,
                            'validation_progress': validation,
                            'sentences': sentences
                        })
                
                except Exception as e:
                    continue
        
        if language_data:
            print(f"[+] {len(language_data)} langues trouvées sur Common Voice.")
            return pd.DataFrame(language_data)
        else:
            print("[-] Aucune donnée de langue trouvée.")
            return pd.DataFrame()
    
    except Exception as e:
        print(f"[-] Erreur lors du scraping Common Voice : {e}")
        return pd.DataFrame()


def get_african_languages_mapping():
    """
    Crée un mapping des langues africaines avec leurs pays respectifs.
    Cette fonction utilise une base de connaissances pour mapper les langues aux pays.
    """
    print("[*] Création du mapping langues africaines -> pays...")
    
    # Mapping manuel basé sur la géographie linguistique
    african_languages_mapping = {
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
    }
    
    return african_languages_mapping


def filter_african_languages(df_cv):
    """
    Filtre les langues Common Voice pour garder seulement les langues africaines.
    """
    print("[*] Filtrage des langues africaines...")
    
    african_mapping = get_african_languages_mapping()
    african_languages = list(african_mapping.keys())
    
    # Créer une colonne pour indiquer si c'est une langue africaine
    df_cv['is_african'] = df_cv['language'].isin(african_languages)
    
    # Ajouter les pays associés
    df_cv['african_countries'] = df_cv['language'].map(lambda x: african_mapping.get(x, []))
    
    df_african = df_cv[df_cv['is_african']].copy()
    
    print(f"[+] {len(df_african)} langues africaines trouvées sur Common Voice.")
    return df_african, african_mapping


if __name__ == "__main__":
    print("=" * 60)
    print("SCRAPING DES DONNÉES COMMON VOICE")
    print("=" * 60)
    
    # Scraper Common Voice
    df_cv = scrape_common_voice_languages()
    
    if not df_cv.empty:
        # Filtrer les langues africaines
        df_african_cv, mapping = filter_african_languages(df_cv)
        
        # Sauvegarder
        df_cv.to_csv('./common_voice_all_languages.csv', index=False)
        df_african_cv.to_csv('./common_voice_african_languages.csv', index=False)
        
        print(f"\n[+] Données Common Voice sauvegardées.")
        print(f"    - Toutes les langues : common_voice_all_languages.csv")
        print(f"    - Langues africaines : common_voice_african_languages.csv")
        print("\nAperçu des langues africaines sur Common Voice :")
        print(df_african_cv[['language', 'hours', 'speakers', 'validation_progress']].head(15))
    else:
        print("[-] Impossible de récupérer les données Common Voice.")
