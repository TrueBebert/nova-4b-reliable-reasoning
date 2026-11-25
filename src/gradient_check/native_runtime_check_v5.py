"""Bounded, opt-in Runpod diagnostic v5 (Opus 5.5): choice of the native training runtime against the fp32 truth.

v4 measured, against a float32 truth, the compiled Unsloth path (history-dependent, layers 0-3 wrong by up to 114 %),
the non-compiled Unsloth path (deterministic; 0.059 / 0.186 on groups 0 / 1) and standard transformers + PEFT bf16
(0.110 / 0.099). Reading the installed unsloth_zoo 2026.8.15 showed two Unsloth mechanisms active in BOTH paths:
vendored fla Triton kernels for the Gated DeltaNet layers, whose autotuners are patched to reuse the first tuned config for
every unseen shape (compile_fla_no_autotune), and a persistent cross-process compile cache (Mega-cache) plus torch's
on-disk Inductor caches. v5 measures one environment-variable change at a time, same rows, loss and truth as v4.

Modes, each a SEPARATE child process run in this order by the supervisor:
  T    NO Unsloth import (transformers + PEFT, eager, no compile). t32 = float32 truth (TF32 off), twice; h16 = standard
       bf16 weights + autocast, twice.
  UE   Unsloth, UNSLOTH_COMPILE_DISABLE=1 (the v4 non-compiled runtime, repeated on a new pod).
  UEN  UE + UNSLOTH_DISABLE_FLA_NO_AUTOTUNE=1 (fla autotuned per shape, no config reuse).
  UEF  UE + UNSLOTH_DISABLE_VENDORED_FLA=1 (pure-torch Gated DeltaNet, as transformers).
  UCC  compile ON with every cross-run cache disabled (UNSLOTH_MEGA_CACHE=0, TORCHINDUCTOR_FORCE_DISABLE_CACHES=1) and
       UNSLOTH_DISABLE_FLA_NO_AUTOTUNE=1: can compile be made history-independent?
  Each Unsloth mode: x1 (per-row snapshots), x1b (again, no reset), reset, x2, reset, trainer (2 steps, lr 0); wall time
  of every pass is recorded, with the Gated DeltaNet implementation actually bound and the Mega-cache status.
  CMP  CPU tensors only: every vector against the fp32 truth, per layer / kind / lora side, plus determinism pairs.
No threshold is used here to pass or fail: this test measures; the decision rules are frozen in a separate file before
the comparisons. Nothing is trained beyond the lr-0 probe; no promotion.
Only stdlib is imported until the signed package and the explicit authorization are checked.
"""
from __future__ import annotations
import argparse
import contextlib
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import secrets
import subprocess
import sys
import time
import traceback
import zipfile

HERE = Path(__file__).resolve().parent
SCOPE = 'CORE_NATIVE_RUNTIME_CHOICE_V5'
NO_COMPILE = {'UNSLOTH_COMPILE_DISABLE': '1'}
def _own_cache(mode):
    # Each Unsloth mode starts from its own empty Mega-cache directory, as on a fresh pod: the bundle key does not include
    # the fla variables, so a shared directory would let UEN/UEF load what UE saved at exit.
    return {'UNSLOTH_MEGA_CACHE_DIR': '/root/core_v5_megacache_' + mode}


MODES = (('T', 420, {}),
         ('UE', 420, dict(NO_COMPILE, **_own_cache('UE'))),
         ('UEN', 420, dict(NO_COMPILE, UNSLOTH_DISABLE_FLA_NO_AUTOTUNE='1', **_own_cache('UEN'))),
         ('UEF', 540, dict(NO_COMPILE, UNSLOTH_DISABLE_VENDORED_FLA='1', **_own_cache('UEF'))),
         ('UCC', 600, dict({'UNSLOTH_MEGA_CACHE': '0', 'TORCHINDUCTOR_FORCE_DISABLE_CACHES': '1',
                            'UNSLOTH_DISABLE_FLA_NO_AUTOTUNE': '1'}, **_own_cache('UCC'))),
         ('CMP', 240, {}))  # CMP: CPU tensors only
