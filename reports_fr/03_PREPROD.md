# PREPROD R1 — choix de la configuration de production (25/09/2026)

**Recommandation préenregistrée : `r2g + normaliseur`.** Les deux candidats sont éligibles. `r2g + normaliseur` a le plus
haut score conjoint sur le jeu A (372 contre 367), soit un écart de 5, juste au-dessus du seuil d'égalité fixé à 4.
**Aucune promotion n'a été faite : la décision de production vous revient.**

**Réserve importante (analyse complémentaire, non préenregistrée).** L'avance de r2g sur r2f est mince : 5 cas sur 380
réponses, dont un seul sur la graine S2. En revanche, sur les tâches générales (jeu B), r2g a davantage d'erreurs
confirmées que r2f : 24 et 17 contre 17 et 13. L'écart vient surtout des reformulations, où r2g recopie le texte au lieu
de le reformuler (7 et 6 fois sur 25, contre 3 et 2 pour r2f). Si ces tâches générales comptent pour vous,
`r2f + normaliseur` est l'alternative prudente : lui aussi est éligible et presque à égalité sur A.

## 1. Ce qui a été comparé

Le protocole a été fixé avant tout résultat (`work/core_4b_preprod_r1/PROTOCOLE.md`, copie signée dans `package/`).

| Code | Système | Adaptateurs |
|---|---|---|
| P0 | R2 + normaliseur (production actuelle) | R2 S1, R2 S2 |
| P1 | r2f + normaliseur | r2f S1, r2f S2 |
| P2 | r2g + normaliseur | r2g S1, r2g S2 |

Les 6 bras (3 systèmes × 2 graines) ont traité les mêmes 490 entrées normalisées, avec un décodage déterministe et au
plus 768 jetons. Le normaliseur est ici légitime, puisque ce sont les systèmes de production.

- **Jeu A (décide)** : les 190 cas neufs scellés de REP R1. Chaque réponse a reçu un jugement masqué qui porte à la fois
  sur le verdict, les statuts des faits, la cohérence et la justification ; une réponse incohérente compte comme une
  erreur.
- **Jeu B (veto seulement)** : les 300 cas historiques V1. Chaque réponse a été jugée par deux passes masquées
  indépendantes, selon la policy « fiable » du 20/09. Une erreur (FAIL) n'est confirmée que si les deux passes la
  retiennent.
- **Règles préenregistrées** :
  - D1 : score conjoint du candidat ≥ score de P0 + 10 sur A, pour S1 et pour S2 ;
  - D2 : erreurs confirmées du candidat − erreurs de P0 ≤ 15 sur B, pour S1 et pour S2 ;
  - choix : le plus haut total conjoint sur A ; si l'écart est ≤ 4, le candidat le moins incohérent ; en cas d'égalité
    persistante, r2f.

## 2. Exécution et intégrité

- **Pod** : POD_ID (RTX PRO 4500), 7 002 s, soit **environ 1,40 $**. Il s'est arrêté seul après la récupération
  des résultats, et son état EXITED a été confirmé. Aucun pod ne tourne à ce jour.
- **Porte d'équivalence parallèle** : 3 bras lancés simultanément ont produit exactement les mêmes séquences de jetons que
  le bras de référence lancé seul, sur **48 entrées sur 48**. Le calcul parallèle était donc autorisé.
  - Durées : 3 bras en 360 s, contre 313 s pour un seul bras.
  - Évaluation complète : environ 1,7 h au lieu d'environ 5,3 h estimées en séquentiel.
  - C'est la réponse à votre remarque sur la RTX PRO 4500 sous-utilisée : un seul modèle 4B n'occupe pas la carte, trois
    en même temps oui. Pendant la vague, j'ai observé en direct environ 27,5 Go et 89 % d'utilisation ; cette mesure
    n'a pas été archivée.
- **Générations** : 2 940, toutes terminées par EOS, aucune tronquée.
- **Preuve des entrées** : les 2 940 prompts évalués sont identiques aux entrées déclarées, reconstruites sur CPU
  (`A_ANALYSIS.json`).
- **Revérification locale avec décodeur** : chaque réponse retrouvée à l'identique à partir des jetons, empreintes des
  adaptateurs et porte revalidées (`LOCAL_RECHECK.json`).

## 3. Jeu A — 190 cas neufs, jugement masqué conjoint

