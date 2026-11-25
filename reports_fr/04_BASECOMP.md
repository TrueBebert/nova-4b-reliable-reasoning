# BASECOMP R1 — Qwen de base contre production (27/09/2026)

**Question.** Les faiblesses générales vues dans GENBENCH R1 viennent-elles de Qwen3.5-4B lui-même (**héritées**) ou de
nos adaptations LoRA (**introduites**) ?

**Réponse.** Elles sont **héritées**. La règle préenregistrée ne trouve aucune faiblesse introduite, et l'adaptation
améliore nettement la logique.

C'est un diagnostic : il ne change pas la production (r2f S1 + normaliseur R1).

## En bref

| Mesure (même GPU, mêmes 377 entrées, mêmes réglages) | Production | Qwen de base |
|---|---|---|
| Logique, jugement conjoint à l'aveugle (/128) | **116** | 49 |
| Général, FAIL confirmés par deux passes (/249) | **104** | 117 |
| Catégories où la production a ≥ 3 FAIL de plus (seuil « introduite ») | **aucune** | — |
| Copies en reformulation (/40) | 0 | 0 |
| Réponses violant une contrainte de forme explicite (contrôle par code) | 20 | 13 |

- **Faiblesses héritées.** Sur les 85 cas de GENBENCH ratés par nos six systèmes, Qwen de base en rate aussi **66**
  (17 réussis, 2 indécis ; analyse a posteriori).
- **Deux signaux à surveiller, sous les seuils :**
  - la forme stricte (nombre exact de phrases, de puces ou de lignes, JSON) est un peu moins bien tenue par la
    production ;
  - le défaut « condition fausse à côté d'une condition incertaine », déjà connu depuis R2F, est propre à notre
    adaptation.
- **Mesure robuste.** Malgré un autre GPU et d'autres juges, la production refait 104 FAIL (105 dans GENBENCH) et 116
  en logique (117).

## Déroulement

- **Exécution.**
  - RTX 5070 locale de l'utilisateur, le 27/09 de 11:03 à 12:23 UTC (80 min), sans coût.
  - RunPod n'avait plus de RTX PRO 4500 : aucun Pod n'a été créé.
  - Changements d'exécution consignés **avant** les générations du modèle de base : ordonnancement séquentiel,
    plafond de 7 h, comparaison inter-GPU devenue descriptive (`work/core_4b_basecomp_r1/ADDENDUM_EXECUTION_LOCALE.md`).
- **Générations.**
  - 754 réponses, sans aucune erreur.
  - Preuve d'entrées : 754 prompts identiques aux entrées scellées.
  - Revérification indépendante avec décodeur : OK.
  - Production : 36 min, 90 jetons par réponse en moyenne, 0 troncature.
  - Qwen de base : 36 min, 122 jetons en moyenne, 2 réponses coupées à 768 jetons.
- **Jugements à l'aveugle, consignes de GENBENCH reprises mot pour mot** (`work/core_4b_basecomp_r1/JUDGE_PROMPTS.md`).
  - Logique : jugement conjoint des 256 réponses distinctes, puis seconde lecture des 146 réponses où les deux systèmes
    divergent. La seconde lecture n'a changé aucun verdict.
  - Général : 2 passes × 12 lots, soit 492 candidats par passe, avec des étiquettes permutées entre les passes.
- **Incident.**
  - Trois juges ont été interrompus par la limite d'usage de la session, avant d'avoir écrit leur résultat.
  - Leurs brouillons ont été archivés sans être lus (`review_G/_stopped_tmp_ratelimit_2026-09-27/`).
  - Les trois lots ont été rejugés par des juges neufs.

## Logique (128 dossiers)

| Sous-ensemble | n | Production (conjoint / verdict juste) | Base (conjoint / verdict juste) |
|---|---|---|---|
| Tous | 128 | **116** / 121 | 49 / 66 |
| Un fait décisif est en conflit (attestations contradictoires) | 44 | **39** / 41 | 5 / 9 |
| Un fait requis est faux (« irrecevable » attendu) | 44 | 37 / 38 | 26 / **43** |
| Ni l'un ni l'autre (recevable, ou fait décisif inconnu) | 48 | **45** / 47 | 22 / 22 |
| Formes habituelles | 64 | 62 / 63 | 28 / 33 |
| Formes nouvelles | 64 | 54 / 58 | 21 / 33 |
| Réponses incohérentes (statuts énoncés ≠ verdict) | — | 7 | 62 |