UNSLOTH_MODES = ('UE', 'UEN', 'UEF', 'UCC')
RUNTIME_ENV = ('UNSLOTH_COMPILE_DISABLE', 'UNSLOTH_DISABLE_FLA_NO_AUTOTUNE', 'UNSLOTH_DISABLE_VENDORED_FLA', 'UNSLOTH_MEGA_CACHE',
               'TORCHINDUCTOR_FORCE_DISABLE_CACHES', 'UNSLOTH_MEGA_CACHE_DIR')
GLOBAL_LIMIT_SECONDS = 2760  # sum of mode limits (2640) + base hashing (~60 s) + margin: CMP is never skipped for time
TRAINABLE_COUNT = 21233664
KINDS = ('q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj')
SEQUENCE = (('x1', False, True), ('x1b', False, False), ('x2', True, False))  # (regime, reset before, per-row snapshots)
ARM = 'treatment'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(label, observed, expected, out):
    with (out / 'CHECKS.jsonl').open('a', encoding='utf-8') as f:
        f.write(json.dumps({'check': label, 'observed': observed, 'expected': expected}, ensure_ascii=False) + '\n')
    if observed != expected:
        raise ValueError(f'{label}: observed={observed!r}; expected={expected!r}')


def canonical(name):
    """PEFT/Unsloth parameter name -> 'layers.N.<module>.<proj>.lora_X.weight' (identical in both worlds)."""
    i = name.find('layers.')
    if i < 0 or 'lora_' not in name:
        raise ValueError(f'Unexpected trainable parameter: {name}')
    return name[i:].replace('.default', '')


def order_key(key):
    return int(key.split('.')[1]), key


def compare(actual, ref):
    """float64 comparison record; identity residual checks that the four numbers are mutually consistent."""
    norm = float(ref.norm()); actual_norm = float(actual.norm())
    dot = float(actual.dot(ref))
    error = float((actual - ref).norm()) / max(norm, 1e-30)
    cosine = dot / max(actual_norm * norm, 1e-30)
    scale = dot / max(norm * norm, 1e-30)
    residual = abs(error * error - (1 + (actual_norm / max(norm, 1e-30)) ** 2 - 2 * scale))
    return {'reference_norm': norm, 'actual_norm': actual_norm, 'relative_l2': error, 'cosine': cosine,
            'gradient_scale': scale, 'identity_residual': residual}


def groups(data):
    return [{'update_index': i // 4, 'positions': [x['_core_position'] for x in data[i:i+4]],
             'example_count': len(data[i:i+4]),
             'supervised_denominator': sum(sum(t != -100 for t in x['labels'][1:]) for x in data[i:i+4])}
            for i in range(0, len(data), 4)]


def encode_rows(tok, out, C):
    data = []
    for i, line in enumerate((HERE / 'data' / (ARM + '_full_734.jsonl')).read_text(encoding='utf-8').splitlines()):
        item = C.encode(tok, json.loads(line))
        require(f'encode/{i}/one_eos', item['input_ids'][item['boundary']:].count(tok.convert_tokens_to_ids('<|im_end|>')), 1, out)
        data.append({'input_ids': item['input_ids'], 'labels': item['labels'], '_core_position': i})
    require(ARM + '/groups', groups(data), read(HERE / (ARM.upper() + '_ACCUMULATION_PLAN.json')), out)
    chosen = data[:4] + data[-2:]
    digest = hashlib.sha256(json.dumps([[x['input_ids'], x['labels']] for x in chosen], separators=(',', ':'))
                            .encode('ascii')).hexdigest()
    save(out / 'INPUTS.json', {'sha256_ids_labels': digest, 'positions': [x['_core_position'] for x in chosen],
                               'lengths': [len(x['input_ids']) for x in chosen], 'groups': groups(chosen)})
    return data, chosen


def grads_dict(trainable):
    # Missing gradients are evidence of a detached loss, not zeros.
    if any(p.grad is None for _, p in trainable):
        raise ValueError('Missing trainable LoRA gradient')
    return {canonical(n): p.grad.detach().float().cpu().clone() for n, p in trainable}


def save_vectors(vecdir, tag, vectors):
    from safetensors.torch import save_file
    paths = []
    for g, vec in enumerate(vectors):
        path = vecdir / f'{tag}_g{g}.safetensors'
        if path.exists():
            raise FileExistsError(path)
        save_file({k: v.contiguous() for k, v in vec.items()}, str(path))
        paths.append(path.name)
    return paths


