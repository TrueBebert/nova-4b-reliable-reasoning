# TOOLTRAIN R2 : rapport de campagne (30/09/2026, Opus 5.5)

**Verdict pré-enregistré : `NON_RETENU`.** Les deux graines échouent aux règles de non-régression :
- la porte F1 détecte 4 à 6 nouvelles erreurs de fond par réponse, pour une limite de 0 ;
- HM R1 et R6 échouent : valeurs inventées, dont deux par l'outil.

Le gain de calcul est nettement acquis : +40 et +38 en gain robuste net, p < 10⁻⁵. L'intégrité de campagne est entière ; le
résultat est donc concluant. Production inchangée (R2F S1 + normaliseur) ; aucune promotion ; GENBENCH2 reste scellé.

## Campagne

| Élément | Valeur |
|---|---|
| Accord | (accord explicite de l'utilisateur) |
| Pod | `POD_ID`, RTX PRO 4500 Blackwell, EU-RO-1, 0,72 $/h ; la PRO 4000 a été refusée trois fois faute d'instance |
| Paquet | `package_v5`, manifeste `27d23f3e…` ; archive `8be8c958…` |
| Contrôles avant démarrage | capacité 12.0 ; versions d'entraînement et d'évaluation conformes ; bac à sable Linux conforme ; autotest d'arrêt POSIX réussi |
| Durées | porte 7 min ; entraînement A 48 min ; évaluation A 74 min ; R2F 29 min ; entraînement B 47 min ; évaluation B 72 min ; total 4 h 37 |
| Budget | 47 100 s autorisées ; tous les contrôles avant étape passés |
| Coût | 16 958 s au plus, soit **3,39 $** ; solde estimé ensuite ≈ 10,98 $ (estimation prudente) |
| Résultats | `results.zip` (`7147e655…`, 55 fichiers, dont les deux adaptateurs), rapatrié et vérifié ; copie durable sur le volume réseau |
| Analyse | `analyze_r2.py` v5 : **aucun problème d'intégrité** (`RESULTS_R2.json`, `R2_SUMMARY.json`) |

## Règles par graine

| Règle | Graine A (20261002) | Graine B (20261003) |
|---|---|---|
| **CALCUL** (P+E+H, réponses servies) | **PASS** : VF 194 → 234/276 ; 57 gains, 17 régressions ; net +40 ; p = 3,4·10⁻⁶ | **PASS** : VF 194 → 232 ; 49 gains, 11 régressions ; net +38 ; p = 7,6·10⁻⁷ |
| HM R1, nouvelles erreurs | **FAIL** : 6 certaines (réponse directe) + 1 valeur inventée par l'outil | **FAIL** : 4 (directe) + 2 (servie) + 1 valeur inventée par l'outil |
| HM R2, incomplets signalés | PASS : 41/48 directe, 44/48 servie (R2F : 44 et 36) | PASS : 43 et 44 |
| HM R3, complets justes (servie) | en attente : 43 (+1 non interprétable) ; R2F : 42 | **FAIL** : 40 (+2) sur un seuil de 44 |
| HM R4, refus en trop | en attente | **FAIL** : 3 refus |
| HM R5, conventions | en attente | en attente |
| HM R6, appels sur incomplets | **FAIL** : 3 appels ; l'un finit sur une valeur inventée | **FAIL** : 2 appels ; l'un finit sur une valeur inventée |
| **PORTE** (F1 strict) | **ÉCHOUÉE** : F1 = 4 (directe), 5 (servie) ; 12 corrections dans chaque réponse | **ÉCHOUÉE** : F1 = 6, 4 ; 12 corrections dans chaque réponse |
| F2 à F6 | pertes de forme 1 et 7, gains 35 et 36 ; F3 0 ; F5 0 ; F6 conforme | pertes 3 et 4, gains 30 et 33 ; F3 0 ; F5 0 ; F6 conforme |

## Relecture ciblée des erreurs certaines

Ce sont bien des erreurs, pas des artefacts de l'oracle.

- **Famille `manquant` (développement), dans les deux graines**
  - Le candidat répond `{"cible": null}` là où R2F signalait `MANQUANT:clé`.
  - Il invente une valeur : `"18.65"` pour un volume dont une donnée manque.
  - Il répète l'erreur déjà vue en R1 : 8.41 → 7.41.
- **Graine B** : réponse réduite au seul gabarit en `ligne_exacte` (déjà vu en R1), `CONFLIT` au lieu de 35, `REFUS` au lieu
  d'`ACCORD`.
- **HM, cas complets** : montants faux (464,82 et 484,82 au lieu de 584,82), dates décalées de 1 à 3 jours, une date
  impossible (`2028-07-40`), durée 217 au lieu de 337.
- **HM, cas incomplets** : valeurs inventées dans la réponse directe (100,00 €, 0,00 €).
- **Outil sur incomplets** : dans les deux traces relevées, le code fixe lui-même l'opérande manquant
  (`montant_initial = Decimal("100.00")`, `montant_3 = …`), puis affiche le résultat, repris dans la réponse finale.

## Lecture

Ce qui suit est descriptif ; seule la règle décide.

- **Ce que R2 garde et améliore** :
  - le gain de calcul outillé de R1 (R1, graine A : net +43) ;
  - le signalement des entrées manquantes dans les conventions réservées de HM, en réponse servie : 44/48 contre 36 pour
    R2F ;
  - plus de réponses directes justes sur les complets de HM : 27–28 contre 17, R2F refusant souvent.
- **Ce que R2 ne corrige pas** :
  - les erreurs de fond de R1 sur la convention de développement `MANQUANT` ; elles changent seulement de forme (cible
    `null` au lieu du signal) ;
  - l'invention d'opérandes par l'outil sur des cas incomplets, rare (1 cas par graine) mais présente.
- **Pas d'attribution causale** : R2 compare des recettes globales.

## Suite

- **Relecture masquée** : le verdict ne dépend pas des 516 éléments de `REVIEW_SCOPE.jsonl`. Les échecs reposent sur des
  erreurs certaines notées par code et confirmées par la relecture ciblée ci-dessus. Cette relecture n'est donc pas
  nécessaire ; elle reste possible à titre descriptif.
- **Adaptateurs** : les deux adaptateurs sont conservés comme preuves, sans usage.
- **Pod** : il est arrêté (`EXITED`), pas supprimé. La copie durable des résultats occupe environ 340 Mo sur le volume réseau.
- **Pistes, sous réserve d'accord** :
  - traiter la convention `MANQUANT` du développement comme une cible explicite de l'entraînement ;
  - interdire par construction les opérandes inventés dans le code (valeur absente = signal) ;
  - ou abandonner l'entraînement outillé au profit de l'intégration sans entraînement déjà retenue (aiguilleur A + repli),
    à confirmer sur GENBENCH2.
