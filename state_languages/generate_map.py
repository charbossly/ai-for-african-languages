import pandas as pd
import plotly.express as px
import pycountry

# Les données source ('veille_linguistique_complete.json') stockent 'iso_alpha' en alpha-2
# (compat scraping Common Voice). Plotly choropleth attend de l'alpha-3 avec locationmode='ISO-3',
# on convertit donc au moment de l'affichage uniquement.
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

# Carte 1 : Score d'écart densité linguistique vs couverture Common Voice
fig = px.choropleth(
    df,
    locations="iso_alpha3",
    color="cv_gap_score",
    hover_name="country",
    hover_data={
        "languages": True,
        "cv_languages_count": True,
        "total_cv_hours": True,
        "cv_gap_score": ":.2f",
        "iso_alpha3": False
    },
    title="Veille Cartographique : Densité Linguistique vs Couverture Common Voice en Afrique",
    color_continuous_scale=px.colors.sequential.YlOrRd,
    labels={
        "cv_gap_score": "Score d'Écart (Densité/Support)",
        "languages": "Nombre de Langues",
        "cv_languages_count": "Langues sur Common Voice"
    },
    scope="africa"
)

fig.update_layout(
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
    coloraxis_colorbar=dict(
        title="Indice de Manque de Couverture",
        tickvals=[df['cv_gap_score'].min(), df['cv_gap_score'].max()],
        ticktext=["Bien Couvert", "Sous-représenté"]
    )
)

fig.write_html("./afrique_common_voice_gap_map.html")

# Carte 2 : Nombre direct de langues supportées sur Common Voice
fig2 = px.choropleth(
    df,
    locations="iso_alpha3",
    color="cv_languages_count",
    hover_name="country",
    title="Nombre de Langues Africaines supportées sur Common Voice par Pays",
    color_continuous_scale=px.colors.sequential.Greens,
    scope="africa"
)
fig2.write_html("./afrique_cv_coverage_count.html")

print("Cartes générées :")
print("- ./afrique_common_voice_gap_map.html (Carte d'écart)")
print("- ./afrique_cv_coverage_count.html (Nombre de langues)")
