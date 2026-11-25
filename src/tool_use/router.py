"""TOOLCALC R2 routers (Opus 5.5, 29/09/2026): decide, per request, whether the calculation tool is offered at all.
Import-safe, no model.

Router A (deterministic): a French lexicon of calculation, date/time and mechanical-transformation words, matched on
the INSTRUCTION only (never the context), written from the task definition rather than from observed failures.
Router B (model): the production model answers OUI/NON to a fixed triage question, in the production prompt format
(system Core, INSTRUCTION/CONTEXTE); anything other than a leading OUI/NON counts as NON (no tool)."""
from __future__ import annotations

import re

CALC = (r'calcul\w*|additionn\w*|soustra\w*|multipli\w*|montants?|totale?s?|totaux|sommes?|remises?|rabais|taxes?|'
        r'taxables?|taux|pourcentages?|arrondi\w*|centimes?|moyennes?|variations?|soldes?|ttc|ht|co[uû]ts?')
DATES = (r'dates?|dur[ée]es?|jours?|minutes?|heures?|d[ée]lais?|[ée]ch[ée]ances?|calendriers?|lendemain|veille|'
         r'semaines?|d[ée]calages?')
TRANSFORMATION = r'masqu\w*|casse|doublons?|d[ée]doublonn\w*|s[ée]parateurs?'
LEXICON = re.compile(r'(?<![\w-])(' + '|'.join((CALC, DATES, TRANSFORMATION)) + r')(?![\w-])', re.IGNORECASE)

TRIAGE_INSTRUCTION = (
    "Tu tries les demandes avant d'y répondre. Réponds OUI si répondre correctement à la demande ci-dessous exige au moins "
    "une opération exacte : calcul arithmétique (montant, total, remise, taxe, pourcentage, arrondi, variation), calcul "
    "de date, de durée ou décompte de jours, ou transformation mécanique en plusieurs étapes d'une liste ou d'un texte "
    "(casse, masquage de chiffres, dédoublonnage, jointure). Réponds NON si la demande consiste surtout à décider, "
    "appliquer une règle ou une condition, donner un verdict, choisir une action, extraire, reformuler ou rédiger. "
    "Réponds uniquement OUI ou NON.")
TRIAGE_MAX_NEW_TOKENS = 8


def route_a(instruction):
    """-> (decision, matched words)."""
    words = [m.group(1).lower() for m in LEXICON.finditer(instruction)]
    return bool(words), sorted(set(words))


def triage_row(row):
    """Router B input, in the production INSTRUCTION/CONTEXTE format."""
    return {'instruction': TRIAGE_INSTRUCTION,
            'contexte': 'DEMANDE :\n' + row['instruction'].strip() + '\n\nDONNÉES :\n' + row['contexte'].strip()}


def parse_triage(text):
    """-> 'OUI', 'NON' or 'INVALIDE' (INVALIDE is treated as NON)."""
    head = re.sub(r'^[\s"«*`\'(]+', '', text or '').upper()
    if head.startswith('OUI'):
        return 'OUI'
    if head.startswith('NON'):
        return 'NON'
    return 'INVALIDE'
