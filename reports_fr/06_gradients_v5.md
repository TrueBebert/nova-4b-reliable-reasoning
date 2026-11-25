# Test v5 : choix du runtime d'entraînement (Opus 5.5, 28/09/2026)

Choix délégué : (accord explicite de l'utilisateur).

- **Pod :** `POD_ID`, RTX PRO 4000 (même carte qu'en v4), 32 min, ≈ 0,30 $. Arrêt opérateur après une sauvegarde
  vérifiée ; statut EXITED confirmé.
- **Règles :** figées avant le lancement (`REGLES_V5.md`, sha256 `1336b044…`).
- **Chiffres :** `RESULTS_V5.json`, `results/mode_CMP/COMPARISONS.json`.
- **Périmètre :** aucun entraînement réel, aucune promotion.

## Pourquoi ce test

La lecture du code d'Unsloth 2026.8.15 montrait trois mécanismes actifs même sans compilation :
- ses propres noyaux Triton `fla` pour les couches Gated DeltaNet ;
- un réglage de ces noyaux qui réutilise la première configuration pour toute nouvelle forme ;
- un cache de compilation conservé d'un processus à l'autre (Mega-cache).

Chaque mode change une seule variable d'environnement.

## Résultats (écart L2 au vrai gradient float32)

| Mode | Trainer, groupe 0 | Trainer, groupe 1 | Stable | Selon les règles | Temps pour 6 lignes |
|---|---|---|---|---|---|
| Vérité float32 recalculée | 0 | 0 | exacte | — | 11–14 s |
| bf16 standard (transformers) | 0,110 | 0,099 | exacte | référence ; seuils 0,165 / 0,149 | 11,3 s |
| UE : sans compilation (noyaux `fla` d'Unsloth) | 0,059 | **0,187** | oui | non valide | 1,5 s |
| UEN : UE sans réutilisation de réglage | 0,058 | **0,186** | oui | non valide | 1,5 s |
| **UEF : sans compilation, Gated DeltaNet en torch pur** | **0,126** | **0,075** | **oui (≈ 1,2 %)** | **valide** | 6,7 s |
| UCC : compilation, caches coupés, sans réutilisation | 0,129 | 0,121 | **non** | non valide | 1,4 s |

Précisions :
- UE reproduit v4 à 0,001 près (0,059 et 0,187 contre 0,060 et 0,186).
- Les entrées sont identiques dans les 5 modes (même sha256).

## Ce que ça montre

1. **L'excès du groupe 1 vient des noyaux `fla` d'Unsloth eux-mêmes**, pas de la réutilisation de leur réglage (UEN ne
   change rien). Avec le Gated DeltaNet en torch pur, le groupe 1 tombe à 0,075, mieux que le bf16 standard.
2. **La compilation reste instable, même sans aucun cache ni réutilisation.**
   - Cette fois, c'est le tout premier calcul du processus qui tombe dans l'état faux (0,333 sur le groupe 0).
   - Un entraînement compilé pourrait donc démarrer dans cet état.
   - L'instabilité est propre au chemin compilé.

## Décision (règles figées)

**Runtime R3 = UEF** : `UNSLOTH_COMPILE_DISABLE=1` et `UNSLOTH_DISABLE_VENDORED_FLA=1`, versions inchangées. C'est le seul
mode valide : stable, et dans le seuil sur les deux groupes.

- **Vitesse :** environ 1,1 s par ligne, soit environ 13 min de calcul par passe de 734 lignes. C'est 4,4 fois plus lent
  que les noyaux `fla`, mais 1,7 fois plus rapide que transformers seul. Le surcoût reste de quelques dizaines de
  centimes par campagne.
- **Démarrage :** pas de phase de réglage Triton (10 s contre 92 s au premier passage).

## Limites

- Une exécution par mode, sur un seul GPU ; six lignes en deux groupes.
- Il s'agit d'une mesure de précision du gradient, pas de la qualité d'un entraînement.
- La cause exacte dans les noyaux `fla` n'est pas identifiée. Une piste, non vérifiée : Unsloth signale ailleurs une
  mauvaise compilation Triton de ces noyaux sur Hopper avec Triton 3.4 à 3.7 ; notre version est Triton 3.6, sur Blackwell.
- Auto-relecture : ce n'est pas une revue indépendante.