def flat(vec):
    import torch
    return torch.cat([vec[k].flatten().double() for k in sorted(vec, key=order_key)])


def reference_pass(model, chosen, trainable, collator, device, autocast, keep_rows):
    """Direct backward: sum of token cross-entropies / group supervised count, one row at a time (as v3)."""
    import torch
    vectors = []
    model.train()
    for start in (0, 4):
        model.zero_grad(set_to_none=True)
        subset = chosen[start:start + 4]
        denominator = sum(sum(t != -100 for t in x['labels'][1:]) for x in subset)
        for row in subset:
            batch = collator([row]); batch.pop('_core_position')
            labels = batch.pop('labels').to(device)
            ctx = torch.autocast(device_type=device, dtype=torch.bfloat16) if autocast else contextlib.nullcontext()
            with ctx:
                logits = model(**{k: v.to(device) for k, v in batch.items()}).logits
            target = labels[:, 1:]; mask = target.ne(-100)
            selected = logits[:, :-1, :][mask].float()
            numerator = -selected.log_softmax(-1).gather(1, target[mask, None]).sum()
            (numerator / denominator).backward()
            del logits, selected, numerator, batch, labels
            if keep_rows and start == 0:
                grads_dict(trainable)  # same host synchronisation pattern as v3's per-row snapshots
        vectors.append(grads_dict(trainable))
    model.zero_grad(set_to_none=True)
    return vectors


def runtime_facts(model):
    """Which Gated DeltaNet implementation is actually bound, whether fla is Unsloth's vendored copy, cache status."""
    facts = {'env': {k: os.environ.get(k) for k in RUNTIME_ENV}}
    for m in model.modules():
        if type(m).__name__.endswith('GatedDeltaNet'):
            fn = getattr(m, 'chunk_gated_delta_rule', None)
            facts['gdn_class'] = type(m).__module__ + '.' + type(m).__name__
            facts['gdn_chunk_fn'] = f"{getattr(fn, '__module__', None)}.{getattr(fn, '__qualname__', getattr(fn, '__name__', None))}"
            break
    fla = sys.modules.get('fla')
    facts['fla_loaded'] = fla is not None
    facts['fla_vendored'] = bool(getattr(fla, '_UNSLOTH_VENDORED_FLA', False)) if fla is not None else None
    # Never import unsloth_zoo here: in mode T that would inject the vendored fla into the truth process.
    cache_module = sys.modules.get('unsloth_zoo.compile_cache')
    try:
        facts['megacache'] = cache_module.megacache_status() if cache_module is not None else 'unsloth_zoo not loaded'
    except Exception as exc:
        facts['megacache'] = 'n/a: ' + type(exc).__name__
    return facts


def timed_pass(*args):
    import torch
    sync = torch.cuda.synchronize if torch.cuda.is_available() else (lambda: None)
    sync(); t0 = time.perf_counter()
    vectors = reference_pass(*args)
    sync()
    return vectors, round(time.perf_counter() - t0, 3)


def quick(vectors, base):
    return [dict(compare(flat(v), flat(b)), group=g) for g, (v, b) in enumerate(zip(vectors, base))]


