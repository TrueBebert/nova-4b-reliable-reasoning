"""TOOLCALC R2 pre-registered analysis (Opus 5.5, 29/09/2026). Code only, no LLM judge; frozen with PROTOCOLE.md.
  python analyze.py RESULTS_DIR   -> RESULTS.json next to RESULTS_DIR (never overwrites) + printed summary.

System answer per router X in {A (lexicon), B (model triage)}: if X routes the case, the R2 tool answer, replaced by the
direct (production) answer when the tool path fails (loop_r2.system_answer); otherwise the direct answer.
Scoring as R1 (scoring.score on S/P/E, exact equality on C/F). Paired against the direct answer:
  gain_robuste  VF false -> true and the direct answer never states the reference value; regression VF true -> false.
Criteria per router (thresholds fixed before any R2 output):
  CALC  P+E: gain_robuste - regression >= 18, exact two-sided sign test p <= 0.01; P alone: >= 4   (as R1);
  HARM  F (fresh, 542): 0 answer with tool markup, 0 missing answer, (exact -> not) - (not -> exact) <= 3.
C (148, already inspected in R1) is reported with the same harm measures, as secondary evidence only.
Decision: INTEGRATION_VALIDEE_DEV if at least one router meets CALC and HARM (retained router: the larger P+E net robust
gain among them, tie -> A); APPORT_AVEC_RESERVES if a router meets CALC but none meets both; NON_VALIDEE otherwise."""
from __future__ import annotations

import collections
import json
import math
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import loop_r2  # noqa: E402
import scoring  # noqa: E402
import toolcall  # noqa: E402

THRESHOLDS = {'net_gain_min_PE': 18, 'p_max': 0.01, 'net_gain_min_P': 4, 'f_markup_max': 0, 'f_missing_max': 0,
              'f_exact_net_loss_max': 3}
EXPECTED = {'S': 2, 'P': 42, 'E': 142, 'C': 148, 'F': 542}
VERDICT = re.compile(r'"verdict"\s*:\s*"([A-Z_]+)"')


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = max(wins, losses)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k, n + 1)) / 2 ** n)


def system(record, router):
    routed = record['route_a'] if router == 'A' else record['route_b'] == 'OUI'
    if not routed:
        return record['direct']['final'], False, False
    final, fallback = loop_r2.system_answer(record['outil'], record['direct']['final'])
    return final, True, fallback


def calc_block(records, refs, router):
    c = collections.Counter()
    for r in records:
        ref = refs[r['slot_id']]['reponse']
        final, routed, fallback = system(r, router)
        d, s = scoring.score(r['direct']['final'], ref), scoring.score(final, ref)
        c['n'] += 1; c['routed'] += routed; c['fallback'] += fallback
        c['vf_direct'] += d['valeur_finale']; c['vf_system'] += s['valeur_finale']
        c['exact_direct'] += d['exact']; c['exact_system'] += s['exact']
        if not d['valeur_finale'] and s['valeur_finale']:
            c['gain'] += 1; c['gain_robuste'] += not d['valeur_presente']
        if d['valeur_finale'] and not s['valeur_finale']:
            c['regression'] += 1
    out = {k: c.get(k, 0) for k in ('n', 'routed', 'fallback', 'vf_direct', 'vf_system', 'exact_direct', 'exact_system', 'gain',
                                    'gain_robuste', 'regression')}
    out['net_robuste'] = out['gain_robuste'] - out['regression']
    out['sign_test_p'] = sign_test(out['gain_robuste'], out['regression'])
    return out


def harm_block(records, refs, router):
    c = collections.Counter()
    changed = []
    verdicts = collections.Counter()
    for r in records:
        ref = refs[r['slot_id']]['reponse'].strip()
        final, routed, fallback = system(r, router)
        direct = r['direct']['final']
        d_ok, s_ok = (direct or '').strip() == ref, (final or '').strip() == ref
        c['n'] += 1; c['routed'] += routed; c['fallback'] += fallback
        c['markup'] += toolcall.leaked_markup(final)
        c['missing'] += final is None or not final.strip()
        c['exact_direct'] += d_ok; c['exact_system'] += s_ok
        c['exact_to_not'] += d_ok and not s_ok; c['not_to_exact'] += (not d_ok) and s_ok
        if final != direct:
            c['changed'] += 1
            changed.append(r['slot_id'])
        if r['family'].startswith('L-'):
            want = VERDICT.search(ref).group(1)
            got = [VERDICT.search(x or '') for x in (direct, final)]
            verdicts['direct_' + ('ok' if got[0] and got[0].group(1) == want else 'ko') + '/system_' +
                     ('ok' if got[1] and got[1].group(1) == want else 'ko')] += 1
    out = {k: c.get(k, 0) for k in ('n', 'routed', 'fallback', 'markup', 'missing', 'exact_direct', 'exact_system', 'exact_to_not',
                                    'not_to_exact', 'changed')}
    out['exact_net_loss'] = out['exact_to_not'] - out['not_to_exact']
    out['changed_slots'] = changed
    out['logic_verdicts'] = dict(verdicts)
    return out