Les 8 dossiers CF/FC (fait faux + fait en conflit) figurent dans les deux premières lignes, d'où un total de 136.

- **Erreur type de la base : l'inconnu ou le conflit traité comme faux.** La réponse constate elle-même que le
  procès-verbal est muet ou que les attestations se contredisent, puis conclut « irrecevable ». C'est exactement le
  défaut que nos entraînements ont corrigé.
- **Seul point où la base fait mieux : les dossiers où un fait requis est faux** (43/44 contre 38/44 pour les
  verdicts). Elle y a raison par défaut, puisqu'elle conclut « irrecevable » dès qu'un fait n'est pas confirmé.
  - Sur les 6 verdicts manqués par la production, 5 sont des combinaisons « fait faux + fait en conflit ou inconnu » :
    3 cas CF/FC (5/8 justes) et 2 cas FU/UF (6/8). La base réussit ces deux groupes à 8/8.
  - C'est le défaut résiduel connu depuis R2F/R2G (la production conclut « indéterminé »). BASECOMP montre qu'il vient
    de l'adaptation.

## Général (249 cas)

| Catégorie | n | FAIL production | FAIL base | Écart | Lecture préenregistrée |
|---|---|---|---|---|---|
| Extraction d'information | 20 | 7 | 5 | +2 | sous le seuil (+3) |
| Sortie structurée JSON | 20 | 9 | 7 | +2 | sous le seuil |
| Classification | 20 | 7 | 6 | +1 | sous le seuil |
| Reformulation | 40 | 24 | 23 | +1 | sous le seuil |
| Anti-hallucination | 20 | 3 | 3 | 0 | héritée |
| Résumé | 25 | 12 | 13 | −1 | héritée |
| Choix d'outil | 20 | 9 | 10 | −1 | héritée |
| Information manquante | 20 | 8 | 11 | −3 | héritée |
| Réponse client | 20 | 11 | 14 | −3 | héritée |
| Suivi de procédure | 24 | 6 | 9 | −3 | héritée |
| Rédaction professionnelle | 20 | 8 | 16 | **−8** | héritée |
| **Total** | 249 | **104** | **117** | **−13** | aucune faiblesse introduite ; pas d'alerte (+8) |

- **Recouvrement des échecs.**
  - 78 cas ratés par les deux systèmes.
  - 24 ratés par la production seule, 33 par la base seule.
  - 14 et 13 réponses restent indécises (les passes divergent) ; elles ne comptent pas comme FAIL.
- **Motifs des FAIL** (familles de mots-clés dans les raisons des juges ; indicatif) :

  | Famille | Production | Base |
  |---|---|---|
  | Calculs et dates | 58 | 72 |
  | Forme et longueur | 48 | 49 |
  | Règles et portée | 34 | 34 |
  | Inventions | 16 | **33** |
  | Faux contre inconnu | 18 | 11 |
  | Transformations | 13 | 9 |

- **Contrôles de forme par code** (détection seulement, aucune réparation ; `FORM_AUDIT.json`) :
  - production : 20 réponses en violation, dont 12 au sens strict — surtout le nombre exact de phrases (8) et la
    limite de mots (6), plus des puces, des lignes et un JSON ;
  - base : 13 réponses en violation (9 au sens strict) — limite de mots (7) et nombre exact de phrases (6).

## Analyse a posteriori (descriptive, non préenregistrée ; `POSTHOC_DESCRIPTIVE.json`)

- **Les 85 échecs communs de GENBENCH.**
  - Qwen de base en rate 66, en réussit 17, et 2 restent indécis.
  - La production relancée ici en rate 82, et 3 restent indécis : aucun n'est devenu PASS.
  - La grande majorité des échecs communs vient donc du modèle de base. Les 17 cas réussis par la base, et ratés par
    tous nos systèmes, sont des capacités que l'adaptation a pu dégrader.
