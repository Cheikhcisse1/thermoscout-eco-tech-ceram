# La chaleur fatale — notions de base

## Définition

La chaleur fatale (ou chaleur perdue) est la chaleur produite par un procédé industriel qui n'en est pas
l'objet principal et qui est rejetée dans l'environnement : fumées de four, air chaud de refroidissement,
eaux chaudes de process, buées. En la récupérant, on réduit la consommation d'énergie primaire (gaz, etc.)
et les émissions de CO₂.

## Niveaux de température

- **Basse température (< 100 °C)** : usages limités (chauffage de locaux, réseaux de chaleur) ou pompe à chaleur.
- **Moyenne température (100–250 °C)** : séchage, production d'eau chaude ou de vapeur basse pression.
- **Haute température (> 250 °C)** : préchauffage de l'air de combustion, vapeur, séchage intensif, procédés
  thermiques. C'est le domaine où le stockage céramique est le plus pertinent.

Plus la température est élevée, plus la chaleur est « valorisable » (plus de débouchés, meilleur rendement).

## Pourquoi stocker la chaleur ?

La production de chaleur fatale et le besoin de chaleur ne sont souvent pas simultanés (arrêts, cycles de
production, besoins décalés). Un stockage tampon permet d'utiliser la chaleur plus tard.
L'autonomie du tampon se mesure en heures : puissance récupérable × nombre d'heures = énergie à stocker.

## Formules de base utilisées dans ThermoScout

- Puissance thermique disponible (kW) = débit (Nm³/h) × masse volumique (kg/Nm³) × chaleur massique (kJ/kg.K)
  × (T fumées − T rejet) ÷ 3 600.
- La **température minimale de rejet** est la température sous laquelle on ne refroidit pas les fumées, pour
  éviter la condensation acide (point de rosée) qui corrode les équipements. Elle dépend du combustible.
- Énergie annuelle (MWh) = puissance (kW) × heures de fonctionnement ÷ 1 000.
- Économie annuelle = énergie évitée (MWh) × prix de l'énergie (€/MWh), où l'énergie évitée = chaleur valorisée
  ÷ rendement de la chaudière remplacée.
- CO₂ évité (t) = énergie évitée (MWh) × facteur d'émission (t/MWh).

## Vocabulaire

- **Nm³/h** : normo-mètre cube par heure, débit de gaz ramené aux conditions normales (0 °C, 1 atm).
- **PCI** : pouvoir calorifique inférieur d'un combustible.
- **kW / MWh** : puissance / énergie. 1 MWh = 1 000 kWh.
- **Temps de retour (payback)** : investissement ÷ économie annuelle.
- **Facteur d'émission** : masse de CO₂ émise par MWh de combustible. Valeur par défaut dans l'outil pour le
  gaz naturel : 0,205 t/MWh (modifiable dans l'onglet Paramètres).

## Les bons sites à cibler

Un site est intéressant si : la température des rejets est élevée (> 250 °C), le débit est important,
le fonctionnement est long (> 4 000 h/an), le besoin de chaleur existe sur place (séchage, vapeur, préchauffage)
et l'énergie évitée est chère. Les secteurs typiques : verre, ciment et chaux, céramique et briques,
métallurgie, agroalimentaire, chimie.
