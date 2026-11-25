# TOOLCALC R2 — protocole préenregistré (29/09/2026, Opus 5.5)

Évaluation seule : aucun entraînement, aucune promotion. Suite de TOOLCALC R1 (EXP-208, `APPORT_AVEC_RESERVES`),
décidée avec l'utilisateur : (accord explicite de l'utilisateur).

## Question

L'intégration corrigée garde-t-elle le gain de calcul de R1 **sans dégrader** les autres tâches ? La dégradation se
mesure sur des cas neufs.

## Ce qui change par rapport à R1 (et rien d'autre)

Le modèle (R2F S1), l'outil, sa description, le bac à sable et la limite de 3 tours sont ceux de R1, fichiers
identiques.

1. **Aiguillage.** L'outil n'est proposé que si la demande est aiguillée vers lui. Deux aiguilleurs sont comparés :
   - **A (lexique, déterministe)** : des mots de calcul, de date et de transformation cherchés dans la consigne seule
     (`router.py`). Le lexique est écrit à partir de la définition des tâches, puis vérifié sur P, E et C. Sur F, ses
     décisions sont figées avant toute génération (`ROUTING_A.jsonl`).
   - **B (le modèle trie)** : R2F répond OUI ou NON à une question de tri figée, au format de production. Toute autre
     réponse vaut NON.
2. **Arrêt des relances identiques** : un code déjà soumis dans le même cas n'est pas réexécuté, et la boucle
   s'arrête.
3. **Guillemets échappés** : un code refusé pour erreur de syntaxe et contenant `\"` ou `\'` est réessayé une fois
   sans ces échappements, à condition de passer le même contrôle. La réparation est notée.
4. **Repli** : si la voie outil ne donne pas de réponse utilisable, le système rend la réponse de production (même
   invite sans outil). Cela couvre la limite de tours, un appel illisible, une relance arrêtée, une invite trop longue,
   une réponse vide ou une balise d'outil dans la réponse.

## Données (ouvertes seulement ; aucun benchmark protégé)

| Jeu | Contenu | Rôle |
|---|---|---|
| P, E | les 184 cas de calcul de R1 | maintien du gain (déjà vus en R1) |
| **F** | **542 cas ouverts jamais utilisés** : 330 généraux, 140 de logique, 72 du module (logique, portée, manquant) | **dégradation, principal** |
| C | les 148 cas du dev de R1 | dégradation, secondaire (déjà inspectés) |
| S | 2 cas d'essai technique | exclu |

- **F n'a jamais servi à entraîner R2F.** Aucun contexte F n'apparaît dans les 1 047 fichiers de données antérieurs
  au 27/09 (`OVERLAP_CHECK.json`, `OVERLAP_CHECK_SHORT.json`).

## Exécution

- **R2F S1 seul**, runtime de R1 : transformers 5.5.0 + PEFT 0.20.0, bf16, décodage glouton, sans « thinking »,
  768 jetons par tour.
- **Pour chaque cas** :
  1. réponse directe ;
  2. tri par le modèle (8 jetons au plus) ;
  3. décision figée de l'aiguilleur A ;
  4. si A ou B aiguille le cas : voie outil R2.
- **Contrôle des entrées** : chaque invite est identique au jeton près à sa preuve CPU (`PROMPT_PROOFS.jsonl`).
- **Réponse du système** : pour chaque aiguilleur, elle est calculée ensuite par `analyze.py`.

## Mesures et décision (code seulement ; `analyze.py` ; seuils fixés avant toute sortie R2)

La notation est celle de R1 : valeur finale (VF), gain robuste, régression.

- **CALCUL, par aiguilleur** :
  - sur P+E : gains robustes − régressions ≥ 18 et test des signes p ≤ 0,01 ;
  - sur P seul : ≥ 4.
- **DÉGRADATION, par aiguilleur, sur F** :
  - aucune balise d'outil dans une réponse ;
  - aucune réponse manquante ;
  - (exact → non exact) − (non exact → exact) ≤ 3.
- **C** : mêmes mesures, rapportées comme preuve secondaire.
- **Décision** :
  - `INTEGRATION_VALIDEE_DEV` : au moins un aiguilleur remplit CALCUL et DÉGRADATION. L'aiguilleur retenu est celui
    qui a le plus fort gain net robuste sur P+E ; en cas d'égalité, A.
  - `APPORT_AVEC_RESERVES` : CALCUL seul est rempli.
  - `NON_VALIDEE` : sinon.
  - Un run incomplet est signalé comme tel.

## Limites déclarées

- **P et E ne sont pas neufs pour le calcul.** L'aiguillage et la réparation des guillemets viennent de l'examen de
  R1 et peuvent les influencer.
- **F est neuf par ses cas, mais il reprend les gabarits de C**, que j'ai inspectés.
- **Seules les égalités exactes sont notées par code.** Les réponses libres modifiées sont listées pour une relecture
  masquée ultérieure.
- **Un seul passage, en décodage glouton.**
- **Une conclusion positive reste de développement.** La confirmation se ferait sur un test scellé (par exemple
  GENBENCH2 « calculs_dates »), avec l'accord explicite de l'utilisateur et un protocole propre.
