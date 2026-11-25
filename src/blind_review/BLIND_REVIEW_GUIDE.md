# Seconde passe masquée R2F — consignes de relecture (reprises de R2C, exemple de conflit complété)

Tu relis des réponses d'un modèle à des dossiers fictifs de recevabilité. Tu ne sais pas quel modèle a produit chaque réponse et tu ne dois pas chercher à le deviner. Chaque élément donne l'instruction, le contexte, la réponse et l'attendu (verdict et règle, avec l'état V/F/U/C du premier et du second fait).

## Lecture des faits

- « atteste : « P » », « confirme que P », « valide l'affirmation « P » » → P est **vrai**.
- « contredit : « P » », « dément : « P » », « réfute l'affirmation « P » », « infirme : « P » » ou « l'affirmation « P » est fausse » (une seule source) → P est **faux**.
- « reste muet sur », « ne se prononce pas », « ne permet pas de savoir » → P est **inconnu**.
- Deux sources opposées sur P (« un procès-verbal atteste : « P » ; un autre procès-verbal contredit : « P » », « Un procès-verbal atteste : « P » ; un autre procès-verbal le contredit » ou « … le dément », ou « Deux relevés s'opposent… ») → P est **inconnu**. C'est l'état C.
- Le verdict ne dépend que des critères décisifs de la règle :
  - critère unique : vrai → recevable, faux → irrecevable, inconnu → indéterminé ;
  - conjonction : un requis faux → irrecevable ; tous vrais → recevable ; sinon → indéterminé.

## Champs à remplir, pour chaque élément

| Champ | Contenu |
|---|---|
| `id` | Identifiant de l'élément. |
| `verdict_initial` | La décision annoncée **en premier** : `TRUE` (recevable), `FALSE` (irrecevable, non recevable), `UNKNOWN` (indéterminé, les renseignements ne permettent pas de trancher, information insuffisante, indécidable…), `OTHER` (« Contradiction » ou autre). |
| `verdict_ok` | `verdict_initial` correspond au verdict attendu. |
| `statuts_ok` | Les statuts des faits **décisifs** que la réponse énonce ou utilise sont justes. Faux si la réponse invente une source ou une affirmation absente du contexte. |
| `coherence_ok` | Le verdict découle des statuts que la réponse énonce elle-même. Exemple incohérent : « inconnu… » puis « irrecevable ». |
| `justification_ok` | La justification nomme les exigences décisives et leur statut, de façon suffisante et sans erreur. |
| `grave` | `none` si tout est juste ; `major` si le verdict est faux ou si un fait est inventé ; `minor` sinon. |
| `note` | 25 mots au maximum, factuels. |

## Format de sortie

Un seul fichier JSON : une liste d'objets avec exactement ces clés, un objet par élément, dans n'importe quel ordre. N'écris aucun autre fichier.