def preflight(args):
    if sys.platform != 'linux':
        raise RuntimeError('GPU diagnostic is restricted to an explicitly authorized Linux Runpod host')
    spec = read(HERE / 'NATIVE_MANIFEST.json')
    auth = read(args.authorization)
    expected = {'scope': SCOPE, 'authorized': True, 'manifest_sha256': sha(HERE / 'NATIVE_MANIFEST.json'),
                'pod_id': os.environ.get('RUNPOD_POD_ID'), 'full_campaign_authorized': False}
    if not expected['pod_id'] or any(auth.get(k) != v for k, v in expected.items()):
        raise ValueError(f'Explicit authorization mismatch; observed={auth}; expected={expected}')
    for name, digest in spec['files'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError(f'Unsafe package path: {name}')
        actual = sha(HERE / name)
        if actual != digest:
            raise ValueError(f'Package {name}: observed={actual}; expected={digest}')
    return spec


def initial_adapter(args, out):
    initial = out / 'initial_adapter'; initial.mkdir()
    shutil.copy2(HERE / 'adapter/adapter_model.safetensors', initial / 'adapter_model.safetensors')
    config = read(HERE / 'adapter/adapter_config.json')
    require('lora_dropout', config['lora_dropout'], 0.0, out)
    config['base_model_name_or_path'] = str(args.base_model.resolve())
    save(initial / 'adapter_config.json', config)
    return initial


def worker_truth(args, spec, out, vecdir, device='cuda'):
    """No Unsloth: transformers + PEFT. t32 = fp32 truth (TF32 off), h16 = standard bf16 weights + autocast."""
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1', TOKENIZERS_PARALLELISM='false')
    import gc
    import torch
    from peft import PeftModel
    from safetensors.torch import load_file
    from transformers import AutoTokenizer, Qwen3_5ForConditionalGeneration
    import label_contract as C
    from runtime_contract import cpu_or_native_collator
    require('no_unsloth_imported', sorted(m for m in sys.modules if m.split('.')[0] in ('unsloth', 'unsloth_zoo')), [], out)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.set_float32_matmul_precision('highest')
    if device == 'cuda':
        require('device_count', torch.cuda.device_count(), 1, out)
        require('bf16_supported', torch.cuda.is_bf16_supported(), True, out)
    tok = AutoTokenizer.from_pretrained(str(args.base_model), local_files_only=True)
    _, chosen = encode_rows(tok, out, C)
    initial = initial_adapter(args, out)
    expected = load_file(str(initial / 'adapter_model.safetensors'))
    results = {}
    for regime, dtype, autocast in (('t32', torch.float32, False), ('h16', torch.bfloat16, True)):
        model = Qwen3_5ForConditionalGeneration.from_pretrained(str(args.base_model), dtype=dtype, attn_implementation='eager',
                                                                local_files_only=True,
                                                                device_map={'': 'cuda:0' if device == 'cuda' else device})
        model.config.use_cache = False
        if hasattr(model.config, 'text_config'):
            model.config.text_config.use_cache = False
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        model = PeftModel.from_pretrained(model, str(initial), is_trainable=True)
        trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
        require(regime + '/lora_only', bool(trainable) and all('lora_' in n for n, _ in trainable), True, out)
        require(regime + '/trainable_count', sum(p.numel() for _, p in trainable), TRAINABLE_COUNT, out)
        by_key = {canonical(n): p for n, p in trainable}
        file_by_key = {canonical(k): v for k, v in expected.items()}
        require(regime + '/adapter_keys', sorted(by_key), sorted(file_by_key), out)
        require(regime + '/adapter_weights_exact', all(torch.equal(p.detach().float().cpu(), file_by_key[k].float())
                                                       for k, p in by_key.items()), True, out)
        require(regime + '/base_dtype', str(model.get_base_model().model.language_model.embed_tokens.weight.dtype), str(dtype), out)
        facts = runtime_facts(model)
        first, t_first = timed_pass(model, chosen, trainable, cpu_or_native_collator, device, autocast, False)
        second, t_second = timed_pass(model, chosen, trainable, cpu_or_native_collator, device, autocast, False)
        results[regime] = {'files': save_vectors(vecdir, f'T_{regime}a', first) + save_vectors(vecdir, f'T_{regime}b', second),
                           'repeat_vs_first': quick(second, first), 'adapter_dtype': str(trainable[0][1].dtype),
                           'seconds_per_pass': [t_first, t_second], 'runtime': facts,
                           'peak_vram_bytes': torch.cuda.max_memory_allocated() if device == 'cuda' else None}
        save(out / 'IN_PROCESS.json', results)
        del model, trainable, by_key, first, second
        gc.collect()
        if device == 'cuda':
            torch.cuda.empty_cache(); torch.cuda.reset_peak_memory_stats()
    return {'status': 'TRUTH_RECORDED', 'regimes': results, 'tf32': {'matmul': torch.backends.cuda.matmul.allow_tf32,
            'cudnn': torch.backends.cudnn.allow_tf32, 'float32_matmul_precision': torch.get_float32_matmul_precision()}}


def worker_unsloth(args, spec, mode, out, vecdir):
    compile_disabled = os.environ.get('UNSLOTH_COMPILE_DISABLE', '0')
    require('mode/compile_disable_env', compile_disabled, '0' if mode == 'UCC' else '1', out)
    expected_env = dict(next(e for m, _, e in MODES if m == mode))
    require('mode/runtime_env', {k: os.environ.get(k) for k in RUNTIME_ENV}, {k: expected_env.get(k) for k in RUNTIME_ENV}, out)
    # Must precede the Unsloth import; custom loss requires real logits.
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                      TOKENIZERS_PARALLELISM='false', UNSLOTH_RETURN_LOGITS='1')
    versions = {k: importlib.metadata.version(k) for k in spec['versions']}
    require('versions', versions, spec['versions'], out)
    from unsloth import FastLanguageModel
    import torch
    from datasets import Dataset
    from peft import get_peft_model_state_dict
    from safetensors.torch import load_file
    from transformers import TrainerCallback, set_seed
    from trl import SFTTrainer, SFTConfig
    import label_contract as C
    from runtime_contract import instrumented_trainer, cpu_or_native_collator

    require('device_count', torch.cuda.device_count(), 1, out)
    require('bf16_supported', torch.cuda.is_bf16_supported(), True, out)
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    save(out / 'ENVIRONMENT.json', {'mode': mode, 'versions': versions, 'gpu': torch.cuda.get_device_name(),
         'capability': list(torch.cuda.get_device_capability()), 'unsloth_compile_disable': compile_disabled,
         'manifest_sha256': sha(HERE / 'NATIVE_MANIFEST.json'), 'pod_id': os.environ['RUNPOD_POD_ID']})
    Trainer = instrumented_trainer(SFTTrainer)

    def state(model):
        return {n: t.detach().cpu().clone() for n, t in get_peft_model_state_dict(model).items()}

    def matches(actual, expected):
        return set(actual) == set(expected) and all(torch.equal(t, expected[n].to(t.dtype)) for n, t in actual.items())

    def config(path, steps, lr, clip):
        return SFTConfig(output_dir=str(path), bf16=True, fp16=False, per_device_train_batch_size=1,
            gradient_accumulation_steps=4, max_steps=steps, learning_rate=lr, weight_decay=0.01,
            optim='adamw_8bit', max_grad_norm=clip, lr_scheduler_type='cosine', warmup_ratio=0.05,
            train_sampling_strategy='sequential', dataloader_drop_last=False, dataloader_num_workers=0,
            remove_unused_columns=False, packing=False, padding_free=False, max_length=1536,
            dataset_kwargs={'skip_prepare_dataset': True}, report_to='none', logging_strategy='no',
            save_strategy='no', eval_strategy='no', disable_tqdm=True, gradient_checkpointing=True, seed=20260928)

    def unsloth_reset(model):
        """Same reset as Unsloth's _unsloth_reset_stray_compile_cache: dynamo cache, GC buffers, gradients."""
        import torch._dynamo as dynamo
        dynamo.reset()
        from unsloth_zoo.gradient_checkpointing import reset_unsloth_gradient_checkpointing_buffers
        reset_unsloth_gradient_checkpointing_buffers()
        model.zero_grad(set_to_none=True)
        torch.cuda.synchronize()

    initial = initial_adapter(args, out)
    set_seed(20260928)
    model, processor = FastLanguageModel.from_pretrained(model_name=str(initial), max_seq_length=1536,
        dtype=torch.bfloat16, load_in_4bit=False, load_in_8bit=False, load_in_16bit=True,
        full_finetuning=False, fast_inference=False, local_files_only=True, use_gradient_checkpointing='unsloth')
    FastLanguageModel.for_training(model, use_gradient_checkpointing='unsloth')
    model.config.use_cache = False
    tok = processor.tokenizer if hasattr(processor, 'tokenizer') else processor
    trainable = [(n, p) for n, p in model.named_parameters() if p.requires_grad]
    require('lora_only', bool(trainable) and all('lora_' in n for n, _ in trainable), True, out)
    require('trainable_count', sum(p.numel() for _, p in trainable), TRAINABLE_COUNT, out)
    require('weights', matches(state(model), load_file(str(initial / 'adapter_model.safetensors'))), True, out)
    facts = runtime_facts(model)
    save(out / 'RUNTIME_FACTS.json', facts)
    before = state(model)
    data, chosen = encode_rows(tok, out, C)
    selected_groups = groups(chosen)
    # As in v3: build a Trainer and traverse the native prepared loader (no forward) before the first reference, so
    # that x1 is computed in the same state as v3's first reference and as a real run's first step.
    expected_groups = read(HERE / (ARM.upper() + '_ACCUMULATION_PLAN.json'))
    full = Trainer(model=model, args=config(out / 'loader', 184, 0.0, 0.0), train_dataset=Dataset.from_list(data),
                   processing_class=tok, data_collator=cpu_or_native_collator, core_expected_groups=expected_groups,
                   core_trace=out / 'LOADER_TRACE.jsonl')
    loader = full.get_train_dataloader(); iterator = iter(loader)
    for g in expected_groups:
        full.get_batch_samples(iterator, g['example_count'], full.args.device)
    require('loader_groups', full.core_groups, expected_groups, out)
    require('loader_exhausted', next(iterator, None) is None, True, out)
    del iterator, loader, full
    results, base = {}, None
    for regime, reset, keep_rows in SEQUENCE:
        if reset:
            unsloth_reset(model)
        vectors, seconds = timed_pass(model, chosen, trainable, cpu_or_native_collator, 'cuda', True, keep_rows)
        base = base or vectors
        results[regime] = {'reset_before': reset, 'per_row_snapshots': keep_rows, 'seconds': seconds,
                           'files': save_vectors(vecdir, f'{mode}_{regime}', vectors), 'versus_x1': quick(vectors, base)}
        save(out / 'IN_PROCESS.json', results)
    unsloth_reset(model)
    probe = []

    class Probe(TrainerCallback):
        def on_train_begin(self, args_, state_, control, **kwargs):
            require('prepared_model_identity', kwargs['model'] is model, True, out)
            require('prepared_amp', trainer.accelerator.native_amp, True, out)
            require('forward_amp_wrapper', hasattr(model, '_original_forward'), True, out)

        def on_pre_optimizer_step(self, args_, state_, control, **kwargs):
            probe.append(grads_dict(trainable))

    trainer = Trainer(model=model, args=config(out / 'gradient_probe', 2, 0.0, 0.0),
        train_dataset=Dataset.from_list(chosen), processing_class=tok, data_collator=cpu_or_native_collator,
        callbacks=[Probe()], core_expected_groups=selected_groups, core_trace=out / 'TRACE.jsonl')
    torch.cuda.synchronize(); t0 = time.perf_counter()
    trainer.train()
    torch.cuda.synchronize(); train_seconds = round(time.perf_counter() - t0, 3)
    require('two_gradient_groups', len(probe), 2, out)
    require('seen_positions', trainer.core_observed_positions, [0, 1, 2, 3, 732, 733], out)
    require('lr_zero_weights_unchanged', matches(state(model), before), True, out)
    results['trainer'] = {'reset_before': True, 'seconds': train_seconds, 'files': save_vectors(vecdir, f'{mode}_trainer', probe),
                          'versus_x1': quick(probe, base),
                          'native_divisor_after_override': trainer.accelerator.gradient_accumulation_steps}
    save(out / 'IN_PROCESS.json', results)
    return {'status': 'REGIMES_RECORDED', 'mode': mode, 'regimes': results, 'runtime': facts,
            'runtime_after': runtime_facts(model), 'peak_vram_bytes': torch.cuda.max_memory_allocated()}


