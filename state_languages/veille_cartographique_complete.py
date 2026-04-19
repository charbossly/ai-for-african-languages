#!/usr/bin/env python3.11
"""
SCRIPT MASTER : Veille Cartographique Complète
Collecte automatique des données linguistiques africaines et couverture Common Voice
Génère les cartes interactives et les rapports.
"""

import requests
import pandas as pd
import json
import re
from bs4 import BeautifulSoup
from datetime import datetime
import plotly.express as px
import pycountry
import sys

class VeilleLinguistique:
    """Classe principale pour la veille cartographique des langues africaines."""
    
    def __init__(self):
        self.df_linguistic = None
        self.df_cv_all = None
        self.df_cv_african = None
        self.df_merged = None
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def scrape_african_linguistic_data(self):
        """Scrape les données linguistiques africaines depuis Wikipédia."""
        print("[*] Scraping des données linguistiques africaines...")
        
        url = "https://en.wikipedia.org/wiki/List_of_countries_by_number_of_languages"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            tables = soup.find_all('table', {'class': 'wikitable'})
            if not tables:
                print("[-] Aucun tableau trouvé.")
                return False
            
            table = tables[0]
            rows = table.find_all('tr')[1:]
            
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
            
            data = []
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    country = cols[0].get_text(strip=True)
                    try:
                        num_languages = int(cols[1].get_text(strip=True).replace(',', ''))
                        if any(ac.lower() in country.lower() for ac in african_countries):
                            data.append({'country': country, 'languages': num_languages})
                    except ValueError:
                        continue
            
            self.df_linguistic = pd.DataFrame(data)
            print(f"[+] {len(self.df_linguistic)} pays africains avec données linguistiques.")
            return True
        
        except Exception as e:
            print(f"[-] Erreur : {e}")
            return False
    
    def scrape_common_voice_data(self):
        """Scrape les données Common Voice depuis l'API et le HTML."""
        print("[*] Scraping des données Common Voice...")
        
        # Récupérer les langues depuis l'API
        try:
            response = requests.get(
                "https://commonvoice.mozilla.org/api/v1/languages",
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=10
            )
            
            if response.status_code == 200:
                api_languages = response.json()
                print(f"[+] {len(api_languages)} langues trouvées via l'API.")
                
                # Créer un DataFrame initial
                self.df_cv_all = pd.DataFrame(api_languages)
                self.df_cv_all = self.df_cv_all.rename(columns={'english_name': 'language'})
                
                # Scraper les statistiques du HTML
                self._scrape_cv_stats_from_html()
                
                return True
        except Exception as e:
            print(f"[-] Erreur API : {e}")
            return False
    
    def _scrape_cv_stats_from_html(self):
        """Scrape les statistiques détaillées depuis le HTML Common Voice."""
        print("[*] Scraping des statistiques Common Voice...")
        
        url = "https://commonvoice.mozilla.org/en/languages"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.content, 'html.parser')
            
            stats = {}
            for h3 in soup.find_all('h3'):
                lang_name = h3.get_text(strip=True).strip()
                if not lang_name or len(lang_name) > 50:
                    continue
                
                parent = h3.find_parent('div')
                if not parent:
                    continue
                
                parent_text = parent.get_text()
                
                hours_match = re.search(r'Hours?\s*(\d+(?:,\d+)?)', parent_text)
                speakers_match = re.search(r'Speakers?\s*(\d+(?:,\d+)?)', parent_text)
                validation_match = re.search(r'Validation\s*Progress?\s*(\d+)%', parent_text)
                sentences_match = re.search(r'Sentences?\s*(\d+(?:,\d+)?)', parent_text)
                
                hours = int(hours_match.group(1).replace(',', '')) if hours_match else 0
                speakers = int(speakers_match.group(1).replace(',', '')) if speakers_match else 0
                validation = int(validation_match.group(1)) if validation_match else 0
                sentences = int(sentences_match.group(1).replace(',', '')) if sentences_match else 0
                
                if hours > 0 or speakers > 0:
                    stats[lang_name] = {
                        'hours': hours,
                        'speakers': speakers,
                        'validation_progress': validation,
                        'sentences': sentences
                    }
            
            # Fusionner avec les données API
            if self.df_cv_all is not None and stats:
                for idx, row in self.df_cv_all.iterrows():
                    lang = row['language']
                    if lang in stats:
                        self.df_cv_all.at[idx, 'hours'] = stats[lang]['hours']
                        self.df_cv_all.at[idx, 'speakers'] = stats[lang]['speakers']
                        self.df_cv_all.at[idx, 'validation_progress'] = stats[lang]['validation_progress']
                        self.df_cv_all.at[idx, 'sentences'] = stats[lang]['sentences']
                
                print(f"[+] Statistiques extraites pour {len(stats)} langues.")
        
        except Exception as e:
            print(f"[-] Erreur scraping HTML : {e}")
    
    def filter_african_languages(self):
        """Filtre les langues africaines sur Common Voice."""
        print("[*] Filtrage des langues africaines...")
        
        african_mapping = {
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
        
        if self.df_cv_all is None:
            return False
        
        self.df_cv_all['is_african'] = self.df_cv_all['language'].isin(african_mapping.keys())
        self.df_cv_all['african_countries'] = self.df_cv_all['language'].map(lambda x: african_mapping.get(x, []))
        
        self.df_cv_african = self.df_cv_all[self.df_cv_all['is_african']].copy()
        
        print(f"[+] {len(self.df_cv_african)} langues africaines trouvées.")
        return True
    
    def merge_data(self):
        """Fusionne les données linguistiques et Common Voice."""
        print("[*] Fusion des données...")
        
        if self.df_linguistic is None or self.df_cv_african is None:
            print("[-] Données manquantes.")
            return False
        
        # Compter les langues CV par pays
        country_cv_stats = {}
        for _, row in self.df_cv_african.iterrows():
            countries = row.get('african_countries', [])
            if not isinstance(countries, list):
                countries = [countries]
            
            for country in countries:
                if country not in country_cv_stats:
                    country_cv_stats[country] = {
                        'cv_languages_count': 0,
                        'total_cv_hours': 0,
                        'cv_languages_list': []
                    }
                country_cv_stats[country]['cv_languages_count'] += 1
                country_cv_stats[country]['total_cv_hours'] += row.get('hours', 0)
                country_cv_stats[country]['cv_languages_list'].append(row['language'])
        
        df_cv_stats = pd.DataFrame.from_dict(country_cv_stats, orient='index').reset_index()
        df_cv_stats.columns = ['country', 'cv_languages_count', 'total_cv_hours', 'cv_languages_list']
        
        # Fusionner
        self.df_merged = pd.merge(self.df_linguistic, df_cv_stats, on='country', how='left')
        self.df_merged['cv_languages_count'] = self.df_merged['cv_languages_count'].fillna(0)
        self.df_merged['total_cv_hours'] = self.df_merged['total_cv_hours'].fillna(0)
        self.df_merged['cv_languages_list'] = self.df_merged['cv_languages_list'].apply(lambda x: x if isinstance(x, list) else [])
        
        # Calculer le score d'écart
        self.df_merged['cv_gap_score'] = self.df_merged['languages'] / (self.df_merged['cv_languages_count'] + 1)
        
        print(f"[+] {len(self.df_merged)} pays fusionnés.")
        return True
    
    def generate_iso_codes(self):
        """Ajoute les codes ISO aux pays."""
        print("[*] Ajout des codes ISO...")
        
        # Codes ISO alpha-2 (utilisés pour scraping Common Voice / sources en ligne).
        # La conversion alpha-2 -> alpha-3 pour Plotly se fait au moment de l'affichage.
        mapping = {
            "Benin": "BJ",
            "Togo": "TG",
            "Burkina Faso": "BF",
            "Senegal": "SN",
            "Algeria": "DZ",
            "Rwanda": "RW",
            "Burundi": "BI",
            "Somalia": "SO",
            "Uganda": "UG",
            "Niger": "NE",
            "Ghana": "GH",
            "Mali": "ML",
            "Cameroon": "CM",
            "Ethiopia": "ET",
            "Kenya": "KE",
            "Chad": "TD",
            "Liberia": "LR",
            "Sierra Leone": "SL",
            "Guinea": "GN",
            "Guinea-Bissau": "GW",
            "Gambia": "GM",
            "Mauritania": "MR",
            "Djibouti": "DJ",
            "Eritrea": "ER",
            "Mozambique": "MZ",
            "Zimbabwe": "ZW",
            "Zambia": "ZM",
            "Malawi": "MW",
            "Botswana": "BW",
            "Lesotho": "LS",
            "Namibia": "NA",
            "Angola": "AO",
            "Congo": "CG",
            "Gabon": "GA",
            "Equatorial Guinea": "GQ",
            "Central African Republic": "CF",
            "Seychelles": "SC",
            "Mauritius": "MU",
            "Comoros": "KM",
            "Cape Verde": "CV",
            "Nigeria": "NG",
            "South Africa": "ZA",
            "Sudan": "SD",
            "South Sudan": "SS",
            "Libya": "LY",
            "Tunisia": "TN",
            "Democratic Republic of the Congo": "CD",
            "Tanzania": "TZ",
            "Cote d'Ivoire": "CI",
        }
        
        def get_iso3(country_name):
            if country_name in mapping:
                return mapping[country_name]
            try:
                return pycountry.countries.search_fuzzy(country_name)[0].alpha_3
            except:
                return None
        
        self.df_merged['iso_alpha'] = self.df_merged['country'].apply(get_iso3)
        print("[+] Codes ISO ajoutés.")
    
    def generate_maps(self):
        """Génère les cartes interactives."""
        print("[*] Génération des cartes...")
        
        # Carte 1 : Gap Score
        fig1 = px.choropleth(
            self.df_merged,
            locations="iso_alpha",
            color="cv_gap_score",
            hover_name="country",
            hover_data={
                "languages": True,
                "cv_languages_count": True,
                "total_cv_hours": True,
                "cv_gap_score": ":.2f",
                "iso_alpha": False
            },
            title="Veille Cartographique : Densité Linguistique vs Couverture Common Voice (Afrique)",
            color_continuous_scale=px.colors.sequential.YlOrRd,
            labels={
                "cv_gap_score": "Score d'Écart",
                "languages": "Langues",
                "cv_languages_count": "Langues CV"
            },
            scope="africa"
        )
        fig1.write_html("./afrique_common_voice_gap_map.html")
        print("[+] Carte 1 générée : afrique_common_voice_gap_map.html")
        
        # Carte 2 : Couverture
        fig2 = px.choropleth(
            self.df_merged,
            locations="iso_alpha",
            color="cv_languages_count",
            hover_name="country",
            title="Nombre de Langues Africaines supportées sur Common Voice",
            color_continuous_scale=px.colors.sequential.Greens,
            scope="africa"
        )
        fig2.write_html("./afrique_cv_coverage_count.html")
        print("[+] Carte 2 générée : afrique_cv_coverage_count.html")
    
    def save_data(self):
        """Sauvegarde les données."""
        print("[*] Sauvegarde des données...")
        
        self.df_merged.to_csv('./veille_linguistique_complete.csv', index=False)
        self.df_cv_african.to_csv('./common_voice_african_languages.csv', index=False)
        self.df_cv_all.to_csv('./common_voice_all_languages.csv', index=False)
        
        # Sauvegarder aussi en JSON
        self.df_merged.to_json('./veille_linguistique_complete.json', orient='records', indent=2)
        self.df_cv_african.to_json('./common_voice_african_languages.json', orient='records', indent=2)
        
        print("[+] Données sauvegardées.")
    
    def generate_report(self):
        """Génère un rapport textuel."""
        print("[*] Génération du rapport...")
        
        report = f"""
================================================================================
RAPPORT DE VEILLE CARTOGRAPHIQUE - LANGUES AFRICAINES ET COMMON VOICE
Généré le : {self.timestamp}
================================================================================

1. RÉSUMÉ EXÉCUTIF
------------------
- Pays africains analysés : {len(self.df_merged)}
- Langues africaines sur Common Voice : {len(self.df_cv_african)}
- Densité linguistique moyenne : {self.df_merged['languages'].mean():.1f} langues/pays
- Couverture Common Voice moyenne : {self.df_merged['cv_languages_count'].mean():.1f} langues/pays

2. TOP 10 DES PAYS AVEC LE PLUS GRAND BESOIN DE COUVERTURE
-----------------------------------------------------------
{self.df_merged.nlargest(10, 'cv_gap_score')[['country', 'languages', 'cv_languages_count', 'cv_gap_score']].to_string()}

3. LANGUES AFRICAINES MIEUX COUVERTES
--------------------------------------
{self.df_cv_african[['language', 'name']].head(10).to_string() if len(self.df_cv_african) > 0 else 'Aucune donnée'}

4. DONNÉES DÉTAILLÉES
---------------------
Fichiers générés :
- veille_linguistique_complete.csv : Données fusionnées complètes
- common_voice_african_languages.csv : Langues africaines sur CV
- common_voice_all_languages.csv : Toutes les langues sur CV
- afrique_common_voice_gap_map.html : Carte interactive (Gap Score)
- afrique_cv_coverage_count.html : Carte interactive (Couverture)

================================================================================
"""
        
        with open('./rapport_veille_linguistique.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("[+] Rapport généré : rapport_veille_linguistique.txt")
        print(report)
    
    def run(self):
        """Exécute le pipeline complet."""
        print("\n" + "=" * 70)
        print("VEILLE CARTOGRAPHIQUE COMPLÈTE - LANGUES AFRICAINES")
        print("=" * 70 + "\n")
        
        steps = [
            ("Scraping données linguistiques", self.scrape_african_linguistic_data),
            ("Scraping Common Voice", self.scrape_common_voice_data),
            ("Filtrage langues africaines", self.filter_african_languages),
            ("Fusion des données", self.merge_data),
            ("Génération codes ISO", self.generate_iso_codes),
            ("Génération des cartes", self.generate_maps),
            ("Sauvegarde des données", self.save_data),
            ("Génération du rapport", self.generate_report),
        ]
        
        for step_name, step_func in steps:
            try:
                result = step_func()
                if result is False:
                    print(f"[-] Étape échouée : {step_name}")
                    return False
            except Exception as e:
                print(f"[-] Erreur dans {step_name} : {e}")
                return False
        
        print("\n" + "=" * 70)
        print("[+] VEILLE COMPLÈTE TERMINÉE AVEC SUCCÈS")
        print("=" * 70 + "\n")
        return True


if __name__ == "__main__":
    veille = VeilleLinguistique()
    success = veille.run()
    sys.exit(0 if success else 1)
