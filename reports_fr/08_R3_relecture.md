# R3 : résultat de la relecture sémantique masquée (29/09/2026)

## Déroulement

- **Relecteurs** : deux, indépendants et à l'aveugle — Astra (GPT) et Sonnet (Claude).
- **Matière relue** : 238 réponses distinctes sur 190 cas ; les autres étaient identiques à la référence.
- **Verrouillage** : chaque relecteur a verrouillé avant la levée du masque (empreintes vérifiées) :
  - Astra : `73fe70ff…`, 149 jugements marqués à adjuger ;
  - Sonnet : `a8fd4815…`, 42 marqués.
- **Levée du masque** : `unblind.py` ; chiffres complets dans `UNBLINDED.json`. La liste des divergences, toujours masquée,
  est dans `DIVERGENCES.json`.

## Accord entre relecteurs

- Jugement de fond identique pour 87 % des réponses (kappa de Cohen 0,78).
- Erreur critique identique pour 97 % des réponses.
- 36 réponses divergent.

## Résultats (consensus, sur 190 cas)

| Modèle | Fond correct | Incorrect | À adjuger | Erreurs critiques |
|---|---|---|---|---|
| R2F initial | 142 | 29 | 15 | 28 |
| Témoin V5, graine 28 | 148 | 33 | 9 | 29 |
| Témoin V5, graine 29 | 150 | 30 | 10 | 26 |
| Mix R3, graine 28 | 150 | 29 | 11 | 25 |
| Mix R3, graine 29 | 151 | 29 | 10 | 25 |

**Mix R3 contre son témoin, cas par cas :**

| Graine | Gains | Régressions | Erreurs persistantes | À adjuger |
|---|---|---|---|---|
| 28 | 3 | 1 | 26 | 14 |
| 29 | 3 | 3 | 24 | 14 |

Chaque relecteur, pris seul, donne entre 5 et 6 gains pour 2 à 6 régressions. Le sens est le même.

## Régressions critiques vérifiées

Chaque extrait a été relu et le calcul refait par code.

1. **`G-remplacement_regle-11`**, sur **les deux graines**.
   - Le mix répond « ACCEPTE » alors que la note remplace le maximum par 26, borne comprise, pour un lot de 27. La bonne
     réponse est REFUSE.
   - Les deux témoins sont justes. R2F initial commettait la même erreur : le mix n'a pas acquis la correction que la
     répétition V5 donne au témoin.
2. **`N-12-remise_puis_frais`**, graine 29 : le mix répond 11.40 EUR au lieu de 37.20 EUR (42.50 × 0,8 + 3.20).
3. **`T2-dev-centimes-1-1-0`**, graine 29 : le mix répond 115.60 EUR au lieu de 87.71 EUR ; le témoin de la même graine
   trouve le bon montant. Sur la graine 28, les deux bras se trompent.

## Conclusion

- **Aucun signal positif pour R3.** Le protocole est explicite : une régression critique vérifiée bloque tout signal
  scientifique positif et toute revendication de maintien.
- **Le gain vu à l'égalité exacte sur le module était surtout un effet de forme.** Sur le fond, les témoins donnaient déjà
  souvent des réponses justes formulées autrement. L'écart net de fond n'est que de +2 et +1 cas.
- **Décision :** la stratégie « module de transfert à la place de 144 répétitions V5 » n'est pas retenue. Production
  inchangée : R2F S1 + normaliseur.
- **Faiblesses communes à tous les modèles, R2F compris :** calculs en centimes, transformations et dates. Cela rejoint
  BASECOMP et oriente la suite vers l'évaluation d'un outil de calcul exact, troisième point de l'ordre fixé par le
  relecteur externe.

## Limites

- **Divergences non adjugées** : 36 réponses divergent encore. Leur adjudication préciserait les chiffres, mais ne peut pas
  lever le blocage dû aux régressions critiques vérifiées.
- **Exposition des relecteurs** : les deux relecteurs avaient vu un résumé agrégé de R3 avant de relire, sans jamais savoir
  quel modèle avait produit chaque réponse.
- **Défaut du kit** : les sauts de ligne n'étaient pas visibles. Un contrôle par code l'a compensé : les quatre modèles
  entraînés reproduisent la structure de lignes de la référence dans les 190 cas.
- **Portée** : dev ouvert, synthétique, écrit par un seul auteur. Ce n'est ni un test externe ni un test du métier.
