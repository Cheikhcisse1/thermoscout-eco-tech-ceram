# ThermoScout — qualification de gisements de chaleur fatale (démo Eco Tech Ceram)

Outil de pré-qualification : à partir du débit, de la température et des heures de fonctionnement d'un site
industriel, il estime la puissance récupérable, l'énergie valorisée, l'économie annuelle, le CO₂ évité, le
stockage tampon et le retour sur investissement, avec un score de potentiel sur 100.

## Fonctions
- Analyse d'un site, avec alertes techniques
- Import **Excel/CSV multi-sites**, classement et export Excel
- **Paramètres éditables** (`params.json`) — à remplacer par les données réelles de l'entreprise
- **Mail de prospection** rédigé par IA, à relire et valider (rien n'est envoyé automatiquement)
- **Proposition PDF** (impression du navigateur)
- **Assistant (chat RAG)** qui répond depuis le dossier `knowledge/` en citant ses sources
- Devise euro / dirham

## Important
Les chiffres sont des **estimations indicatives** (formules thermiques simples, hypothèses génériques). Ils ne
remplacent pas une étude d'ingénierie et ne constituent pas un devis. Ce projet est une démonstration et n'est
pas un produit officiel d'Eco-Tech Ceram. Le document `knowledge/01_*` provient de sources publiques ; les points
« à confirmer » doivent être validés par l'entreprise.

## Installation (Windows)
```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
ollama pull hermes3
```

## Lancement
Double-clic sur `start_thermoscout.bat`, puis http://127.0.0.1:8780

## Tests
```powershell
.\.venv\Scripts\python.exe -m unittest tests -v
```

## Ajouter des connaissances à l'assistant
Déposer des fichiers `.md` / `.txt` dans `knowledge/` (voir `knowledge/00_LISEZ-MOI_base_documentaire.md`).
Ne jamais y mettre de secrets ni de données personnelles.

## Déploiement en ligne (Render, démo publique gratuite)

La démo en ligne est **ouverte à tous, sans mot de passe**, et utilise l'IA **gratuite** Google Gemini (Ollama n'existe pas en ligne).
Garde-fous du mode public (`PUBLIC_MODE=1`) : fournisseur d'IA imposé (Gemini), limite de requêtes par visiteur et par heure (`RATE_LIMIT_PER_HOUR`), taille des textes plafonnée, aucune action serveur sensible (envoi de mail ou modification des paramètres partagés désactivés).

1. Créer une clé gratuite sur https://aistudio.google.com/apikey.
2. Créer un compte sur render.com (avec ton compte GitHub).
3. **New + > Blueprint** > choisir ce dépôt : Render lit `render.yaml`.
4. Coller la clé dans la variable `GEMINI_API_KEY` du tableau de bord Render (jamais dans Git).
5. Ouvrir l'URL fournie par Render.

Limites : le plan gratuit met le service en veille après inactivité (premier chargement d'environ 1 minute) ; le quota gratuit de Gemini est limité par jour.
Pour un accès privé avec Claude à la place : retirer `PUBLIC_MODE`, définir `APP_PASSWORD` et `ANTHROPIC_API_KEY`.
