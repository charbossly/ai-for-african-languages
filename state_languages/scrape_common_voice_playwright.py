"""
Scraper Common Voice utilisant Playwright pour gérer le contenu dynamique (JavaScript).
"""

import asyncio
import pandas as pd
import json
import re
from datetime import datetime

async def scrape_common_voice_with_playwright():
    """
    Utilise Playwright pour charger la page et extraire les données dynamiques.
    """
    print("[*] Initialisation de Playwright...")
    
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("[-] Playwright non installé. Installation...")
        import subprocess
        subprocess.run(["sudo", "pip3", "install", "playwright"], check=True)
        from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        print("[*] Lancement du navigateur...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            url = "https://commonvoice.mozilla.org/en/languages"
            print(f"[*] Navigation vers {url}...")
            await page.goto(url, wait_until="networkidle")
            
            # Attendre que les données se chargent
            await page.wait_for_timeout(3000)
            
            # Extraire les données via JavaScript
            print("[*] Extraction des données...")
            languages_data = await page.evaluate("""
            () => {
                const languages = [];
                
                // Chercher tous les h3 qui contiennent les noms de langues
                const headings = document.querySelectorAll('h3, h4');
                
                headings.forEach(heading => {
                    const text = heading.textContent.trim();
                    if (text && text.length > 0 && text.length < 50) {
                        // Chercher le conteneur parent
                        let container = heading.closest('div');
                        if (container) {
                            const fullText = container.textContent;
                            
                            // Extraire les chiffres
                            const hoursMatch = fullText.match(/Hours?\\s*(\\d+(?:,\\d+)?)/i);
                            const speakersMatch = fullText.match(/Speakers?\\s*(\\d+(?:,\\d+)?)/i);
                            const validationMatch = fullText.match(/Validation\\s*Progress?\\s*(\\d+)%/i);
                            const sentencesMatch = fullText.match(/Sentences?\\s*(\\d+(?:,\\d+)?)/i);
                            
                            const hours = hoursMatch ? parseInt(hoursMatch[1].replace(/,/g, '')) : 0;
                            const speakers = speakersMatch ? parseInt(speakersMatch[1].replace(/,/g, '')) : 0;
                            const validation = validationMatch ? parseInt(validationMatch[1]) : 0;
                            const sentences = sentencesMatch ? parseInt(sentencesMatch[1].replace(/,/g, '')) : 0;
                            
                            if (hours > 0 || speakers > 0) {
                                // Vérifier que ce n'est pas un doublon
                                const exists = languages.some(l => l.language === text);
                                if (!exists) {
                                    languages.push({
                                        language: text,
                                        hours: hours,
                                        speakers: speakers,
                                        validation_progress: validation,
                                        sentences: sentences
                                    });
                                }
                            }
                        }
                    }
                });
                
                return languages;
            }
            """)
            
            print(f"[+] {len(languages_data)} langues extraites.")
            
            await browser.close()
            return languages_data
        
        except Exception as e:
            print(f"[-] Erreur : {e}")
            await browser.close()
            return []


def get_african_languages_mapping():
    """Mapping des langues africaines."""
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


async def main():
    print("=" * 70)
    print("SCRAPING COMMON VOICE AVEC PLAYWRIGHT")
    print("=" * 70)
    
    # Scraper avec Playwright
    languages_data = await scrape_common_voice_with_playwright()
    
    if not languages_data:
        print("[-] Aucune donnée extraite.")
        return
    
    # Créer un DataFrame
    df_cv = pd.DataFrame(languages_data)
    
    # Filtrer les langues africaines
    african_mapping = get_african_languages_mapping()
    df_cv['is_african'] = df_cv['language'].isin(african_mapping.keys())
    df_cv['african_countries'] = df_cv['language'].map(lambda x: african_mapping.get(x, []))
    
    df_african = df_cv[df_cv['is_african']].copy()
    
    # Sauvegarder
    df_cv.to_csv('/home/ubuntu/common_voice_all_languages.csv', index=False)
    df_african.to_csv('/home/ubuntu/common_voice_african_languages.csv', index=False)
    df_cv.to_json('/home/ubuntu/common_voice_all_languages.json', orient='records', indent=2)
    df_african.to_json('/home/ubuntu/common_voice_african_languages.json', orient='records', indent=2)
    
    print(f"\n[+] {len(df_cv)} langues au total.")
    print(f"[+] {len(df_african)} langues africaines.")
    print("\n[+] Fichiers sauvegardés :")
    print("    - common_voice_all_languages.csv / .json")
    print("    - common_voice_african_languages.csv / .json")
    
    if len(df_african) > 0:
        print("\n[*] Top 10 des langues africaines sur Common Voice :")
        print(df_african[['language', 'hours', 'speakers', 'validation_progress']].sort_values('hours', ascending=False).head(10).to_string())


if __name__ == "__main__":
    asyncio.run(main())
