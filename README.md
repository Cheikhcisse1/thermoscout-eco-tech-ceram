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

## Déploiement en ligne (Render)

> En ligne, **Ollama n'existe pas** : l'IA passe par l'API Claude (ou OpenAI) avec TA clé, qui sera facturée selon l'usage.
> Le serveur est protégé par mot de passe et limite les requêtes par IP (voir `security.py`) : sans `APP_PASSWORD`,
> il refuse de démarrer.

1. Créer un compte sur [render.com](https://render.com) (avec ton compte GitHub).
2. **New +** > **Blueprint** > choisir ce dépôt : Render lit `render.yaml`.
3. Renseigner les variables demandées dans le tableau de bord Render (jamais dans Git) :
   - `APP_PASSWORD` : le mot de passe d'accès (nom d'utilisateur libre) ;
   - `ANTHROPIC_API_KEY` : ta clé (nécessite des crédits sur console.anthropic.com).
4. Une fois déployé, ouvrir l'URL fournie par Render et saisir le mot de passe.

Limites à connaître : le plan gratuit met le service en veille après inactivité (premier chargement lent) ;
le disque est éphémère (les paramètres modifiés en ligne sont perdus à chaque redéploiement) ; l'image Docker n'a
pas été testée localement par l'auteur.
