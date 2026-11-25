# TOOLCALC R2 : résultat de la relecture masquée (29/09/2026)

## Déroulement

- **Matière.**
  - 36 cas neufs dont la réponse change avec l'aiguilleur A : réponse client sur un délai (10), courriel (10),
    courtoisie (8), manquant (8).
  - 69 réponses jugées à l'aveugle. Les 3 réponses identiques à la référence sont comptées justes par le code.
- **Relecteurs.** Deux relecteurs indépendants, verrouillés avant la levée du masque :
  - Claude Sonnet, dans le dossier `astra` ;
  - Astra (GPT), dans le dossier `sonnet`.
- **Incident.**
  - Les deux relecteurs ont d'abord reçu le même prompt et ont écrit dans le même dossier. La relecture verrouillée
    de Sonnet a été écrasée par celle d'Astra.
  - Elle a été restaurée à l'identique à partir de l'historique local de la session : son empreinte est égale à celle
    du verrou. Rien n'est perdu, et aucun masque n'a été levé entre-temps.
  - Le détail est dans `work/core_4b_toolcalc_r2_review/RESTAURATION_VERROUS.json`.
- **Accord.** L'accord entre relecteurs est moyen : 70 % sur le fond (kappa 0,49). 37 réponses divergent.
- **Arbitrage.** Comme le protocole le prévoit, un arbitre indépendant, dans une nouvelle session, a tranché ces 37
  réponses à l'aveugle. Il a verrouillé son arbitrage (empreinte `15cf76f2…`) et déclare n'avoir vu aucun résultat
  auparavant.

## Résultat après arbitrage (36 cas, réponse de production contre réponse avec l'aiguilleur A)

| | Gains | Régressions | Équivalents | Erreurs persistantes |
|---|---|---|---|---|
| Fond | **15** | **8** | 3 | 10 |

- **Forme** : 6 gains, 4 pertes, 26 cas inchangés.
- **Erreurs critiques** :
  - aucune nouvelle erreur introduite par A ;
  - 11 erreurs des réponses de production corrigées (4 inventions, 7 omissions) ;
  - 6 omissions persistent.

**Par famille** (fond, « gains / régressions ») :

| Famille | Gains / régressions | Remarque |
|---|---|---|
| Réponse client sur un délai | 3 / **6** | seule famille en recul |
| Courriel | 5 / 2 | |
| Courtoisie | 4 / 0 | 4 pertes de forme et 3 gains de forme |
| Manquant | 3 / 0 | 3 gains de forme |

## Verdict préenregistré : `AIGUILLEUR_A_RETENU`

Les trois conditions sont remplies :

1. aucune nouvelle erreur critique ;
2. régressions de fond (8) ≤ gains de fond (15) ;
3. pertes de forme (4) ≤ gains de forme (6).

## Nuances à garder en tête

- **Sans arbitrage, chaque relecteur pris seul aurait conduit à préférer B**, parce qu'il comptait plus de pertes
  que de gains de forme. L'arbitrage a tranché les 7 désaccords de forme. Par exemple, « Cordialement » a été jugé
  acceptable.
- **Les 8 régressions arrivent toutes sans appel d'outil.** Ce n'est pas l'outil qui abîme la rédaction : c'est sa
  seule présence dans l'invite. L'effet joue dans les deux sens.
  - En mieux : des erreurs critiques de la production sont corrigées, comme « a été expédié » au lieu d'un départ
    futur.
  - En moins bien : 6 réponses client sur un délai sur 10 se dégradent.
- **Piste d'amélioration**, à tester sur des cas neufs avant d'y croire : ne pas proposer l'outil pour les demandes de
  rédaction. On garderait le gain de calcul sans perturber la rédaction, mais on perdrait aussi les corrections
  accidentelles.

## Suite proposée (chaque étape sur accord explicite)

1. **Confirmation sur un test scellé** (GENBENCH2) de l'intégration retenue : aiguilleur A, arrêt des relances,
   repli. Il faudra un protocole propre et ton accord.
2. **En option** : la variante d'aiguillage qui exclut la rédaction, testée d'abord sur des cas neufs.

**Production inchangée** : R2F S1 + normaliseur.

## Limites

- **Relecteurs.** Les trois relecteurs sont des modèles de langue, de deux familles, et non des experts humains.
  L'accord entre les deux premiers est moyen, et un seul arbitre a tranché.
- **Exposition.**
  - Sonnet avait vu un résumé agrégé dans l'index de mémoire.
  - Astra avait vu le décompte du verrou de Sonnet (69 lignes, 47 à adjuger). Rien n'indique qu'il ait lu ses
    jugements, et ses propres jugements en diffèrent largement, mais ce n'est pas vérifiable.
- **Portée.** 36 cas seulement, tous tirés des gabarits synthétiques du jeu F.

## Preuves

| Fichier | Contenu |
|---|---|
| `UNBLINDED.json` | levée du masque sans arbitrage |
| `UNBLINDED_ADJUDICATED.json` | résultat après arbitrage et décision |
| `DIVERGENCES.json` | divergences, sous forme masquée |
| `reviews/*/` | jugements, verrous et notes des relecteurs |
| `adjudication/` | arbitrage, verrou et notes de l'arbitre |
| `work/core_4b_toolcalc_r2_review/PROTOCOLE_RELECTURE.md` | protocole |
| `work/core_4b_toolcalc_r2_review/RESTAURATION_VERROUS.json` | incident et restauration |
| `work/core_4b_toolcalc_r2_review/ANOMALIE_VERROU_ASTRA.json` | première hypothèse, corrigée |
