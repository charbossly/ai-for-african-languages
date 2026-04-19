import pandas as pd
import plotly.express as px
import pycountry
import matplotlib.pyplot as plt

# Les données source stockent 'iso_alpha' en alpha-2 (compat scraping Common Voice).
# Plotly choropleth attend de l'alpha-3, on convertit donc au moment de l'affichage.
df = pd.read_json('./veille_linguistique_complete.json')

# Filtrer les pays non-africains (Papua New Guinea est dans la source mais hors scope)
df = df[df['iso_alpha'] != 'PNG'].reset_index(drop=True)


def alpha2_to_alpha3(code):
    if not isinstance(code, str):
        return None
    code = code.strip().upper()
    country = pycountry.countries.get(alpha_2=code) or pycountry.countries.get(alpha_3=code)
    return country.alpha_3 if country else None


df['iso_alpha3'] = df['iso_alpha'].apply(alpha2_to_alpha3)

# Carte choroplèthe Plotly
fig = px.choropleth(
    df,
    locations="iso_alpha3",
    color="cv_gap_score",
    hover_name="country",
    title="Veille Cartographique : Densité Linguistique vs Common Voice (Afrique)",
    color_continuous_scale=px.colors.sequential.YlOrRd,
    scope="africa"
)

# Graphique à barres : Top 15 du gap de couverture
df_sorted = df.sort_values(by='cv_gap_score', ascending=False).head(15)

plt.figure(figsize=(10, 8))
plt.barh(df_sorted['country'], df_sorted['cv_gap_score'], color='salmon')
plt.xlabel("Indice de Manque (Langues / (CV_Langues + 1))")
plt.title("Top 15 des pays africains avec le plus grand besoin de couverture Common Voice")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig('./afrique_cv_gap_bar_chart.png')
print("Graphique à barres généré : ./afrique_cv_gap_bar_chart.png")
