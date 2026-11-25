# Test « vérité fp32 » v4 : résultats (Opus 5.5, 28/09/2026)

Accord (accord explicite de l'utilisateur).

- **Pod :** `POD_ID`, RTX PRO 4000 Blackwell, 28 min au total, coût ≈ 0,26 $.
- **Arrêt :** par l'opérateur après une sauvegarde vérifiée ; statut EXITED confirmé par `get-pod`.
- **Règles d'interprétation :** figées avant les comparaisons (`REGLES_INTERPRETATION.md`, sha256 `2b3c098a…`).
- **Chiffres complets :** `RESULTS_V4.json` et `results/mode_CMP/COMPARISONS.json`.
- **Périmètre :** aucun entraînement réel, aucune promotion, aucun fichier supprimé.

**Incident.** Le premier lancement s'est arrêté à l'écriture des vecteurs bf16 : « Disk quota exceeded » sur le volume
réseau (`ABORTED_R1.json`).
- Relancé sur le même Pod, avec le même paquet signé, sur le disque local du Pod.
- La vérité fp32 des deux lancements est identique octet pour octet (`TRUTH_CROSS_LAUNCH_CHECK.json`).

## Question

Quel régime de calcul donne le gradient le plus proche du gradient exact ?
- Mêmes poids, mêmes 6 lignes et même perte que v3.
- La vérité est calculée en float32, TF32 coupé, sans Unsloth ni compilation.

## Résultats

Écart L2 relatif au vrai gradient, par groupe :

| Régime | Groupe 0 | Groupe 1 | Selon les règles (seuil 0,165 / 0,149) |
|---|---|---|---|
| Vérité fp32 recalculée | 0,000 | 0,000 | Reproductible, aussi d'un lancement à l'autre |
| bf16 standard (transformers + PEFT, sans Unsloth) | 0,110 | 0,099 | Référence de ce qu'atteint le bf16 |
| Unsloth compilé, 1er calcul (x1), puis x1b et x1c | 0,127 à 0,131 | 0,121 | Exact au niveau bf16 |
| Unsloth compilé après remise à zéro (x2, x2b) | 0,140 | 0,168 à 0,169 | Dévié |
| **Unsloth compilé, trainer** | **0,329** | 0,123 | **Dévié** |
| Unsloth sans compilation (6 variantes) | 0,059 | 0,186 | Dévié sur le groupe 1 |

**Décision des règles figées :** ni le trainer compilé ni le trainer sans compilation ne passe. Aucune configuration Unsloth
n'est validée ; il faut chercher la cause avant R3.

## Ce que ça montre

1. **Le bf16 a une erreur propre d'environ 10 % sur ce modèle,** même dans le montage standard.
   - L'erreur croît vers les premières couches : 0,21 à 0,27 sur les couches 0 à 3, contre 0,04 sur les couches 16 à 31.
   - Le seuil de 3 % du contrôle natif ne peut donc valoir qu'entre deux calculs d'un même régime.
2. **Le chemin Unsloth compilé est instable.**
   - Selon l'historique du processus, il bascule dans un régime où les gradients LoRA des couches 0 à 3 sont faux à
     81–114 %, contre 21–27 % en bf16 standard. Les couches 16 à 31 restent correctes.
   - Ici, cela touche le 1er groupe du trainer, soit la 1ʳᵉ étape après la remise à zéro. Le 2ᵉ groupe est correct
     (0,123). On retrouve la même forme dans v3 B : 0,19 puis 0,05.
   - Ce régime a une norme d'environ 6,64 ; la vérité est à 6,34.
   - La bascule n'est pas prévisible : ici le 1er calcul était sain et le trainer dévié, alors qu'en v3 le 1er calcul
     était probablement dévié.
3. **Le chemin Unsloth sans compilation est stable et déterministe** : toutes les variantes concordent à environ 1,2 %.
   - Il est plus précis que le bf16 standard sur le groupe 0 (0,059), mais moins sur le groupe 1 (0,186, surtout sur les
     LoRA d'attention : 0,246).

## Relecture de v3 (a posteriori)

Cette relecture est déduite des normes seules, pas d'une comparaison directe.

- La référence et le trainer de A (normes 6,635 et 6,639) étaient très probablement tous deux dans le régime dévié.
- La « 2ᵉ référence » d'A′ (6,338), jugée déviante, était probablement la plus proche du vrai gradient.
- A validait donc une cohérence à l'intérieur d'un régime faux.

`RAPPORT_V3.md` n'est pas modifié, puisqu'il est enregistré comme preuve.

## Portée pour la production

- r2f S1 a été entraîné avec la compilation active. On ne sait pas dans quel régime son entraînement a tourné.
- Ses résultats aux tests restent valables en tant que tels.

## Limites

- Six lignes, deux groupes, un seul GPU.
- Le groupe 1 ne compte que deux lignes.
- Il s'agit d'une mesure de précision du gradient, pas de la qualité d'un entraînement.
- Le mécanisme de la bascule compilée n'est pas identifié.
- Auto-relecture : ce n'est pas une revue indépendante.

## Suite proposée (non lancée, accord requis)

1. **Ne pas utiliser le chemin Unsloth compilé pour R3.**
2. **Au choix :**
   - **a. Test de cause**, environ 20 min et 0,25 $ : désactiver la compilation fonction par fonction pour trouver celle
     qui corrompt les couches 0 à 3, et localiser l'excès du groupe 1 sans compilation.
   - **b. Préparer R3 sur le chemin transformers + PEFT standard,** qui est la référence bf16 et un chemin déterministe.
     Il faut d'abord mesurer sa vitesse et sa mémoire.
3. **Libérer ou agrandir le volume réseau.** Il est plein (51,3 Go utilisés) et bloque toute campagne qui y écrit.
   C'est à toi de décider ; rien n'est supprimé.