Les 591 réponses distinctes ont été réparties en 5 lots et relues par 5 relecteurs masqués. Les réponses identiques
d'un bras à l'autre ont été fusionnées et l'ordre mélangé. Les jugements ont été verrouillés
(`review_A/A_LOCKED.json`) avant l'ouverture de la table de correspondance.

| Système | Graine | Conjoint | Verdict | Statuts | Cohérence | Incohérentes |
|---|---|---|---|---|---|---|
| R2 + normaliseur | S1 | 144 | 153 | 189 | 173 | 17 |
| R2 + normaliseur | S2 | 146 | 153 | 190 | 176 | 14 |
| r2f + normaliseur | S1 | 184 | 184 | 190 | 184 | 6 |
| r2f + normaliseur | S2 | 183 | 186 | 190 | 184 | 6 |
| r2g + normaliseur | S1 | **188** | 188 | 190 | 188 | **2** |
| r2g + normaliseur | S2 | **184** | 185 | 189 | 184 | 6 |

Scores conjoints par sous-ensemble :

| Système | Graine | « contredit » décisif (44) | Conflits (52) | CF/FC (16) | FU/UF (8) | Non-régression (94) |
|---|---|---|---|---|---|---|
| R2 + normaliseur | S1 | 39 | 15 | 2 | 7 | 90 |
| R2 + normaliseur | S2 | 40 | 15 | 2 | 8 | 91 |
| r2f + normaliseur | S1 | 44 | 48 | 13 | 8 | 92 |
| r2f + normaliseur | S2 | 44 | 48 | 15 | 8 | 91 |
| r2g + normaliseur | S1 | 44 | 52 | 16 | 8 | 92 |
| r2g + normaliseur | S2 | 44 | 48 | 13 | 8 | 92 |

- **Totaux conjoints (S1 + S2)** : R2 290, r2f 367, r2g 372.
- **Réponses incohérentes** : R2 31, r2f 12, r2g 8.
- **Accord avec le classifieur automatique v2** sur le verdict initial : 591 sur 591 ; aucune correction de verdict_ok.
- **Contrôle direct** : 11 cas départagent r2f et r2g, dont 4 reposent sur un jugement de cohérence (A0257, A0033,
  A0316, A0562). Je les ai relus : les notes tiennent, et la même phrase fautive est sanctionnée pareillement chez r2f et
  chez r2g. Une recherche d'incohérences manquées parmi les réponses jugées correctes n'en a trouvé aucune.
- **Erreur dominante restante** : les dossiers à sources opposées, surtout la combinaison « un fait requis faux + un fait
  en conflit ». Certaines réponses annoncent « Contradiction », ce qui compte comme une erreur (convention
  préenregistrée), ou concluent « indéterminé » alors qu'un seul fait faux suffit.

## 4. Jeu B — 300 cas historiques, veto

108 paires cas × graine (55 en S1, 53 en S2) ont reçu trois réponses identiques. Elles n'ont pas été jugées, car elles
comptent de la même façon pour les trois systèmes. Les 492 éléments restants ont été jugés deux fois par 22 juges
distincts (11 par passe, étiquettes permutées entre les passes). Toutes les citations d'erreur étaient exactes, et aucun
FAIL n'a été rétrogradé. Les jugements sont verrouillés dans `review_B/B_LOCKED.json`.

| Système | Graine | PASS | FAIL confirmés | Non résolus |
|---|---|---|---|---|
| R2 + normaliseur | S1 | 215 | 14 | 16 |
| R2 + normaliseur | S2 | 224 | 11 | 12 |
| r2f + normaliseur | S1 | 215 | 17 | 13 |
| r2f + normaliseur | S2 | 221 | 13 | 13 |
| r2g + normaliseur | S1 | 212 | 24 | 9 |
| r2g + normaliseur | S2 | 214 | 17 | 16 |

Veto D2, c'est-à-dire l'écart d'erreurs confirmées avec P0 (limite 15) : r2f **+3 / +2**, r2g **+10 / +6**. Les deux
passent.

## 5. Décision (règles appliquées mécaniquement, `PREPROD_FINAL.json`)

| Candidat | D1 en S1 (≥ P0 + 10) | D1 en S2 | D2 en S1 (≤ 15) | D2 en S2 | Éligible |
|---|---|---|---|---|---|
| r2f + normaliseur | 184 contre 154 : oui | 183 contre 156 : oui | +3 : oui | +2 : oui | oui |
| r2g + normaliseur | 188 contre 154 : oui | 184 contre 156 : oui | +10 : oui | +6 : oui | oui |

