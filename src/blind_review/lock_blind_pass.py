"""Validate and lock the blind second pass, THEN open the private map and summarize per arm.

Compares each reviewer's verdict_initial with the automatic classifier (agreement) and reports,
per arm and subset, verdict_ok / statuts_ok / coherence_ok / joint (all four ok incl. justification).
"""
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W / 'work/core_4b_contredit_probe_r1'))
from verdict_classifier import classify  # noqa: E402

OUT = W / 'outputs/core_4b_r2f_r1'
REV = OUT / 'review_work'
FIELDS = {'id', 'verdict_initial', 'verdict_ok', 'statuts_ok', 'coherence_ok', 'justification_ok', 'grave', 'note'}
EXPECTED = {'irrecevable': 'FALSE', 'recevable': 'TRUE', 'indéterminé': 'UNKNOWN'}


def main():
    items = {}
    for k in (1, 2, 3):
        for it in json.loads((REV / f'blind_batch_{k}.json').read_text(encoding='utf-8')):
            items[it['id']] = it
    decisions, inconsistencies = {}, []
    for k in (1, 2, 3):
        for d in json.loads((REV / f'blind_pass_{k}.json').read_text(encoding='utf-8')):
            assert set(d) == FIELDS, (k, d.get('id'), set(d) ^ FIELDS)
            assert d['id'] in items and d['id'] not in decisions, d['id']
            assert d['verdict_initial'] in ('TRUE', 'FALSE', 'UNKNOWN', 'OTHER') and d['grave'] in ('none', 'minor', 'major')
            assert all(isinstance(d[f], bool) for f in ('verdict_ok', 'statuts_ok', 'coherence_ok', 'justification_ok'))
            exp = EXPECTED[items[d['id']]['attendu']['verdict']]
            if d['verdict_ok'] != (d['verdict_initial'] == exp):  # reviewer slip: verdict_ok recomputed, slip recorded
                inconsistencies.append(dict(id=d['id'], reviewer_verdict_ok=d['verdict_ok'], verdict_initial=d['verdict_initial'], expected=exp))
                d = dict(d, verdict_ok=d['verdict_initial'] == exp)
            decisions[d['id']] = d
    assert set(decisions) == set(items), set(items) - set(decisions)
    lock = REV / 'BLIND_LOCKED.json'
    assert not lock.exists()
    digest = hashlib.sha256(json.dumps(decisions, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    lock.write_text(json.dumps(dict(state='BLIND_PASS_LOCKED', items=len(decisions), decisions_sha256=digest), indent=1) + '\n', encoding='utf-8')
    private = json.loads((REV / '_PRIVATE_BLIND_MAP.json').read_text(encoding='utf-8'))
    prepared = json.loads((REV / 'BLIND_PREPARED.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((REV / '_PRIVATE_BLIND_MAP.json').read_bytes()).hexdigest() == prepared['map_sha256']
    gold = {json.loads(s)['slot_id']: json.loads(s) for s in (OUT / 'data_build/test_gold_local.jsonl').read_text(encoding='utf-8').splitlines() if s.strip()}
    per = collections.defaultdict(lambda: collections.Counter())
    agree = collections.Counter()
    for bid, d in decisions.items():
        auto = classify(items[bid]['reponse'])
        auto = 'OTHER' if auto == 'CONTRADICTION' else auto
        agree['same' if auto == d['verdict_initial'] else 'diff'] += 1
        g = gold[private[bid]['slot_id']]
        subsets = ['H1_C_contredit' if g['kind'] == 'fresh' else 'H2_R3' if g['kind'] == 'r3_contredit' else 'H3_conflict']
        if g['kind'] == 'fresh' and g.get('rule') == 'both' and {g['first'], g['second']} == {'F', 'U'}:
            subsets.append('H4_C_both_FU_UF')
        if g['kind'] == 'conflict' and g.get('rule') == 'both' and (g['first'], g['second']) == ('C', 'F'):
            subsets.append('H4_conflict_both_CF')
        joint = d['verdict_ok'] and d['statuts_ok'] and d['coherence_ok'] and d['justification_ok']
        for arm in private[bid]['arms']:
            for subset in subsets:
                c = per[(arm, subset)]
                c['n'] += 1
                c['verdict_ok'] += d['verdict_ok']
                c['statuts_ok'] += d['statuts_ok']
                c['coherence_ok'] += d['coherence_ok']
                c['joint'] += joint
                c['major'] += d['grave'] == 'major'
    summary = {f'{a}|{s}': dict(c) for (a, s), c in sorted(per.items())}
    diffs = [dict(id=b, reviewer=decisions[b]['verdict_initial'],
                  auto=('OTHER' if classify(items[b]['reponse']) == 'CONTRADICTION' else classify(items[b]['reponse'])),
                  reponse=items[b]['reponse'][:200]) for b in decisions
             if (('OTHER' if classify(items[b]['reponse']) == 'CONTRADICTION' else classify(items[b]['reponse'])) != decisions[b]['verdict_initial'])]
    result = dict(state='BLIND_PASS_SUMMARIZED', items=len(decisions), classifier_agreement=dict(agree), disagreements=diffs,
                  reviewer_verdict_ok_slips=inconsistencies,
                  per_arm_subset=summary)
    target = OUT / 'BLIND_PASS_SUMMARY.json'
    assert not target.exists()
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for k, v in summary.items():
        print(k.ljust(32), v)
    print('agreement', dict(agree))


if __name__ == '__main__':
    main()
