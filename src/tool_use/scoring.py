"""Code-only scoring for the tool evaluation (Opus 5.5, 29/09/2026). No LLM judge. Import-safe.

For each case the answer type is derived from the reference text alone (kind()). Three measures per answer:
  exact          stripped answer == stripped reference (form and substance);
  valeur_finale  the LAST value of the reference's type stated in the answer equals the reference value
                 (substance, primary; refusal references compete with amounts: the last one decides);
  valeur_presente the reference value appears somewhere in the answer (descriptive only).
Pre-registered limits: only ISO dates are recognised; integers inside dates, clock times and decimals are ignored;
text answers are compared after stripping outer quotes, on the whole answer or its last non-empty line."""
from __future__ import annotations

import json
import re
from decimal import Decimal

AMOUNT = re.compile(r'(?<![\d.,])(-?\d+)[.,](\d{2})(?!\d)')
REFUSAL = re.compile(r'\b(IMPOSSIBLE|INCONNU)\b')
DATE = re.compile(r'(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)')
TIME = re.compile(r'(?<!\d)\d{1,2}:\d{2}(?!\d)')
DECIMAL = re.compile(r'(?<!\d)\d+[.,]\d+')
INTEGER = re.compile(r'(?<![\w])([+\-−]?\d+)(?![\w])')
PERCENT = re.compile(r'(\d+(?:[.,]\d+)?)\s*%')
QUOTES = '"\'`«»“”‘’ '


def kind(reference):
    ref = reference.strip()
    if re.fullmatch(r'-?\d+\.\d{2} EUR', ref):
        return 'montant'
    if ref in ('IMPOSSIBLE', 'INCONNU'):
        return 'refus'
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', ref):
        return 'date'
    if re.fullmatch(r'[+-]\d+', ref):
        return 'entier_signe'
    if re.fullmatch(r'\d+', ref):
        return 'entier'
    if re.fullmatch(r'\d+(\.\d+)?%', ref):
        return 'pourcentage'
    if ref[:1] in '{[':
        return 'json'
    return 'texte'


def _amounts(text):
    return [(m.start(), Decimal(m.group(1) + '.' + m.group(2))) for m in AMOUNT.finditer(text)]


def _integers(text):
    text = DATE.sub(' ', text)
    text = TIME.sub(' ', text)
    text = DECIMAL.sub(' ', text)
    return [int(m.group(1).replace('−', '-')) for m in INTEGER.finditer(text)]


def _json_value(text):
    body = text.strip()
    body = re.sub(r'^```(?:json)?\s*|\s*```$', '', body)
    try:
        return True, json.loads(body)
    except json.JSONDecodeError:
        pass
    for i, ch in enumerate(body):
        if ch in '{[':
            try:
                return True, json.JSONDecoder().raw_decode(body[i:])[0]
            except json.JSONDecodeError:
                continue
    return False, None


def _strip_quotes(text):
    text = text.strip()
    while len(text) >= 2 and text[0] in QUOTES and text[-1] in QUOTES:
        text = text[1:-1].strip()
    return text


def reference_value(reference):
    k, ref = kind(reference), reference.strip()
    if k == 'montant':
        return Decimal(ref[:-4])
    if k in ('entier', 'entier_signe'):
        return int(ref)
    if k == 'pourcentage':
        return Decimal(ref[:-1])
    if k == 'json':
        return json.loads(ref)
    return ref


def final_value(answer, reference):
    """The last value of the reference's type in the answer, or None."""
    k = kind(reference)
    if answer is None:
        return None
    if k in ('montant', 'refus'):
        found = [(p, v) for p, v in _amounts(answer)] + [(m.start(), m.group(1)) for m in REFUSAL.finditer(answer)]
        return max(found, key=lambda x: x[0])[1] if found else None
    if k == 'date':
        found = DATE.findall(answer)
        return '-'.join(found[-1]) if found else None
    if k in ('entier', 'entier_signe'):
        found = _integers(answer)
        return found[-1] if found else None
    if k == 'pourcentage':
        found = PERCENT.findall(answer)
        return Decimal(found[-1].replace(',', '.')) if found else None
    if k == 'json':
        ok, value = _json_value(answer)
        return value if ok else None
    lines = [x for x in answer.strip().splitlines() if x.strip()]
    whole = _strip_quotes(answer)
    return whole if whole == reference.strip() or not lines else _strip_quotes(lines[-1])


def present(answer, reference):
    k = kind(reference)
    if answer is None:
        return False
    target = reference_value(reference)
    if k == 'montant':
        return any(v == target for _, v in _amounts(answer))
    if k == 'refus':
        return bool(re.search(r'\b' + reference.strip() + r'\b', answer))
    if k == 'date':
        return reference.strip() in ['-'.join(x) for x in DATE.findall(answer)]
    if k in ('entier', 'entier_signe'):
        return target in _integers(answer)
    if k == 'pourcentage':
        return any(Decimal(x.replace(',', '.')) == target for x in PERCENT.findall(answer))
    if k == 'json':
        ok, value = _json_value(answer)
        return ok and value == target
    return reference.strip() in answer


def score(answer, reference):
    value = final_value(answer, reference)
    return {'kind': kind(reference),
            'exact': answer is not None and answer.strip() == reference.strip(),
            'valeur_finale': value is not None and value == reference_value(reference),
            'valeur_presente': present(answer, reference),
            'valeur_extraite': None if value is None else str(value) if not isinstance(value, (dict, list)) else value}


def tool_diagnosis(trace, reference, final_ok):
    """Where the `outil` arm lost a case (pre-registered categories)."""
    calls = [c for t in trace['turns'] for c in t['calls']]
    results = [r for t in trace['turns'] for r in t['results']]
    in_output = any(present(r.get('stdout') or '', reference) for r in results)
    if final_ok:
        category = 'correct'
    elif trace['final_status'] == 'ROUND_LIMIT':
        category = 'limite_de_tours'
    elif trace['final_status'] == 'MALFORMED_CALL':
        category = 'appel_malforme'
    elif not calls:
        category = 'sans_appel'
    elif not any(r['status'] == 'OK' for r in results):
        category = 'erreur_execution'
    elif not in_output:
        category = 'mauvais_calcul'
    else:
        category = 'mauvaise_retranscription'
    return {'calls': len(calls), 'ok_results': sum(r['status'] == 'OK' for r in results),
            'reference_in_tool_output': in_output, 'category': category}
