import pandas as pd

# Les données sont déjà traitées par le pipeline de veille linguistique.
# On se contente de charger le JSON, de filtrer les pays non-africains (ex: Papua New Guinea)
# et de sauvegarder un CSV prêt à consommer par les scripts de visualisation.

SOURCE_JSON = './veille_linguistique_complete.json'
OUTPUT_CSV = './processed_african_data.csv'

# Codes ISO alpha-3 à exclure (pays hors Afrique présents dans la source)
NON_AFRICAN_ISO = {'PNG'}

df = pd.read_json(SOURCE_JSON)
df = df[~df['iso_alpha'].isin(NON_AFRICAN_ISO)].reset_index(drop=True)

df.to_csv(OUTPUT_CSV, index=False)
print(f"Données traitées et sauvegardées dans {OUTPUT_CSV}")
print(
    df[['country', 'languages', 'cv_languages_count', 'cv_gap_score']]
    .sort_values(by='cv_gap_score', ascending=False)
    .head(10)
)