Choix : le plus haut total conjoint sur A, 372 contre 367. L'écart de 5 dépasse le seuil de 4, donc **r2g +
normaliseur**. Si le départage par la cohérence avait été appliqué, il aurait aussi désigné r2g (8 incohérences contre
12).

## 6. Analyse complémentaire (post-hoc, non préenregistrée)

Voir `POSTHOC_B_ANALYSIS.json`. Cette analyse ne modifie pas la décision ci-dessus.

- **Erreurs propres à r2g** : 16 cas-graines où r2g a une erreur confirmée que r2f n'a pas.
  - 9 sont des reformulations : 7 copies de la source et 2 attributions « une note récente » retirées.
  - 4 portent sur le raisonnement sur des conditions : une priorité inventée entre règles, une condition fausse traitée
    comme inconnue, un raisonnement erroné et un doute inventé.
  - Les 3 autres sont : un nom d'outil inventé, un e-mail sans la mention « décision non prise » et un mauvais numéro de
    bon de commande.
- **Mesure objective des copies** : réponse égale au texte source, ponctuation et casse mises à part, sur les 25 tâches
  de reformulation.

  | Système | Copies S1 | Copies S2 |
  |---|---|---|
  | R2 + normaliseur | 2 | 1 |
  | r2f + normaliseur | 3 | 2 |
  | r2g + normaliseur | **7** | **6** |

  L'effet se reproduit sur les deux graines.
- **Erreurs confirmées par catégorie** (S1 P0/P1/P2 | S2 P0/P1/P2) :
  - reformulation : 4/3/8 | 2/1/5 ;
  - suivi de procédure : 0/2/4 | 1/2/3.

  Les autres catégories sont proches.
- **Lecture** : l'origine n'est pas établie. Hypothèse à vérifier : les 80 lignes ajoutées par r2g, riches en citations
  littérales, renforceraient la recopie. Le nouveau benchmark général devra le tester.

## 7. Limites

- **Jeu A** : un seul relecteur par réponse. Les conventions varient un peu d'un relecteur à l'autre, mais les réponses
  sont réparties au hasard entre les bras, et les cas décisifs ont été relus.
- **« Contradiction » comptée comme erreur** : c'est la convention préenregistrée, et c'est une grande part des erreurs
  de R2 + normaliseur.
- **Jeu REP R1 consommé** : les 190 cas sont désormais ouverts et ne peuvent plus servir de test neuf.
- **Jeu B** : les juges sont des modèles appliquant la policy 1.0. Les cas non résolus (9 à 16 par système et graine) ne
  comptent pas, conformément au protocole. Le jeu B pèse volontairement moins que le jeu A (veto seulement).
- **Métrique de copie** : c'est une heuristique, mais les juges B ont constaté les copies indépendamment, par comparaison
  exacte.

## 8. Coût et budget

- **PREPROD** : environ 1,40 $. Solde estimé : **environ 11,15 $** (13,92 $ annoncés, moins 1,37 $ pour R2GEVAL et
  1,40 $ pour PREPROD, hors stockage du volume). La règle d'un solde restant ≥ 3 $ est respectée.
- **Jugements masqués** : faits par des agents Claude, sans GPU et sans coût RunPod.

## 9. Suites proposées

1. **Votre décision** : `r2g + normaliseur` (recommandation préenregistrée) ou `r2f + normaliseur` (alternative prudente
   pour les tâches générales). Rien n'a été promu ; R2 S1/S2 restent les points de référence.
2. **Un nouveau benchmark général jamais touché**, incluant des reformulations pour vérifier la recopie.
3. **Arrêt des entraînements ciblés « contredit »** ; DPO ou apprentissage contrastif plus tard, si besoin.
4. **Toute campagne (Pod ou PC) uniquement sur votre accord explicite.**

## Fichiers

| Fichier | Contenu |
|---|---|
| `PREPROD_FINAL.json` | Décision |
| `A_BLIND_SUMMARY.json`, `review_A/A_LOCKED.json` | Jeu A |
| `B_SUMMARY.json`, `review_B/B_LOCKED.json` | Jeu B |
| `A_ANALYSIS.json` | Preuve des entrées, classifieur, porte |
| `LOCAL_RECHECK.json` | Revérification avec décodeur |
| `POSTHOC_B_ANALYSIS.json` | Analyse complémentaire |
| `results/BACKUP_VERIFIED.json`, `POD_STOPPED.json` | Sauvegarde et arrêt du pod |

Scripts : `work/core_4b_preprod_r1/`.
