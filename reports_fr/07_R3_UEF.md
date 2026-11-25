# Campagne R3 en runtime UEF : résultats descriptifs (Opus 5.5, 28–29/09/2026)

Accord de l'utilisateur : (accord explicite de l'utilisateur).

- **Pod :** `POD_ID`, RTX PRO 4500 (la PRO 4000 était indisponible).
- **Durée et coût :** 3 h 12, ≈ 2,31 $.
- **Arrêt :** par l'opérateur après une sauvegarde vérifiée (archive `2fe2ff86…`) ; statut EXITED confirmé.
- **État final :** `COMPLETE_AWAITING_OPEN_DEV_REVIEW`.
- **Périmètre :** aucune promotion. Production inchangée (R2F S1 + normaliseur).

## Déroulement

**Porte native : PASS.**
- Gradients, trainer contre référence : L2 0,0119 et 0,0103 (traitement), 0,0118 et 0,0105 (témoin). Seuil : 0,03.
- Smoke réussi. Validation après rechargement : 0,281. Générations : 4/4 terminées par EOS.
- Runtime UEF prouvé à chaque chargement.

**4 entraînements complets** (184 mises à jour, 734 positions dans l'ordre, groupes conformes au plan) :

| Bras | Graine 20260928 | Graine 20260929 |
|---|---|---|
| Témoin V5 | perte 0,076 | 0,077 |
| Mix R3 (module de transfert) | 0,124 | 0,122 |

**15 chargements frais, 1 130 sorties.**
- Toutes se terminent par EOS avant 384 jetons.
- Les passages 2 et 3 sont identiques au passage 1 pour les 18 cas répétés, sur chaque modèle : la génération est
  déterministe d'un rechargement à l'autre.

## Mesures (dev ouvert, 190 cas ; `R3_DESCRIPTIVE_SPLIT.json`, `R3_DESCRIPTIVE_FAMILIES.json`)

Deux mesures sont données :
- **exact** : égalité stricte au texte de référence (espaces normalisés). C'est un score de code : il ne juge pas le fond,
  et une paraphrase correcte compte comme non exacte ;
- **perte** : perte moyenne par jeton, en validation.

| Modèle | Exact V5 (142) | dont G (80) | L (40) | N (22) | Exact module (48) | Perte V5 | Perte module |
|---|---|---|---|---|---|---|---|
| R2F initial | 43 | 34 | 0 | 9 | 12 | 0,573 | 0,834 |
| Témoin, graine 28 | 124 | 76 | 40 | 8 | 12 | 0,119 | 0,793 |
| Témoin, graine 29 | 125 | 77 | 40 | 8 | 12 | 0,122 | 0,787 |
| Mix R3, graine 28 | 124 | 75 | 40 | 9 | 16 | 0,120 | 0,499 |
| Mix R3, graine 29 | 125 | 75 | 40 | 10 | 18 | 0,111 | 0,461 |

**Module, par catégorie** (exact sur 8) :

| Catégorie | R2F, témoins | Mix R3 |
|---|---|---|
| Informations manquantes | 1 | 5 et 6 |
| Logique | 3 | 3 et 4 |
| Portée | 8 | 8 |
| Calendrier, centimes, transformation | 0 | 0 |

**Mix R3 contre son témoin, cas par cas :**
- graine 28 : 6 gains, 2 pertes ;
- graine 29 : 8 gains, 2 pertes ;
- les 4 pertes sont toutes dans la famille G (générale).

## Lecture prudente

- **Les deux graines vont dans le même sens.**
  - Remplacer 144 répétitions V5 par le module ne dégrade pas le score exact global en V5 (124–125 dans les deux bras)
    et ne change pas la perte V5.
  - Cela améliore nettement la perte sur le module (environ −0,31), avec quelques gains exacts, surtout en
    « informations manquantes ».
  - Pour le calendrier, les centimes et la transformation, la comparaison exacte ne distingue aucun modèle : 0/8 partout.
- **Ce sont des mesures d'apprentissage et d'interpolation** sur un dev ouvert, synthétique, écrit par le même auteur.
  Elles ne démontrent ni la généralisation externe ni le maintien du métier en production. Aucune porte de ce type n'est
  définie.
- **Les pertes G et les zéros du module doivent être relus sur le fond.** Une paraphrase peut être juste ; une erreur
  critique (calcul, date, invention, portée, verdict) bloquerait tout signal positif.

## Suite prévue par le protocole (non faite)

1. **Relecture sémantique masquée**, dans un contexte neuf, sans identité des modèles jusqu'au verrouillage :
   - toutes les différences de fond et les variantes distinctes ;
   - citations exactes des extraits décisifs ;
   - jugements séparés sur la forme et sur le fond (gain, régression, équivalent, erreur persistante, indécidable) ;
   - adjudication des cas sensibles.
2. **Rapporter par graine et par cas** : les 22 formes nouvelles, les 20 cas d'entretien, les 40 verdicts.
3. **Aucune promotion** tant que les portées externe et métier ne sont pas définies.

## Limites

- Une campagne, deux graines, un GPU.
- Le score exact sous-estime les réponses justes.
- Auto-analyse descriptive : ce n'est pas la relecture indépendante exigée.
- Le résumé `R3_SUMMARY.json` contient aussi des entrées vides pour les fichiers `.log` (défaut d'affichage sans effet
  sur les totaux).
