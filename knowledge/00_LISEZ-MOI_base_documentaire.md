# Base documentaire de l'assistant (RAG)

L'assistant de ThermoScout répond aux questions en cherchant dans les documents de ce dossier `knowledge`.
Il cite ses sources et dit qu'il ne sait pas quand l'information n'y figure pas.

## Contenu actuel
- `01_eco_tech_ceram_presentation.md` : l'entreprise et Eco-Stock (informations publiques).
- `02_chaleur_fatale_notions.md` : notions et formules sur la chaleur fatale.
- `03_guide_thermoscout.md` : mode d'emploi de l'outil.
- `04_faq.md` : questions fréquentes.

## Ajouter ou modifier un document
1. Déposer un fichier `.md` ou `.txt` (UTF-8) dans le dossier `knowledge`. Maximum 1 Mo par fichier.
2. Rien d'autre à faire : la base est réindexée automatiquement à la prochaine question.
3. Structurer avec des titres (`#`, `##`) : chaque section devient un passage cherchable.

## Bonnes pratiques
- Un document = un sujet. Phrases complètes, chiffres avec unités et date.
- Indiquer la source et la date, et marquer « à confirmer » ce qui ne l'est pas.
- Ne jamais y mettre de mots de passe, de clés API ni de données personnelles : tous les utilisateurs de
  l'outil peuvent interroger cette base.
- Retirer un document obsolète en supprimant le fichier.

## Pour compléter les connaissances de l'assistant (à faire par Eco-Tech Ceram)
Fiches produit Eco-Stock validées, références clients autorisées à être citées, grille tarifaire indicative,
conditions d'éligibilité aux aides, process de visite de site, réponses aux objections courantes.
