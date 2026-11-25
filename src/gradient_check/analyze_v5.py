"""CPU analysis of the v5 runtime-choice test (after BACKUP_VERIFIED): applies REGLES_V5.md, frozen before launch (sha256
checked). Writes RESULTS_V5.json; never overwrites."""
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/core_4b_native_runtime_choice_r1'
RES = OUT / 'results'
RULES_SHA256 = '1336b04467fce8acac03bd918a94ca91692c2d45c5e3ee5b040c8a211e4756bd'
NO_COMPILE_MODES = ('UE', 'UEN', 'UEF')
ALL_MODES = NO_COMPILE_MODES + ('UCC',)
V4_UE = {'trainer': [0.05978, 0.18576], 'x1': [0.05882, 0.18592]}


def load(p):
    p = Path(p)
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None


def main():
    target = OUT / 'RESULTS_V5.json'
    assert (OUT / 'BACKUP_VERIFIED.json').exists() and not target.exists()
    rules_sha = hashlib.sha256((OUT / 'REGLES_V5.md').read_bytes()).hexdigest()
    if rules_sha != RULES_SHA256:
        raise ValueError(f'rules changed: observed={rules_sha}; expected={RULES_SHA256}')
    cmp = load(RES / 'mode_CMP/COMPARISONS.json')
    if cmp is None:
        raise FileNotFoundError('mode_CMP/COMPARISONS.json missing: see mode_CMP/FAIL.json')
    vt, pairs = cmp['versus_truth'], cmp['pairs']
    e = {tag: [r['relative_l2'] for r in recs] for tag, recs in vt.items()}
    noise = max(e['T_t32b'])
    floor = 10 * noise
    e_h = e['T_h16a']
    s = [max(1.5 * e_h[g], e_h[g] + 0.02) for g in (0, 1)]
    modes = {}
    for m in ALL_MODES:
        if f'{m}_trainer' not in e:
            modes[m] = {'complete': False, 'fail': (load(RES / f'mode_{m}/FAIL.json') or {}).get('error', '')[:400]}
            continue
        stab = {r: [pairs[f'{m}_{r} vs {m}_x1'][g]['relative_l2'] for g in (0, 1)] for r in ('x1b', 'x2', 'trainer')}
        stable = all(max(v) <= max(0.02, floor) for v in stab.values())
        exact = all(e[f'{m}_trainer'][g] <= s[g] for g in (0, 1))
        inproc = load(RES / f'mode_{m}/IN_PROCESS.json') or {}
        modes[m] = {'complete': True, 'e_trainer': e[f'{m}_trainer'], 'e_x1': e[f'{m}_x1'], 'e_x2': e[f'{m}_x2'],
                    'stability_vs_x1': stab, 'stable': stable, 'exact': exact, 'valid': stable and exact,
                    'seconds': {r: v.get('seconds') for r, v in inproc.items()},
                    'runtime_facts': load(RES / f'mode_{m}/RUNTIME_FACTS.json')}
    valid = [m for m in NO_COMPILE_MODES if modes[m].get('valid')]
    if valid:
        best = min(valid, key=lambda m: max(modes[m]['e_trainer']))
        close = [m for m in valid if max(modes[m]['e_trainer']) - max(modes[best]['e_trainer']) < 0.01]
        choice = min(close, key=lambda m: modes[m]['seconds'].get('x1b') or float('inf'))
        decision = (f'Runtime R3 retenu : {choice} (valide ; plus grand e(trainer) = {max(modes[choice]["e_trainer"]):.3f}'
                    + (f' ; départagé à la vitesse parmi {close}' if len(close) > 1 else '') + ').')
    else:
        choice = 'HF_PEFT'
        decision = ('Aucun mode Unsloth sans compilation valide : R3 sur transformers + PEFT standard (nouveau code '
                    'd\'entraînement à écrire et valider), Unsloth écarté.')
    ucc = modes.get('UCC', {})
    ucc_note = ('UCC valide : compilation propre = piste d\'accélération, à confirmer sur un autre Pod ; non retenue pour R3.'
                if ucc.get('valid') else 'UCC non valide : la compilation reste écartée.')
    report = {'state': 'NATIVE_RUNTIME_V5_ANALYZED', 'rules_sha256': rules_sha, 'truth_repeat_noise': noise,
              'interpretation_floor': floor, 'e_H': e_h, 'threshold_s': s, 'relative_l2_vs_truth': e, 'modes': modes,
              'choice': choice, 'decision': decision, 'ucc_note': ucc_note,
              'ue_vs_v4': {'v4': V4_UE, 'v5': {'trainer': e.get('UE_trainer'), 'x1': e.get('UE_x1')}},
              'truth_norms': [vt['T_t32a'][g]['reference_norm'] for g in (0, 1)], 'pairs': pairs,
              'summary_remote': load(RES / 'SUMMARY.json'),
              'limits': ['Une exécution par mode, un seul GPU ; six lignes en deux groupes.',
                         'Mesure de précision du gradient, pas de qualité d\'entraînement.', 'Auto-relecture.']}
    with target.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({'noise': noise, 'e_H': e_h, 's': s,
                      'modes': {m: {k: v for k, v in d.items() if k in ('e_trainer', 'stable', 'exact', 'valid', 'seconds', 'fail')}
                                for m, d in modes.items()},
                      'decision': decision, 'ucc': ucc_note}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