- **Échecs propres à la production (24).**
  - Catégories : reformulation 5, JSON 4, extraction 3, résumé 3, et quelques autres.
  - Motifs : surtout calculs (11), forme (10) et règles (9) ; une seule invention.
- **Échecs propres à la base (33).**
  - Catégories : surtout rédaction (8) et information manquante (5).
  - Motifs : calculs (18), forme (12) et inventions (9).
- **L'adaptation réduit nettement les inventions dans les tâches générales.**
- **Pas de sur-emploi de « impossible à déterminer » par la production hors de la catégorie information manquante** :
  8 réponses (4 PASS, 2 FAIL, 2 indécises), contre 5 pour la base (toutes PASS).

## Reproductibilité (production, Pod RTX PRO 4500 contre RTX 5070 locale)

- **Entrées identiques** : 377/377.
- **Jetons générés identiques** : 291/377.
  - Logique : 119/128, et aucun des 9 écarts ne change la décision.
  - Général : 172/249.
  - Les écarts viennent de petites différences numériques entre GPU, amplifiées par le décodage glouton.
- **Scores** : 104 FAIL contre 105, et 116 contre 117 en logique. Les juges et la mesure sont stables.

## Ce que cela implique (orientation pour la décision de l'utilisateur)

1. **Le futur corpus doit enseigner, pas réparer.** Les faiblesses générales (calculs et dates, portée des règles,
   contraintes de forme) sont celles du 4B de base.
2. **Calculs et dates dominent chez les deux systèmes.** Déléguer les calculs exacts (dates, sommes, délais) à un outil
   au moment de la réponse est une piste sérieuse, à évaluer séparément.
3. **Préserver ce que la base sait faire.**
   - Les 17 cas réussis par la base et ratés par nos systèmes, et la forme stricte un peu moins tenue, plaident pour
     mélanger des données générales de suivi de consignes dans tout futur entraînement.
   - Il faut aussi suivre les contrôles de forme par code à chaque campagne.
4. **Le défaut CF** (fait faux à côté d'un fait en conflit, conclu « indéterminé ») est propre à notre adaptation. Il
   reste à traiter si la logique redevient prioritaire.
5. **Selon les règles d'Astra**, la prochaine étape est de construire d'abord un nouveau test vierge, isolé du
   constructeur de corpus, puis seulement un corpus équilibré. Aucun entraînement sans accord explicite.

## Limites

- **Taille des catégories.** Les seuils portent sur de petites catégories (20 à 40 cas) : un écart de +2 n'est pas
  interprétable seul.
- **Juges.** Ce sont des agents de langage (Claude), à l'aveugle, en deux passes. Leur fiabilité est estimée par la
  reproduction 104 contre 105, pas par un jugement humain.
- **Indicateurs approximatifs.** Les familles de motifs viennent de mots-clés, et l'analyse a posteriori est
  descriptive.
- **Test ouvert.** GENBENCH était déjà ouvert : BASECOMP compare deux systèmes sur un test connu, sans mesurer de
  nouvelle capacité.

## Traçabilité

| Élément | Chemin |
|---|---|
| Protocole préenregistré (inchangé) | `work/core_4b_basecomp_r1/PROTOCOLE.md` |
| Addendum d'exécution locale | `work/core_4b_basecomp_r1/ADDENDUM_EXECUTION_LOCALE.md` |
| Consignes des juges | `work/core_4b_basecomp_r1/JUDGE_PROMPTS.md` |
| Lecture préenregistrée | `BASECOMP_FINAL.json` |
| Logique | `L_FINAL.json`, `L_PASS1_SUMMARY.json` |
| Général | `G_SUMMARY.json`, `review_G/G_LOCKED.json` |
| Contrôles objectifs | `RUN_ANALYSIS.json`, `COPY_METRIC.json`, `FORM_AUDIT.json`, `LOCAL_RECHECK.json` |
| A posteriori | `POSTHOC_DESCRIPTIVE.json` |
| Sauvegarde | `results/BACKUP_VERIFIED.json` (archive 715d8f7f…) |
