"""Automatic first-decision classifier for the « contredit » probe (diagnostic only).

Maps the opening decision of an answer to the review vocabulary:
TRUE (recevable), FALSE (irrecevable), UNKNOWN (cannot decide), CONTRADICTION (the model's
« Contradiction » label), OTHER (anything else, always sent to manual reading).
Validated before the probe against the locked R3 blind review (see validate_classifier.py).
v2: adds « indécision » / « indécisible » (the only 3 v1 mismatches, CLASSIFIER_VALIDATION_v1.json).
"""
import re
import unicodedata

PREFIX = re.compile(r"^(?:\*\*)?\s*(?:d[ée]cision|verdict|r[ée]ponse)\s*:?\s*(?:\*\*)?\s*:?\s*", re.I)
DOSSIER = re.compile(r"^(?:le\s+)?dossier\s+(?:est\s+)?", re.I)
UNKNOWN = ('indecidable', 'indecisible', 'indecision', 'indetermine', 'information insuffisante', 'informations insuffisantes',
           'renseignements insuffisants', 'impossible de trancher', 'on ne peut pas trancher',
           'les renseignements ne permettent pas', 'non determinable', 'ne peut pas etre tranche')


def fold(text):
    text = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in text if not unicodedata.combining(c)).lower()


def classify(prediction):
    head = prediction.strip().lstrip('#*- ').strip()
    head = PREFIX.sub('', head, count=1)
    head = DOSSIER.sub('', head, count=1)
    first = fold(head[:80])
    if re.match(r"(?:non\s+recevable|n'est pas recevable|n’est pas recevable|irrecevable)\b", first):
        return 'FALSE'
    if re.match(r"recevable\b", first):
        return 'TRUE'
    if any(first.startswith(u) for u in UNKNOWN):
        return 'UNKNOWN'
    if first.startswith('contradiction') or first.startswith('contradictoire'):
        return 'CONTRADICTION'
    return 'OTHER'
