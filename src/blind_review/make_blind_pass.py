"""Blind second pass on the decisive R2F subsets (H1 C « contredit », H2 R3 cases, H3 32 conflicts; H4 inside).

Identical answers to the same case are merged; arms are hidden; order is shuffled with a fixed seed.
Writes review_work/blind_batch_{1,2,3}.json (disjoint) and review_work/_PRIVATE_BLIND_MAP.json
(read only after all batches are returned and locked by lock_blind_pass.py).
"""
import hashlib
import json
import random
from pathlib import Path

W = Path(__file__).resolve().parents[2]
OUT = W / 'outputs/core_4b_r2f_r1'
EXT = OUT / 'results/extracted'
REV = OUT / 'review_work'


def rows(p):
    return [json.loads(s) for s in Path(p).read_text(encoding='utf-8').splitlines() if s.strip()]


def main():
    REV.mkdir(exist_ok=True)
    assert not (REV / '_PRIVATE_BLIND_MAP.json').exists()
    gold = {g['slot_id']: g for g in rows(OUT / 'data_build/test_gold_local.jsonl')}
    inputs = {r['slot_id']: r for r in rows(EXT / 'inputs.jsonl')}
    m = json.loads((EXT / 'manifest.json').read_text(encoding='utf-8'))
    wanted = [s for s, g in gold.items() if (g['kind'] == 'fresh' and g['family'] == 'C' and g['decisive_false'])
              or g['kind'] in ('r3_contredit', 'conflict')]
    merged = {}
    for arm in m['evaluation_arms']:
        preds = {r['slot_id']: r for r in rows(EXT / 'evaluation' / arm / 'predictions.jsonl')}
        for s in wanted:
            key = (s, preds[s]['prediction'])
            merged.setdefault(key, []).append(arm)
    items, private = [], {}
    rng = random.Random(20260928)
    keys = sorted(merged)
    rng.shuffle(keys)
    for n, (s, pred) in enumerate(keys, 1):
        g = gold[s]
        bid = f'B{n:03d}'
        items.append(dict(id=bid, instruction=inputs[s]['instruction'], contexte=inputs[s]['contexte'], reponse=pred,
                          attendu=dict(verdict=g['verdict'], regle=g['rule'], etat_premier=g['first'], etat_second=g['second'],
                                       note='C = sources opposées (inconnu)' if 'C' in (g['first'], g['second']) else '')))
        private[bid] = dict(slot_id=s, arms=merged[(s, pred)])
    third = (len(items) + 2) // 3
    for k in range(3):
        (REV / f'blind_batch_{k + 1}.json').write_text(json.dumps(items[k * third:(k + 1) * third], ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (REV / '_PRIVATE_BLIND_MAP.json').write_text(json.dumps(private, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    digest = hashlib.sha256((REV / '_PRIVATE_BLIND_MAP.json').read_bytes()).hexdigest()
    (REV / 'BLIND_PREPARED.json').write_text(json.dumps(dict(items=len(items), batches=3, map_sha256=digest,
                                                             subsets=['H1 C decisive false', 'H2 R3 contredit', 'H3 conflicts']),
                                                        indent=1) + '\n', encoding='utf-8')
    print(len(items), 'unique answers in 3 batches; map', digest[:12])


if __name__ == '__main__':
    main()
