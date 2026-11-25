# TOOLTRAIN R1 : entraînement avec l'outil dans la boucle, résultats (29/09/2026)

## En bref

- **Verdict préenregistré : `SIGNAL_POSITIF_DEV`, sur une seule graine (A).**
  - La graine B a été interrompue par un crash du PC à la mise à jour 81 sur 184. L'utilisateur a décidé de conclure
    sur A.
- **Le candidat pose bien mieux les calculs à plusieurs étapes**, y compris sur des formulations jamais vues.
- **Il change toutefois le texte de 291 réponses sans calcul**, sans perte mesurable par le code. Une relecture
  masquée s'impose avant toute suite.
- **Production inchangée.** GENBENCH2 reste scellé. Aucun Pod, coût nul.

## Déroulement

- **Préparation** : 736 lignes d'entraînement.
  - 360 trajectoires avec appel d'outil et 8 refus, sur 12 familles, avec des formulations nouvelles.
  - 184 rejeux de R2F avec l'outil proposé mais non appelé, et 184 rejeux standard.
  - Contrôle de fuite vis-à-vis de GENBENCH2, par code et en comptes seulement : 52 lignes remplacées, puis 0 recouvrement.
  - Tests CPU : 24 sur 24.
- **V1 (14:09 UTC)** : porte arrêtée par manque de mémoire, au deuxième chargement du modèle. Aucun entraînement.
  Correction consignée dans `AMENDEMENT_V2.md`, sans changement de méthode.
- **V2 (14:29 UTC)** :
  - Porte PASS : gradients identiques à la référence (écart 0,0).
  - Graine A entraînée en 49 min, perte de 0,26 à environ 0,05.
  - Évaluation de 968 cas en 75 min, puis R2F sur H (92 cas).
- **Graine B** : démarrée, puis très ralentie, la carte étant saturée (11,8 Go sur 12,2 avec les applications de
  bureau). Elle a été interrompue par le crash du PC. Elle n'a ni adaptateur ni évaluation (`STOPPED_LOCAL_V2.json`).

## Calcul, dates, transformations (réponses du système avec l'outil, contre R2F avec le même outil)

| Jeu | R2F | Candidat |
|---|---|---|
| P, dev (42) | 25 | **36** |
| E, jamais vus en entraînement (142) | 95 | **113** |
| H, formulations réservées (92) | 74 | **88** |
| **Total (276)** | **194** | **237** |

- **Bilan** : 58 gains robustes pour 15 régressions (p ≈ 4·10⁻⁷). Aucune famille n'est en perte nette.
- **Le gain porte là où c'était visé** (familles à plusieurs étapes, bonnes valeurs finales) :

  | Famille | R2F | Candidat |
  |---|---|---|
  | Calendrier | 9/40 | 26/40 |
  | Transformation | 12/40 | 30/40 |
  | Centimes | 21/40 | 27/40 |

  Les familles simples étaient déjà au plafond.
- **Les 15 régressions** : 7 en centimes, 3 en calendrier (décalage d'un jour), 3 en transformation (tous les chiffres
  masqués), 2 en pourcentage (dont un « 73.5 » sans le symbole %).

## Préservation (réponses sans outil sur les 690 tâches non calculatoires)

- **Critères préenregistrés remplis** :
  - égalité exacte de 218 à 221 (5 perdues, 8 gagnées) ;
  - verdicts de logique : aucun changement de justesse sur 180 ;
  - aucune balise d'outil.
- **Mais 291 réponses sur 690 ont changé de texte.** C'est une limite importante, que les critères de code ne mesurent
  pas.
  - **Logique** : 149 réponses changées, toutes avec le même verdict ; seul le motif est reformulé.
  - **Rédaction et JSON** : surtout des paraphrases, mais aussi quelques changements de fond. Par exemple, un choix
    d'action rendu dans un autre format JSON avec des arguments inventés, ou une valeur fausse sans outil sur une tâche
    « manquant » (7.41 au lieu de 8.41).
- **Invariance face à l'outil proposé : pas d'amélioration** (47 → 49 réponses changées par la seule présence de
  l'outil).
- **Sans outil, le candidat calcule un peu moins bien** que R2F (99 → 93 sur 276) : il compte sur l'outil.

## Ce que cela veut dire

1. **L'entraînement avec l'outil dans la boucle marche pour la mise en équation.** Le gain est large et tient sur des
   formulations jamais vues.
2. **Il modifie aussi le style de nombreuses réponses sans calcul.** Le rejeu ne l'a pas empêché. Tant qu'une
   relecture masquée n'a pas jugé ces changements, on ne peut pas affirmer qu'il n'y a pas de régression.
3. **Une seule graine** : la stabilité reste à vérifier, puisque R3 avait montré des écarts entre graines.

## Suite proposée (chaque étape sur accord)

1. **Relecture masquée des réponses sans calcul qui ont changé**, en priorité les 142 hors logique, qui portent le
   risque de fond. Les motifs de logique suivraient, par échantillon.
2. **Rejouer la graine B**, sur un Pod ou avec le PC libre, pour vérifier la stabilité. En local, il faudra réduire
   l'empreinte mémoire : la carte de 12 Go était au maximum et le PC a planté.
3. **Si ces deux points sont bons** : inclure le candidat, avec et sans outil, dans la campagne GENBENCH2 unique, à
   côté de la production et de la production avec outil.

## Limites

- Évaluation de développement sur des jeux synthétiques, avec les familles de l'entraînement. La généralisation n'est
  testée que par des formulations nouvelles.
- Une seule graine, un seul passage en décodage glouton.
- Préservation notée par le code seulement.
- L'aiguilleur A figé n'aiguille pas 4 cas de H (formulation « a varié »).
- Incidents d'exécution : porte V1 arrêtée par manque de mémoire, puis crash du PC pendant la graine B.

## Preuves

- **Décision** : `RESULTS.json`.
- **Détails et liste des réponses changées** : `INSPECTION.json`.
- **Réponses brutes** : `results_v2/eval_tt_20260930/responses.jsonl` et `results_v2/eval_r2f_H/responses.jsonl`.
- **Entraînement** : `results_v2/train_20260930/status.json`, adaptateur `f7c62313…`.
- **Porte** : `results_v2/gate/TT_GATE.json`.
- **Protocole et amendement** : `package_v2/PROTOCOLE.md` et `package_v2/AMENDEMENT_V2.md`.
- **Données et fuite** : `DATA_MANIFEST.json`, `LEAK_CHECK_CLEAN.json` et `CLEANING.json`.
- **Arrêt de B** : `STOPPED_LOCAL_V2.json`.