def layer_and_kind_breakdown(actual, ref, keys, sizes):
    acc, offset = {}, 0
    for key, size in zip(keys, sizes):
        a = actual[offset:offset + size]; r = ref[offset:offset + size]; offset += size
        e = float((a - r).pow(2).sum()); q = float(r.pow(2).sum())
        layer = int(key.split('.')[1])
        kind = next((k for k in KINDS if k in key), 'other')
        side = 'lora_A' if 'lora_A' in key else 'lora_B'
        for bucket in ('layer_%02d' % layer, 'kind:' + kind, 'side:' + side,
                       'block:' + ('mlp' if kind in ('gate_proj', 'up_proj', 'down_proj') else 'attention')):
            v = acc.setdefault(bucket, [0.0, 0.0]); v[0] += e; v[1] += q
    total = sum(v[0] for k, v in acc.items() if k.startswith('kind:')) or 1.0
    return {k: {'relative_l2': math.sqrt(e / q) if q > 0 else None, 'error_share': e / total} for k, (e, q) in sorted(acc.items())}


PAIRS = tuple((f'{m}_{r}', f'{m}_x1') for m in UNSLOTH_MODES for r in ('x1b', 'x2', 'trainer')) + (
    ('UEN_x1', 'UE_x1'), ('UEF_x1', 'UE_x1'), ('UEF_x1', 'T_h16a'), ('UCC_x1', 'UEN_x1'),
    ('T_t32b', 'T_t32a'), ('T_h16b', 'T_h16a'))


