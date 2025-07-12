# Projet LinkedIn Data Pipeline & Dashboard

Ce dépôt présente la mise en place d'une pipeline ETL avec Snowflake et d'un dashboard interactif avec Streamlit, à partir de données d'offres d'emploi LinkedIn.

---

## 📂 Structure du dépôt

```text
linkedin-project/
│
├── README.md                  # Ce document
├── sql/                       # Scripts SQL commentés par étape
│   ├── 01_create_schema.sql
│   ├── 02_file_formats_and_stage.sql
│   ├── 03_raw_tables.sql
│   ├── 04_load_raw_data.sql
│   ├── 05_json_ingestion.sql
│   ├── 06_transform_to_clean.sql
│   └── 07_industries_dimension.sql
│
├── streamlit/                 # Application Streamlit et visuels
│   ├── app.py                 # Code principal

├── docs/                      # Documentation des problèmes et notes
│   ├── PROBLEMS_AND_SOLUTIONS.md
│   └── NOTES_ON_IMPLEMENTATION.md
│
└── .gitignore                 # Fichiers et dossiers ignorés par Git
```

---

## 🔧 Installation et exécution

1. **Cloner le dépôt**


2. **Exécuter les scripts SQL dans Snowflake**

   * Charger, dans l'ordre, les fichiers du dossier `sql/` :

     1. `01_create_schema.sql`
     2. `02_file_formats_and_stage.sql`
     3. `03_raw_tables.sql`
     4. `04_load_raw_data.sql`
     5. `05_json_ingestion.sql`
     6. `06_transform_to_clean.sql`
     7. `07_industries_dimension.sql`

3. **Lancer l'application Streamlit**


## 🗂️ Scripts SQL détaillés

Chaque script se trouve dans `sql/` et comprend :

* **Commentaires** explicatifs (`-- === COMMENTAIRE ===`).
* **Étapes** successives de la pipeline (création de la base, formats, tables raw, chargement, JSON VARIANT, nettoyage, dimensions).

**Points clés** :

* Utilisation d’un **stage S3** pour charger CSV et JSON.
* Formats personnalisés pour CSV (`SKIP_HEADER`, `PARSE_HEADER`, `ERROR_ON_COLUMN_COUNT_MISMATCH`).
* Tables **raw** vs tables **propres** : on ingère d’abord en brut, puis on transforme via `LATERAL FLATTEN`.
* Table de dimension `industries` pour rapprocher les `industry_id` de leur libellé.

---

## 📊 Application Streamlit

Le fichier `streamlit/app.py` contient :

1. **Distribution des salaires**

   * Histogramme filtrable avec `st.slider`.
2. **Nombre d'offres par industrie**

   * Histogramme interactif.
3. **Top 10 des entreprises**

   * Tableau triable et filtrable.

Chaque section est commentée (`# === COMMENTAIRE ===`) pour expliquer la logique et les widgets Streamlit utilisés.

---

## ⚠️ Problèmes rencontrés & solutions

| Problème                                                                                  | Cause identifiée                                                                | Solution appliquée                                                                                                                                       |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Parsing JSON malformé**                                                                 | Certains fichiers JSON contenaient des lignes incorrectes                       | Ajout de `ON_ERROR = 'CONTINUE'` dans les commandes `COPY` pour avancer malgré les erreurs, suivi d'une inspection manuelle des lignes corrompues.       |
| **Incohérence entre colonnes CSV et table**                                               | Noms de colonnes CSV ne correspondaient pas toujours (casse, espaces)           | Utilisation de `MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE` et `PARSE_HEADER = TRUE` pour la correspondance automatique des noms de colonnes.               |
| **KPIs par secteur : affichage des *IDs* au lieu des *noms***                             | Oubli de jointure entre la table factuelle des offres et la table `industries`. | Ajout d’une requête SQL avec `JOIN industries USING(industry_id)` pour remplacer les `industry_id` par `industry_name` avant génération des KPI/graphes. |
| **Taille des données** : lenteur à l’affichage des graphiques Streamlit pour gros volumes | Chargement complet en mémoire, pas de pagination                                | Implémentation d’un **échantillonnage** (`df.sample(0.3)`) et/ou d’une **pagination** via `st.dataframe(..., height=..)`.                                |

---

## 📖 Notes d'implémentation

Voir `docs/NOTES_ON_IMPLEMENTATION.md` pour :

* Contexte et **choix d'architecture** (Snowflake + Streamlit).
* Bonnes pratiques suivies (naming conventions, modularité des scripts, utilisation de `LATERAL FLATTEN`).
* **Sécurité** et accès (gestion des credentials Snowflake via variables d'environnement).

---

## 🚀 KPIs & Visualisations


1. Top 10 des titres de postes les plus publiés par industrie.

2. Top 10 des postes les mieux rémunérés par industrie.

3. Répartition des offres d’emploi par taille d’entreprise.

4. Répartition des offres d’emploi par secteur d’activité.

5. Répartition des offres d’emploi par type d’emploi (temps plein, stage, temps partiel).

**Note** : la jointure avec la dimension `industries` doit être effectuée pour afficher les libellés au lieu des IDs.

---


