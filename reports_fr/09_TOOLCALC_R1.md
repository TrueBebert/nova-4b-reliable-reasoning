# TOOLCALC R1 : résultats (29/09/2026)

**Exécution.** Sur la RTX 5070 locale, le 29/09 de 01:46 à 03:37 (heure locale), à la demande de l'utilisateur :
(accord explicite de l'utilisateur). Coût : 0 $.

- R2F S1 : 334 cas sur 334 ; la base : 44 sur 44.
- Aucune erreur technique ; toutes les preuves d'entrée ont concordé au jeton près.

## Verdict préenregistré : `APPORT_AVEC_RESERVES`

- **Condition CALCUL : remplie, et largement.**
- **Condition DÉGRADATION : non remplie.** Sur les autres tâches (C), on compte 1 balise d'outil dans une réponse
  finale (maximum toléré : 0) et 6 réponses manquantes (maximum toléré : 2).

## Calculs, dates et transformations (R2F S1, bonne valeur finale)

| Jeu | Sans outil | Avec outil | Gains | Régressions | Test des signes |
|---|---|---|---|---|---|
| P, dev (42) | 13 | 25 | 13 | 1 | p = 0,002 |
| E, jamais vus (142) | 46 | 95 | 50 | 1 | p ≈ 5·10⁻¹⁴ |
| **P + E (184)** | **59** | **120** | **63** | **2** | **p ≈ 10⁻¹⁶** |

- **Réponses exactes au caractère près** : de 41 à 103.
- **Les 63 gains sont robustes** : la réponse sans outil n'énonçait jamais la bonne valeur. J'ai aussi vérifié à la
  main un échantillon de valeurs extraites.

**Par famille**, dans l'ordre « sans outil → avec outil » :

- **Les calculs simples sont entièrement corrigés.** Chacune de ces familles passe à 12/12 :

  | Famille | Avant | Avec outil |
  |---|---|---|
  | montant | 5 | 12/12 |
  | remise | 3 | 12/12 |
  | durée | 5 | 12/12 |
  | décalage de date | 9 | 12/12 |
  | pourcentage | 11 | 12/12 |
  | total incomplet | 10 | 12/12 |

- **Les tâches à plusieurs étapes progressent, mais restent faibles** :

  | Famille | Avant | Avec outil |
  |---|---|---|
  | centimes | 1 | 14/32 |
  | calendrier | 1 | 9/32 |
  | transformation | 0 | 10/32 |

- **Pourquoi ces tâches restent faibles.** Sur les 64 échecs restants, 48 sont des programmes qui tournent mais sont
  mal posés : unités consommées mal traitées, décalage d'un jour, mauvais chiffres masqués. L'outil supprime les
  erreurs d'arithmétique, pas les erreurs de compréhension de la règle.

**Les 2 régressions**, vérifiées une par une :

- `T2-dev-centimes-0-0-0` : l'outil donne 71.16 EUR au lieu de 75.76 EUR. Le calcul est mal posé, alors que la
  réponse directe était juste.
- `G-variation_signee-02` : le code affiche « +--23 », puis le modèle répond -12 au lieu de -23.

## Autres tâches (C, 148 cas) : la raison de la réserve

- **R2F appelle l'outil là où il ne sert pas** : dans 73 cas sur 148, surtout en logique et en règles.
  - Logique L : 25 cas sur 40.
  - Module logique : 7/8 ; portée : 8/8 ; manquant : 8/8.
- **Les 6 réponses manquantes sont toutes en logique.**
  - Le modèle réessaie en boucle un code invalide : guillemets échappés `\"`, ou bug répété.
  - Une fois, l'appel est tronqué : la balise d'outil se retrouve dans la réponse.
  - Conséquence sur les verdicts L : 40/40 sans outil, 37/40 avec l'outil.
- **3 réponses sont détournées en JSON « d'action d'agent »**, contre 2 sans outil. Exemple :
  `{"action": "respond", "tools": []…}` à la place de la liste demandée.
- **En face, il y a des corrections.**
  - L'erreur critique de R3 est corrigée : `G-remplacement_regle-11` donne REFUSE et non plus ACCEPTE.
  - `G-sources_conflit-10` et 2 cas de logique du module sont aussi corrigés.
- **Bilan par le code** : égalité exacte de 42 à 44 (+9/−7) ; sur les réponses courtes, +4/−4.
- **100 réponses sur 148 ont changé.** Seule une relecture masquée pourrait juger leur fond.

## Modèle de base (repère, P seulement)

- **Bonne valeur** : 13 sans outil, 30/42 avec, contre 25 pour R2F avec outil.
- **Réponses exactes** : 5 sans outil, 23 avec.
- **5 appels illisibles**, qui laissent des balises dans la réponse.
- **Lecture** : l'adaptation R2F n'a pas détruit l'usage natif des outils. Ce n'est qu'une indication, sur 42 cas.

## Ce que cela veut dire

1. **Un outil de calcul est la bonne réponse aux erreurs d'arithmétique et de dates.** Le gain est net, reproduit sur
   142 cas jamais vus, avec seulement 2 régressions.
2. **Il ne corrige pas la compréhension des règles à plusieurs étapes.** Là, le levier reste les données et
   l'entraînement, avec l'outil dans la boucle.
3. **Tel quel, l'outil ne doit pas être proposé sur toutes les requêtes.** Sur la logique et les verdicts, il fait
   perdre des réponses.

## Suite proposée (chaque étape sur ton accord)

1. **TOOLCALC R2 : corriger l'intégration, pas le modèle.** Sur CPU, puis un run local gratuit.
   - Ne proposer l'outil que pour les demandes de calcul, de date ou de transformation.
   - Arrêter les relances de code identiques.
   - Tolérer les guillemets échappés.
   - Ces corrections viennent de l'inspection de ce run : elles devront être évaluées sur des cas neufs, pas sur C.
2. **Confirmer ensuite sur un test scellé**, par exemple la catégorie « calculs_dates » de GENBENCH2.
3. **Traiter plus tard la mise en équation des règles à plusieurs étapes** : données d'entraînement avec l'outil dans
   la boucle.

**Production inchangée** : R2F S1 + normaliseur.

## Limites

- **Évaluation de développement.**
  - P avait déjà servi à la relecture R3.
  - Tous les jeux sont synthétiques et viennent d'un seul auteur.
  - Il n'y a eu qu'un seul passage, en décodage glouton.
- **C n'est noté que par le code.**
- **Inspection faite après coup.** L'inspection (`INSPECTION.json`) est descriptive ; elle ne modifie pas la décision
  préenregistrée.
- **Coût en temps.** L'outil multiplie le temps de génération par 8 environ : 4 582 s contre 578 s pour R2F.

## Preuves

- **Décision** : `RESULTS.json`.
- **Détails** : `INSPECTION.json`.
- **Réponses brutes** : `results/<modèle>/responses.jsonl`.
- **Collecte vérifiée** : `COLLECTED.json`.
- **Autorisation et lancement** : `AUTHORIZATION_LOCAL.json` et `LAUNCHED_LOCAL.json`.
- **Protocole** : `package/PROTOCOLE.md`.
