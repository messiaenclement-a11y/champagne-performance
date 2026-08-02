# Champagne Performance — V1

Application Streamlit + Supabase pour le suivi du centre de formation.

## Modules inclus
- Tableau de bord
- Joueurs
- Présences
- Tirs
- Sauts
- Musculation
- Rapports individuels PDF
- Paramètres

## Installation

1. Créer un environnement virtuel :

```bash
python -m venv .venv
```

2. L'activer sous Windows :

```bash
.venv\Scripts\activate
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

4. Dans Supabase, exécuter dans l'ordre :
   - `database/01_schema.sql`
   - `database/02_security.sql`
   - `database/03_seed.sql`

5. Copier `.streamlit/secrets.toml.example` vers `.streamlit/secrets.toml`, puis renseigner :
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `APP_ACCESS_CODE`

6. Lancer :

```bash
streamlit run app.py
```

## Ordre de test recommandé
1. Connexion et navigation
2. Ajout d'un joueur
3. Présences
4. Tirs
5. Sauts
6. Musculation
7. Rapport PDF
8. Paramètres

## Limites volontaires de la V1
- Code d'accès commun au staff
- Pas d'autoconfrontation
- Pas de bibliothèque d'exercices
- Pas de rapports collectifs