def tool_profile(records):
    c = collections.Counter()
    for r in records:
        t = r['outil']
        if t is None:
            continue
        c['runs'] += 1
        c['final_status_' + t['final_status']] += 1
        c['with_call'] += any(x['calls'] for x in t['turns'])
        for turn in t['turns']:
            for res in turn['results']:
                c['sandbox_' + res['status']] += 1
                c['repaired_escaped_quotes'] += bool(res.get('repaired_escaped_quotes'))
    return dict(sorted(c.items()))


def main():
    results_dir = Path(sys.argv[1]).resolve()
    target = results_dir.parent / 'RESULTS.json'
    assert not target.exists(), 'Never overwrite'
    out_root = HERE.parents[1] / 'outputs/core_4b_toolcalc_r2'
    refs = {json.loads(x)['slot_id']: json.loads(x) for x in (out_root / 'REFERENCES.jsonl').read_text(encoding='utf-8').splitlines()}
    records = [json.loads(x) for x in (results_dir / 'r2f/responses.jsonl').read_text(encoding='utf-8').splitlines()]
    sets = collections.defaultdict(list)
    for r in records:
        sets[r['set']].append(r)
    complete = {k: len(v) for k, v in sorted(sets.items())}
    report = {'thresholds': THRESHOLDS, 'complete_cases': complete,
              'complete_as_planned': all(complete.get(k) == v for k, v in EXPECTED.items()), 'routers': {},
              'triage_decisions': {s: dict(collections.Counter(r['route_b'] for r in v)) for s, v in sorted(sets.items())},
              'route_a_by_set': {s: sum(r['route_a'] for r in v) for s, v in sorted(sets.items())},
              'tool_profile_by_set': {s: tool_profile(v) for s, v in sorted(sets.items())}}
    for router in ('A', 'B'):
        sec = {'P': calc_block(sets['P'], refs, router), 'E': calc_block(sets['E'], refs, router),
               'PE': calc_block(sets['P'] + sets['E'], refs, router), 'S': calc_block(sets['S'], refs, router),
               'F_harm': harm_block(sets['F'], refs, router), 'C_harm': harm_block(sets['C'], refs, router)}
        fam = collections.defaultdict(list)
        for r in sets['P'] + sets['E']:
            fam[r['family']].append(r)
        sec['PE_by_family'] = {f: {k: v for k, v in calc_block(rs, refs, router).items()
                                   if k in ('n', 'routed', 'vf_direct', 'vf_system', 'gain_robuste', 'regression', 'fallback')}
                               for f, rs in sorted(fam.items())}
        pe, p, fh = sec['PE'], sec['P'], sec['F_harm']
        sec['calc_criterion'] = pe['net_robuste'] >= THRESHOLDS['net_gain_min_PE'] and pe['sign_test_p'] <= THRESHOLDS['p_max'] \
            and p['net_robuste'] >= THRESHOLDS['net_gain_min_P']
        sec['harm_criterion_F'] = fh['markup'] <= THRESHOLDS['f_markup_max'] and fh['missing'] <= THRESHOLDS['f_missing_max'] \
            and fh['exact_net_loss'] <= THRESHOLDS['f_exact_net_loss_max']
        report['routers'][router] = sec
    both = [x for x in ('A', 'B') if report['routers'][x]['calc_criterion'] and report['routers'][x]['harm_criterion_F']]
    if both:
        best = max(both, key=lambda x: (report['routers'][x]['PE']['net_robuste'], x == 'A'))
        decision = 'INTEGRATION_VALIDEE_DEV'
    elif any(report['routers'][x]['calc_criterion'] for x in ('A', 'B')):
        best, decision = None, 'APPORT_AVEC_RESERVES'
    else:
        best, decision = None, 'NON_VALIDEE'
    report['decision'] = {'decision': decision if report['complete_as_planned'] else decision + '_SUR_RUN_INCOMPLET',
                          'retained_router': best, 'routers_meeting_both': both}
    with target.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print(json.dumps({'complete': complete, 'decision': report['decision'], 'triage': report['triage_decisions']}, ensure_ascii=False))
    for router in ('A', 'B'):
        s = report['routers'][router]
        print(f"router {router}: calc={s['calc_criterion']} harm_F={s['harm_criterion_F']}")
        for name in ('P', 'E', 'PE'):
            b = s[name]
            print(f"  {name}: VF {b['vf_direct']} -> {b['vf_system']}/{b['n']} ; routés {b['routed']} ; replis {b['fallback']} ; gains "
                  f"robustes {b['gain_robuste']} ; régressions {b['regression']} ; p={b['sign_test_p']:.2g} ; exact "
                  f"{b['exact_direct']} -> {b['exact_system']}")
        for name in ('F_harm', 'C_harm'):
            print(f'  {name}:', {k: v for k, v in s[name].items() if k != 'changed_slots'})


if __name__ == '__main__':
    main()
