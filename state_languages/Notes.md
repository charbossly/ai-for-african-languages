# Notes — Veille Cartographique Langues / Common Voice

## Objectif

Visualiser sur une carte de l'Afrique l'écart entre la **densité linguistique** d'un pays
(nombre de langues parlées) et sa **couverture par Common Voice** (nombre de langues
supportées + heures d'audio).

Score d'écart calculé :

```
cv_gap_score = languages / (cv_languages_count + 1)
```

Plus le score est haut, plus le pays est sous-représenté par rapport à sa diversité.

## Pipeline

```
scrape_linguistic_data.py          scrape_common_voice_final.py
              \                   /
               v                 v
      veille_cartographique_complete.py   <-- fusionne, calcule le gap, ajoute iso_alpha
                      |
                      v
        veille_linguistique_complete.json  <-- SOURCE DE VERITE (données déjà traitées)
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
   process_data.py  generate_map.py  generate_static_plots.py
          |           |           |
          v           v           v
   processed_        HTML         PNG (matplotlib)
   african_          interactifs  + choroplèthe statique
   data.csv          (Plotly)
```

## Rôles des scripts

| Script                              | Rôle                                                                                                                                                                                                            |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `veille_cartographique_complete.py` | Orchestrateur : scrape + fusionne + écrit `veille_linguistique_complete.json` avec tous les champs finaux (country, languages, cv_languages_count, total_cv_hours, cv_languages_list, cv_gap_score, iso_alpha). |
| `process_data.py`                   | Charge le JSON, filtre les non-africains (ex. Papua New Guinea), produit `processed_african_data.csv`.                                                                                                          |
| `generate_map.py`                   | Génère 2 cartes HTML Plotly : carte d'écart et carte du nombre de langues CV.                                                                                                                                   |
| `generate_static_plots.py`          | Génère un graphique à barres PNG (Top 15 gap) + une carte Plotly.                                                                                                                                               |

## Bug trouvé et corrigé (2026-04-19)

### Symptôme

Les cartes Plotly n'affichaient que 2-3 pays colorés (South Sudan, Eswatini)
au lieu de toute l'Afrique.

### Cause

Dans `veille_cartographique_complete.py`, le `mapping` manuel associait les pays
à leurs codes ISO **alpha-2** (NG, ZA, CM, CD, TZ, SD...), alors que
`plotly.choropleth` utilise par défaut `locationmode='ISO-3'` qui attend des
codes **alpha-3** (NGA, ZAF, CMR, COD, TZA, SDN...).

Seuls les pays absents du mapping manuel — qui passaient alors par
`pycountry.search_fuzzy()` — recevaient un vrai alpha-3 et s'affichaient.

### Décision d'architecture

On garde `iso_alpha` en **alpha-2** dans la source (`veille_linguistique_complete.json`)
pour rester compatible avec le scraping Common Voice et les sources en ligne qui
utilisent généralement l'alpha-2. La conversion alpha-2 → alpha-3 se fait
**uniquement au moment de l'affichage** dans les scripts de visualisation, via
`pycountry`, dans une colonne dérivée `iso_alpha3` passée à Plotly.

### Fichiers touchés

- `veille_cartographique_complete.py` : mapping harmonisé en alpha-2 (ajout
  notamment de `South Sudan: SS` qui manquait).
- `generate_map.py` : ajout de `alpha2_to_alpha3()` + colonne `iso_alpha3`
  utilisée comme `locations=` dans les `px.choropleth`.
- `generate_static_plots.py` : même ajout.
- `process_data.py` : simplifié — ne retraite plus les données brutes, il lit
  directement le JSON déjà traité et filtre `PNG` (Papua New Guinea).

## Fichiers de sortie

| Fichier                                   | Contenu                                                          |
| ----------------------------------------- | ---------------------------------------------------------------- |
| `veille_linguistique_complete.json`       | Données fusionnées (source de vérité).                           |
| `veille_linguistique_complete.csv`        | Même chose au format CSV.                                        |
| `processed_african_data.csv`              | Sous-ensemble filtré (Afrique uniquement).                       |
| `afrique_common_voice_gap_map.html`       | Carte d'écart interactive.                                       |
| `afrique_cv_coverage_count.html`          | Carte du nombre de langues CV.                                   |
| `afrique_cv_gap_bar_chart.png`            | Top 15 des pays avec le plus grand gap.                          |
| `common_voice_african_languages.csv/json` | Liste filtrée des langues africaines présentes sur Common Voice. |
| `rapport_veille_linguistique.txt`         | Résumé textuel.                                                  |

## Commande de régénération complète

```bash
# 1. Re-scraper + re-fusionner si besoin
python veille_cartographique_complete.py

# 2. Filtrer / exporter le CSV africain
python process_data.py

# 3. Régénérer les visualisations
python generate_map.py
python generate_static_plots.py
```
