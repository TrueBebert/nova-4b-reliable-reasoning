# TOOLTRAIN R1 : relecture masquée des réponses sans outil qui ont changé (29/09/2026, Opus 5.5)

## Verdict préenregistré : `RECETTE_A_REVOIR`

- **Portée** : consensus des deux relecteurs, sur 162 cas.
- **Chaque relecteur, pris seul, conclut aussi** `RECETTE_A_REVOIR`.
- **L'arbitrage est inutile.** Le candidat introduit 15 nouvelles erreurs critiques relevées d'accord par les deux
  relecteurs. La condition 1 échoue donc, quelle que soit l'issue des cas encore ouverts.
- **Sources** :
  - `UNBLINDED.json` (`/consensus/decision`, `/consensus/tous`) ;
  - protocole : `work/core_4b_tooltrain_r1_review/PROTOCOLE_RELECTURE.md` (sha256 `fa72140f…`).

## Déroulé

- **Kit** : 162 cas, soit 142 hors logique et 20 de logique tirés au sort. 311 réponses ont été jugées ; 13 autres, identiques à la
  référence, sont comptées justes par le code.
- **Ordre** : les deux relecteurs ont travaillé l'un après l'autre, chacun dans son dossier. Après chaque verrou, les
  fichiers ont été mis en lecture seule et sauvegardés.

| Relecteur | Verrou (UTC) | Lignes | À adjuger | Citations exactes | Empreinte |
|---|---|---|---|---|---|
| astra | 19:33 | 311 | 93 | 197/197 | `b6484ac1…` |
| sonnet (session neuve) | 20:16 | 311 | 88 | 127/127 | `9503bf92…` |

- **Exposition** : aucun résultat chiffré vu par les relecteurs. Sonnet déclare seulement l'index de mémoire, qui ne
  contenait pas de chiffres.
- **Accord entre relecteurs** :
  - fond : 0,90 (κ 0,72) ;
  - forme : 0,74 ;
  - présence d'une erreur critique : 0,93 ;
  - réponses divergentes : 100.

## Résultats (consensus, `/consensus/tous`)

| Fond | Gain | Régression | Équivalent | Erreur persistante | À adjuger | Total |
|---|---|---|---|---|---|---|
| Cas | 11 | 18 | 100 | 8 | 25 | 162 |

| Forme | Gain | Perte | Inchangée | À adjuger | Total |
|---|---|---|---|---|---|
| Cas | 3 | 4 | 108 | 47 | 162 |

- **Erreurs critiques** :
  - 15 nouvelles, d'accord entre les relecteurs ;
  - 10 corrigées par le candidat ;
  - 18 cas restent ouverts, dont 15 pourraient s'ajouter aux nouvelles. Le total de nouvelles erreurs se situe donc
    entre 15 et 30.
- **Les trois conditions** :
  1. aucune nouvelle erreur critique : **échoue** (15) ;
  2. régressions de fond ≤ gains : 18 contre 11 hors cas ouverts ; non tranché, car jusqu'à 36 gains restent possibles ;
  3. pertes de forme ≤ gains : 4 contre 3 ; non tranché, avec 47 cas ouverts.
- **Chaque relecteur seul** :

  | Relecteur | Régressions de fond / gains | Nouvelles erreurs critiques / corrigées |
  |---|---|---|
  | astra | 32 / 14 | 27 / 13 |
  | sonnet | 18 / 13 | 15 / 10 |

- **Échantillon de logique (20 cas)** : 19 équivalents, 1 gain, 0 régression. Les motifs reformulés ne changent rien au
  verdict.

## Où sont les nouvelles erreurs critiques

| Famille | Nouvelles | Nature |
|---|---|---|
| manquant | 6 | L'entrée absente n'est plus signalée : JSON avec `null`, ou valeurs inventées (`0.00`, `18.65`). Une somme est fausse (7.41 au lieu de 8.41). |
| ligne_exacte | 2 | Le gabarit `CODE\|QUANTITE\|RESPONSABLE` est recopié seul, sans les données. |
| courriel_demande | 2 | Motif inventé : « avant la clôture de ce dossier ». |
| derniere_version | 1 | JSON d'agent (`"action":"respond"`) sans la quantité. |
| client_delai, resume_decision, portee, sources_conflit | 1 chacune | Retard non reconnu ; fait attribué à la mauvaise personne ; ACCORD devenu REFUS ; CONFLIT au lieu de 35. |

**Erreurs corrigées par le candidat** : 10, dont 6 verdicts faux. Elles se trouvent surtout dans les familles de
logique hors `L-*`.

**Contrôles par code sur toutes les réponses C/F** (post hoc, descriptifs : `ANALYSE_RELECTURE.json`,
`ANALYSE_FUITES.json`) :

| Contrôle | R2F | Candidat |
|---|---|---|
| manquant, entrée absente signalée (16 cas) | 7 | **3** |
| manquant, valeur juste (16 cas) | 10 | 9 |
| ligne_exacte, gabarit seul (12 cas) | 6 | **8** |
| JSON d'agent hors familles d'outil (690 réponses) | 0 | **8**, tous en derniere_version |
| identifiant interne « G-… » recopié (690 réponses) | 35 | 36 : défaut déjà présent chez R2F |

**Ampleur des réécritures** : des familles de rédaction entières ont changé, par exemple client_delai,
courriel_demande et outil_autorisation (12 cas sur 12 chacune).

## Lecture et conséquences

- **Deux effets opposés** : le gain en calcul avec outil (EXP-211) reste acquis, mais la recette dégrade des tâches
  sans outil :
  - signalement des entrées manquantes ;
  - formats fermés ;
  - rédaction.
- **Hypothèse, non testée** : 360 trajectoires de calcul pour seulement 8 refus apprennent au modèle à « toujours
  calculer », et le rejeu de R2F n'ancre pas la rédaction.
- **Conséquences prévues par le protocole** :
  - pas de graine B avec cette recette ;
  - adaptateur TOOLTRAIN R1 non retenu ;
  - production inchangée et GENBENCH2 toujours scellé ;
  - pour l'outil, l'option retenue en dev reste TOOLCALC R2 (aiguilleur A + repli), sans entraînement.
- **Pistes pour une recette R2** (accord requis avant toute préparation) :
  1. **Données** : au moins 20 à 25 % de trajectoires avec une entrée manquante (MANQUANT, sans calcul), plus des cas
     « manquant » sans outil.
  2. **Ancrage** : un rejeu couvrant les familles qui ont dérivé, idéalement avec les réponses de R2F lui-même comme
     cibles. À défaut, moins de pas ou un taux d'apprentissage plus bas.
  3. **Porte automatique avant toute relecture**, par code : signalement MANQUANT, gabarit seul, JSON d'agent hors
     famille, identifiant interne recopié.

## Limites

- **Relecteurs** : ce sont des modèles de langue.
- **Cas non arbitrés** : 25 cas de fond et 47 de forme restent ouverts, car leur issue ne peut pas changer le verdict.
- **Graine unique.**
- **Contrôles par code** : ils ont été décidés après la levée du masque.
- **Couverture** : 129 cas de logique modifiés n'ont pas été relus.