def worker_compare(args, out, vecdir):
    import torch
    from safetensors.torch import load_file
    torch.set_num_threads(min(8, os.cpu_count() or 1))
    root = args.out.parent
    digests = {m: read(root / ('mode_' + m) / 'INPUTS.json')['sha256_ids_labels'] for m in ('T',) + UNSLOTH_MODES
               if (root / ('mode_' + m) / 'INPUTS.json').exists()}
    require('inputs_identical_across_modes', len(set(digests.values())), 1, out)
    tags = sorted({p.name.rsplit('_g', 1)[0] for p in vecdir.glob('*.safetensors')})
    truth = [load_file(str(vecdir / f'T_t32a_g{g}.safetensors')) for g in (0, 1)]
    keys = sorted(truth[0], key=order_key)
    sizes = [truth[0][k].numel() for k in keys]
    ref = [flat(t) for t in truth]
    report = {'truth': 'T_t32a', 'tags': tags, 'inputs_sha256': digests, 'versus_truth': {}, 'pairs': {}}
    cache = {}

    def vectors(tag):
        if tag not in cache:
            loaded = [load_file(str(vecdir / f'{tag}_g{g}.safetensors')) for g in (0, 1)]
            for vec in loaded:
                require(tag + '/keys', sorted(vec, key=order_key), keys, out)
                if not all(bool(torch.isfinite(v).all()) for v in vec.values()):
                    raise ValueError(f'Non-finite gradient in {tag}')
            cache.clear()
            cache[tag] = [flat(v) for v in loaded]
        return cache[tag]

    for tag in tags:
        vec = vectors(tag)
        report['versus_truth'][tag] = [dict(compare(vec[g], ref[g]), group=g,
                                            breakdown=layer_and_kind_breakdown(vec[g], ref[g], keys, sizes)) for g in (0, 1)]
        save(out / 'COMPARISONS.json', report)
    for a, b in PAIRS:
        if a in tags and b in tags:
            va = [v.clone() for v in vectors(a)]
            vb = vectors(b)
            report['pairs'][f'{a} vs {b}'] = [dict(compare(va[g], vb[g]), group=g) for g in (0, 1)]
    save(out / 'COMPARISONS.json', report)
    return {'status': 'COMPARED', 'tags': tags}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-model', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--authorization', type=Path, required=True)
    p.add_argument('--vectors', type=Path)
    p.add_argument('--worker', action='store_true')
    p.add_argument('--mode', choices=[m for m, _, _ in MODES])
    args = p.parse_args()
    spec = preflight(args)
    if args.worker:
        started_receipt = read(args.out / 'STARTED.json')
        token = os.environ.get('CORE_RUNTIME_CHILD_TOKEN')
        if not token or token != started_receipt.get('child_token') or started_receipt.get('mode') != args.mode:
            raise RuntimeError('Internal worker must be started by the bounded supervisor')
        with (args.out / 'WORKER_STARTED.json').open('x', encoding='utf-8') as f:
            json.dump({'pid': os.getpid(), 'mode': args.mode}, f)
        try:
            if args.mode == 'T':
                result = worker_truth(args, spec, args.out, args.vectors)
            elif args.mode in UNSLOTH_MODES:
                result = worker_unsloth(args, spec, args.mode, args.out, args.vectors)
            else:
                result = worker_compare(args, args.out, args.vectors)
            save(args.out / 'RESULT.json', result)
        except BaseException as exc:
            save(args.out / 'FAIL.json', {'error': repr(exc), 'traceback': traceback.format_exc()})
            raise
        return
    args.out.mkdir(parents=True, exist_ok=False)
    # This package can be invoked once, even if a caller changes --out.
    with (HERE / 'INVOCATION.json').open('x', encoding='utf-8') as f:
        json.dump({'out': str(args.out), 'pod': os.environ['RUNPOD_POD_ID'], 'started_epoch': time.time()}, f)
    started = time.monotonic()
    for name, digest in spec['base_files'].items():
        require('base/' + name, sha(args.base_model / name), digest, args.out)
    vecdir = args.out.parent / 'vectors'
    free = shutil.disk_usage(args.out.parent).free
    if free < 6 * 1024 ** 3:
        vecdir = Path('/root/core_truth_vectors')
    vecdir.mkdir(parents=True, exist_ok=False)
    save(args.out / 'VECTORS_LOCATION.json', {'path': str(vecdir), 'volume_free_bytes': free})
    summary = []
    for mode, limit, extra_env in MODES:
        remaining = GLOBAL_LIMIT_SECONDS - (time.monotonic() - started)
        mode_out = args.out / ('mode_' + mode); mode_out.mkdir()
        if remaining < limit:
            save(mode_out / 'SKIPPED_BUDGET.json', {'remaining_seconds': remaining, 'mode_limit_seconds': limit})
            summary.append({'mode': mode, 'status': 'SKIPPED_BUDGET'})
            continue
        child_token = secrets.token_hex(16)
        save(mode_out / 'STARTED.json', {'started_epoch': time.time(), 'pod': os.environ['RUNPOD_POD_ID'], 'mode': mode,
                                         'manifest_sha256': sha(HERE / 'NATIVE_MANIFEST.json'), 'limit_seconds': limit,
                                         'grace_seconds': 30, 'child_token': child_token, 'extra_env': extra_env})
        command = [sys.executable, '-u', '-X', 'utf8', '-B', str(Path(__file__).resolve()), '--base-model', str(args.base_model),
                   '--out', str(mode_out), '--authorization', str(args.authorization), '--vectors', str(vecdir),
                   '--worker', '--mode', mode]
        env = {k: v for k, v in os.environ.items() if k not in RUNTIME_ENV}
        env.update(extra_env, CORE_RUNTIME_CHILD_TOKEN=child_token)
        t0 = time.monotonic()
        # Only this child process group may be stopped on its deadline.
        with (mode_out / 'worker.log').open('xb') as log:
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True, env=env)
            try:
                code = child.wait(timeout=limit)
                status = 'EXITED'
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    code = child.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL); code = child.wait()
                status = 'BUDGET_LIMIT'
                save(mode_out / 'BUDGET_LIMIT.json', {'status': 'BUDGET_LIMIT', 'child_exit_code': code})
        save(mode_out / 'PROCESS_EXITED.json', {'child_exit_code': code, 'status': status, 'elapsed_seconds': time.monotonic() - t0})
        summary.append({'mode': mode, 'status': status, 'exit_code': code, 'elapsed_seconds': round(time.monotonic() - t0, 1)})
        save(args.out / 'SUMMARY.json', summary)
    save(args.out / 'SUMMARY.json', summary)
    save(args.out / 'VECTOR_FILES.json', {p.name: sha(p) for p in sorted(vecdir.glob('*.safetensors'))})
    archive = args.out.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as z:
        for path in sorted(args.out.rglob('*')):
            if path.is_file() and path.suffix != '.safetensors':
                z.write(path, path.relative_to(args.out))
    with zipfile.ZipFile(archive) as z:
        bad = z.testzip()
    save(args.out.with_suffix('.archive.json'), {'archive': str(archive), 'sha256': sha(archive), 'bad_zip_member': bad,
                                               'summary': summary, 'pod_stop_performed': False, 'backup_local_verified': False})
    (args.out.parent / 'DONE').write_text(json.dumps({'summary': summary, 'archive_sha256': sha(archive)}), encoding='utf-8')


if __name__ == '__main__':
    main()
