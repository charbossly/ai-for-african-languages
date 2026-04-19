"""
Module de scraping pour récupérer les données linguistiques et démographiques en temps réel.
Sources : Wikipédia (List of countries by number of languages, Languages of Africa)
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
from datetime import datetime

def scrape_african_languages_wikipedia():
    """
    Scrape la page Wikipedia "List of countries by number of languages"
    pour obtenir le nombre de langues par pays africain.
    """
    print("[*] Scraping Wikipédia : Nombre de langues par pays...")
    
    url = "https://en.wikipedia.org/wiki/List_of_countries_by_number_of_languages"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Trouver le tableau principal
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        if not tables:
            print("[-] Aucun tableau trouvé sur la page.")
            return pd.DataFrame()
        
        # Le premier tableau contient généralement les données
        table = tables[0]
        rows = table.find_all('tr')[1:]  # Ignorer l'en-tête
        
        data = []
        african_countries = [
            'Nigeria', 'Cameroon', 'Democratic Republic of the Congo', 'Ethiopia', 
            'Tanzania', 'Kenya', 'Sudan', 'Chad', 'Mali', 'Ghana', 'Ivory Coast',
            'Burkina Faso', 'Senegal', 'Algeria', 'Rwanda', 'Burundi', 'Somalia',
            'South Africa', 'Uganda', 'Niger', 'Benin', 'Togo', 'Liberia', 'Sierra Leone',
            'Guinea', 'Guinea-Bissau', 'Gambia', 'Mauritania', 'Djibouti', 'Eritrea',
            'Mozambique', 'Zimbabwe', 'Zambia', 'Malawi', 'Botswana', 'Lesotho',
            'Eswatini', 'Namibia', 'Angola', 'Congo', 'Gabon', 'Equatorial Guinea',
            'Central African Republic', 'Seychelles', 'Mauritius', 'Comoros', 'Cape Verde'
        ]
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                country = cols[0].get_text(strip=True)
                try:
                    num_languages = int(cols[1].get_text(strip=True).replace(',', ''))
                    
                    # Vérifier si c'est un pays africain
                    if any(african_country.lower() in country.lower() for african_country in african_countries):
                        data.append({
                            'country': country,
                            'languages': num_languages
                        })
                except ValueError:
                    continue
        
        df = pd.DataFrame(data)
        print(f"[+] {len(df)} pays africains trouvés avec données linguistiques.")
        return df
    
    except Exception as e:
        print(f"[-] Erreur lors du scraping Wikipédia : {e}")
        return pd.DataFrame()


def scrape_african_population_wikipedia():
    """
    Scrape les données de population des pays africains depuis Wikipédia.
    """
    print("[*] Scraping Wikipédia : Population des pays africains...")
    
    url = "https://en.wikipedia.org/wiki/Demographics_of_Africa"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher les tableaux
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        data = []
        for table in tables:
            rows = table.find_all('tr')[1:]
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 3:
                    try:
                        country = cols[0].get_text(strip=True)
                        # Extraire le nombre de population (souvent en colonne 2 ou 3)
                        pop_text = cols[2].get_text(strip=True).replace(',', '').replace(' ', '')
                        population = int(re.findall(r'\d+', pop_text)[0] * 1000000) if re.findall(r'\d+', pop_text) else None
                        
                        if population:
                            data.append({
                                'country': country,
                                'population': population
                            })
                    except (ValueError, IndexError):
                        continue
        
        df = pd.DataFrame(data)
        if len(df) > 0:
            print(f"[+] {len(df)} pays avec données de population trouvés.")
        return df
    
    except Exception as e:
        print(f"[-] Erreur lors du scraping de population : {e}")
        return pd.DataFrame()


def scrape_list_of_african_countries():
    """
    Scrape une liste complète des pays africains depuis Wikipédia.
    """
    print("[*] Scraping Wikipédia : Liste des pays africains...")
    
    url = "https://en.wikipedia.org/wiki/List_of_African_countries_by_population"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.content, 'html.parser')
        
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        if not tables:
            return pd.DataFrame()
        
        table = tables[0]
        rows = table.find_all('tr')[1:]
        
        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                try:
                    country = cols[1].get_text(strip=True)
                    pop_text = cols[2].get_text(strip=True).replace(',', '')
                    population = int(re.findall(r'\d+', pop_text)[0]) if re.findall(r'\d+', pop_text) else None
                    
                    if population and country:
                        data.append({
                            'country': country,
                            'population': population
                        })
                except (ValueError, IndexError):
                    continue
        
        df = pd.DataFrame(data)
        print(f"[+] {len(df)} pays africains avec population trouvés.")
        return df
    
    except Exception as e:
        print(f"[-] Erreur lors du scraping de la liste des pays : {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    print("=" * 60)
    print("SCRAPING DES DONNÉES LINGUISTIQUES AFRICAINES")
    print("=" * 60)
    
    # Scraper les données
    df_languages = scrape_african_languages_wikipedia()
    df_population = scrape_list_of_african_countries()
    
    # Fusionner
    if not df_languages.empty and not df_population.empty:
        df_merged = pd.merge(df_languages, df_population, on='country', how='left')
        df_merged.to_csv('./african_countries_linguistic_data.csv', index=False)
        print(f"\n[+] Données fusionnées sauvegardées dans african_countries_linguistic_data.csv")
        print(df_merged.head(10))
    else:
        print("[-] Impossible de fusionner les données.")
