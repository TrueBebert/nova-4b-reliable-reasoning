# R2F R1 — seconde passe masquée (Claude, 25/09/2026)

## Méthode

Méthode identique à R2C, R2D et R2E.

**Préparation** (`work/core_4b_r2f_r1/make_blind_pass.py`)
- Sous-ensembles décisifs : 44 cas « contredit » décisifs faux, 22 cas R3, 32 conflits.
- Pour ces cas, les réponses des 6 bras sont fusionnées quand elles sont identiques : 396 réponses uniques.
- Bras masqués, ordre tiré avec une graine fixe, 3 lots disjoints.

**Relecture**
- 3 relecteurs indépendants (sous-agents), avec le guide `work/core_4b_r2f_r1/BLIND_REVIEW_GUIDE.md` et le verdict attendu.
- Chacun lit **seulement** son lot.
- Champs : verdict initial, statuts, cohérence, justification, gravité.

**Verrouillage** (`lock_blind_pass.py`) : les décisions sont figées et leur empreinte enregistrée. La table privée n'est ouverte qu'ensuite.

## Résultats

| Mesure | Résultat |
|---|---|
| Accord avec le classifieur automatique | **396/396** |
| Erreurs de saisie des relecteurs | 0 |

**Jugement conjoint** (verdict, statuts, cohérence et justification tous justes) :

| Bras | H1 (44) | R3 (22) | Conflits (32) | FU/UF (8) | CF (4) | Erreurs majeures H1 et R3 |
|---|---|---|---|---|---|---|
| r2f S1 | 44 | 22 | 28 | 8 | 0 | 0 |
| r2f S2 | 44 | 22 | 30 | 8 | 2 | 0 |
| r2e S1 | 35 | 22 | 25 | 4 | 0 | 8 |
| r2e S2 | 41 | 21 | 26 | 8 | 0 | 2 |
| R2 S1 | 5 | 3 | 10 | 0 | 0 | 58 |
| R2 S2 | 0 | 0 | 5 | 0 | 0 | 66 |

## Lecture de CF (r2f)

**S1**
- Statuts justes 2/4 : les cas « dément ».
- Verdict cohérent 2/4 : dans les cas « dément », Q est lu faux mais la conclusion reste « indéterminé ». **C'est l'erreur de règle.**

**S2**
- Statuts justes 2/4 : dans les cas « contredit », Q est lu inconnu. **C'est l'erreur lexicale.**
- Cohérence 4/4 : la conclusion suit les statuts, même quand ils sont faux.

## Observations des relecteurs (tous bras confondus)

- L'erreur dominante, surtout sur R2, est de lire « contredit » ou « dément » à source unique comme un conflit. Il y a parfois une source inventée (« l'un affirme, l'autre nie »).
- Les réponses « irrecevable » sont toujours justes. Toutes les erreurs sont des refus de trancher (« Contradiction » ou « indéterminé »), jamais une fausse recevabilité.

## Limites

- Les relecteurs connaissent le verdict attendu. La passe mesure la justesse du raisonnement, pas un jugement indépendant du gold.
- Les gold ont par ailleurs été recalculés indépendamment : 170/170.
