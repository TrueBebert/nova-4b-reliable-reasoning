# TOOLCALC R2 : résultats (29/09/2026)

**Exécution.** Sur la RTX 5070 locale, de 12:57 à 14:22 (84 min), à la demande de l'utilisateur :
(accord explicite de l'utilisateur). Coût : 0 $.

- 876 cas sur 876, sans erreur technique.
- Toutes les invites sont conformes à leurs preuves, au jeton près.
- **Déterminisme** : les 334 réponses directes et les 186 réponses outil communes avec R1 sont identiques à R1.
  Les écarts de R2 viennent donc uniquement des corrections.

## Verdict préenregistré : `INTEGRATION_VALIDEE_DEV`, aiguilleur retenu : A

Les deux aiguilleurs remplissent les deux conditions. A est retenu, conformément à la règle fixée d'avance, parce que
son gain net robuste est plus fort : 61 contre 51.

## Calcul, dates, transformations (P+E, 184 cas)

| | Sans outil | Système A | Système B |
|---|---|---|---|
| Bonnes valeurs finales | 59 | **120** | 110 |
| Gains robustes / régressions | — | 63 / 2 | 53 / 2 |
| Réponses exactes | 41 | 103 | 92 |
| Cas aiguillés vers l'outil | — | 184 | 149 |

- **A garde tout le gain de R1.**
  - La voie outil a échoué sur 8 cas, tous en calendrier ou en transformation : 6 relances identiques arrêtées et
    2 appels illisibles.
  - Ces 8 cas reçoivent la réponse de production (repli).
  - La réparation des guillemets n'a jamais servi : ce défaut touchait des cas de logique, qui ne sont plus aiguillés.
- **B laisse passer 35 cas de calcul.** Les principaux : total incomplet (12), transformation (12), variation (6).

## Dégradation sur les 542 cas neufs (F, critère principal)

| | Système A | Système B |
|---|---|---|
| Cas aiguillés vers l'outil | 56 | 18 |
| Balises d'outil / réponses manquantes | 0 / 0 | 0 / 0 |
| Réponses exactes perdues / gagnées | 0 / 3 | 0 / 2 |
| Verdicts de logique justes (sur 140) | 140 | 140 |
| Réponses modifiées | 36 | 3 |

- **Les dégradations de R1 ont disparu** : plus de réponse manquante, plus de balise, verdicts de logique intacts.
- **Sur C (148 cas, preuve secondaire)** : aucune perte d'égalité exacte, et 40/40 verdicts pour A comme pour B.

## La réserve à connaître avant de choisir

- **Avec A, 31 des 36 réponses modifiées l'ont été sans aucun appel d'outil.** La seule déclaration de l'outil dans
  l'invite change le texte.
- **Ce sont des tâches de rédaction**, aiguillées à cause des mots « délai », « date » et « échéance » : réponse
  client sur un délai (10), courriel (10), courtoisie (8).
- **Ma lecture de quelques exemples : l'effet est mitigé.**
  - Mieux : « le départ est confirmé dans 3 jours » au lieu de « a été expédié » ; le bon numéro de dossier.
  - Moins bien : une phrase fautive ajoutée ; une ligne « Objet : URGENCE » non demandée.
- **L'égalité exacte ne peut pas juger ces textes libres.** Le critère est rempli, mais il ne prouve pas l'absence de
  régression sur ces 28 textes.
- **B évite ce problème** : seulement 3 changements, tous après un vrai calcul. En contrepartie, il perd 10 gains
  de calcul.

## Ce que cela veut dire

1. **Les corrections d'intégration fonctionnent.** Le gain de calcul est intact, et les dégradations mesurables de R1
   ont disparu sur des cas neufs.
2. **Le choix restant est entre deux profils** :
   - A : plus de calculs justes, mais des textes de rédaction modifiés, non jugés ;
   - B : plus propre, avec moins de gains.
3. **Des tâches à plusieurs étapes restent faibles, même avec l'outil** : centimes 14/32, calendrier 9/32,
   transformation 10/32. Leur levier est l'entraînement.

## Suite proposée (chaque étape sur ton accord)

1. **Relecture masquée des 39 réponses modifiées** (36 de A et 3 de B), par deux relecteurs indépendants comme pour
   R3. Le volume est petit. Elle tranchera si les changements de rédaction de A sont acceptables.
2. **Confirmation sur un test scellé** (par exemple GENBENCH2), avec l'aiguilleur choisi, un protocole propre et ton
   accord.
3. **Plus tard** : un entraînement avec l'outil dans la boucle pour les règles à plusieurs étapes.

**Production inchangée** : R2F S1 + normaliseur.

## Limites

- **Évaluation de développement.**
  - P et E ne sont pas neufs pour le calcul.
  - F est neuf par ses cas, mais il reprend les gabarits de C.
  - Il n'y a eu qu'un seul passage, en décodage glouton.
- **Seules les égalités exactes sont notées par code.** Les réponses libres modifiées sont listées dans
  `INSPECTION.json`.
- **Aiguilleur B** : 22 fois, le modèle a répondu à la question de fond au lieu de OUI ou NON (« INDETERMINE »,
  « CONFLIT », « U », « V »). Ces réponses ont compté comme NON, sans danger.
- **Inspection faite après coup.** L'inspection est descriptive ; la combinaison A et B qui y figure est exploratoire.

## Preuves

- **Décision** : `RESULTS.json`.
- **Détails et liste des réponses modifiées** : `INSPECTION.json`.
- **Réponses brutes** : `results/r2f/responses.jsonl`.
- **Collecte vérifiée** : `COLLECTED.json`.
- **Autorisation et lancement** : `AUTHORIZATION_LOCAL.json` et `LAUNCHED_LOCAL.json`.
- **Protocole** : `package/PROTOCOLE.md`.
