# Guide d'utilisation de ThermoScout

ThermoScout est un outil de pré-qualification : il estime rapidement le potentiel de récupération de chaleur
d'un site industriel. Il ne remplace ni une visite de site ni une étude d'ingénierie.

## Onglet « Analyse d'un site »

1. Renseigner le client, le secteur, le débit de fumées (Nm³/h), la température des fumées (°C) et les heures de
   fonctionnement par an. Ces trois derniers champs sont obligatoires.
2. Les autres champs (température de rejet, tampon, prix de l'énergie, rendements, facteur CO₂) sont préremplis
   avec les valeurs de l'onglet Paramètres ; on peut les ajuster pour un site précis.
3. Cliquer sur « Analyser le gisement ». Résultats : score sur 100, puissance récupérable, chaleur valorisée,
   économie annuelle, CO₂ évité, stockage tampon, retour sur investissement, alertes.

### Le score de potentiel (0 à 100)
Règle de l'outil, non issue d'une norme : 40 points pour la puissance récupérable (maximum atteint à 2 000 kW),
35 points pour le niveau de température (de 150 °C à 600 °C), 25 points pour la durée de fonctionnement
(maximum à 6 000 h/an). Niveaux : « Fort potentiel » à partir de 65, « Potentiel moyen » à partir de 40
(seuils modifiables).

### Alertes possibles
Température basse (< 200 °C), température de rejet inférieure à 140 °C (risque de condensation acide),
moins de 2 000 h/an, absence de tampon, temps de retour supérieur à 8 ans.

### Le retour sur investissement
Il n'est calculé que si un investissement est saisi, ou si le coût d'investissement par kW est renseigné dans
les Paramètres. Sinon l'outil affiche « — » : il ne devine pas de prix.

### Actions après l'analyse
- **Synthèse commerciale** : texte rédigé par l'IA à partir des chiffres calculés.
- **Mail de prospection** : brouillon modifiable. Le bouton « Valider et ouvrir dans ma messagerie » ouvre le
  message dans l'application de mail de l'utilisateur, qui l'envoie lui-même. Rien n'est envoyé automatiquement.
  La signature `[Prénom Nom]` est à compléter.
- **Proposition PDF** : document mis en page, à enregistrer via « Imprimer » puis « Enregistrer au format PDF ».

## Onglet « Multi-sites (Excel / CSV) »

Charger un fichier .xlsx ou .csv (max 500 lignes, 2 Mo). Colonnes obligatoires : `debit_nm3h`, `t_source`,
`heures_an`. Colonnes facultatives : `client`, `secteur`, `t_rejet`, `heures_tampon`, `prix_energie`, `capex`,
`contact_nom`, `contact_email`. Les colonnes vides prennent les valeurs des Paramètres. Un modèle Excel est
téléchargeable dans l'onglet. Les sites sont classés par score ; les lignes invalides sont listées avec la raison
sans bloquer les autres. Le classement s'exporte en Excel. Un clic sur une ligne ouvre le détail du site.

## Onglet « Paramètres »

Contient les hypothèses du moteur : masse volumique et chaleur massique des fumées, chaleur massique du matériau
de stockage, rendements (récupération, stockage, chaudière), facteur CO₂, prix de l'énergie, température de rejet,
autonomie du tampon, taux de change euro/dirham, coût d'investissement (par kW et fixe), seuils de score.
Toute valeur hors plage est refusée. Les valeurs par défaut sont génériques : **elles doivent être remplacées par
les données réelles d'Eco-Tech Ceram** pour obtenir des chiffres fiables.

## Devise

Le sélecteur en haut à droite bascule l'affichage entre euros et dirhams. Les calculs sont faits en euros ; le
taux (10,8 DH pour 1 € par défaut) est à vérifier et modifiable dans les Paramètres.

## Limites à connaître

- Les résultats sont des estimations indicatives, pas un devis ni un engagement de performance.
- Les formules sont simples (régime permanent, pas de modélisation dynamique du stockage ni des pertes réelles).
- L'IA ne calcule rien : elle rédige à partir des chiffres fournis par le moteur. Ses textes doivent être relus.
- L'IA locale (Hermes via Ollama) peut être lente (de 1 à 2 minutes par texte) sur un ordinateur sans carte graphique.
