"""Restricted Python executor for the CORE tool evaluation (Opus 5.5, 29/09/2026). Deterministic, no LLM.

The model's code is (1) parsed and checked against an AST whitelist, then (2) run in a separate interpreter (COMMAND:
no site-packages or user site, no bytecode, working directory kept out of sys.path, UTF-8 mode) with a replaced
environment (PYTHONHASHSEED=0 for reproducible set order), a fresh temporary directory, a wall-clock timeout, builtins
without file/eval/introspection access and an import hook limited to ALLOWED_MODULES.
On Linux the child also gets CPU/memory/file-size limits and drops to uid/gid 65534 when started as root.
Threat model: a non-adversarial 4B model making mistakes, not a determined attacker; every program is logged.
Import-safe: nothing runs at import."""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile

ALLOWED_MODULES = ('math', 'decimal', 'fractions', 'datetime', 'calendar', 're', 'json', 'itertools', 'collections',
                   'statistics', 'string', 'unicodedata')
FORBIDDEN_NAMES = ('open', 'exec', 'eval', 'compile', '__import__', 'input', 'breakpoint', 'globals', 'locals', 'vars',
                   'getattr', 'setattr', 'delattr', 'hasattr', 'dir', 'help', 'exit', 'quit', 'memoryview', 'copyright',
                   'credits', 'license', '__build_class__', '__loader__', '__spec__', '__builtins__')
FORBIDDEN_NODES = (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith, ast.Await)
# Imported lazily by C code called from the program's frame (datetime.strptime, date.strftime); never importable by the
# program itself (the AST check refuses any module outside ALLOWED_MODULES).
INTERNAL_LAZY = ('_strptime', 'time')
MAX_CODE_CHARS = 8000
MAX_OUTPUT_CHARS = 2000
TIMEOUT_SECONDS = 10
CPU_SECONDS = 5
MEMORY_BYTES = 1 << 30

RUNNER = r'''
import builtins, json, sys, traceback
sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")
job = json.loads(sys.stdin.read())
allowed = set(job["allowed"]); forbidden = set(job["forbidden"]); lazy = set(job["lazy"])
real_import = builtins.__import__
def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level != 0 or (name.split(".")[0] not in allowed and name not in lazy):
        raise ImportError("module non autorisé : " + str(name))
    return real_import(name, globals, locals, fromlist, level)
safe = {k: v for k, v in vars(builtins).items() if k not in forbidden and not k.startswith("_")}
safe["__import__"] = guarded_import
safe["__build_class__"] = builtins.__build_class__
scope = {"__builtins__": safe, "__name__": "__main__"}
try:
    exec(compile(job["code"], "<outil>", "exec"), scope)
except BaseException as exc:
    sys.stdout.flush()
    sys.stderr.write("\nCORE_TOOL_ERROR " + traceback.format_exception_only(type(exc), exc)[-1].strip())
    sys.exit(1)
'''


def check(code):
    """Return None if the program is acceptable, else a short French reason."""
    if not isinstance(code, str) or not code.strip():
        return 'programme vide'
    if len(code) > MAX_CODE_CHARS:
        return f'programme trop long ({len(code)} caractères, maximum {MAX_CODE_CHARS})'
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return f'SyntaxError: {exc.msg} (ligne {exc.lineno})'
    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES):
            return 'code asynchrone non autorisé'
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom) and (node.level or not node.module):
                return 'import relatif non autorisé'
            names = [node.module] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names]
            for name in names:
                if name.split('.')[0] not in ALLOWED_MODULES:
                    return f'module non autorisé : {name}'
        if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
            return f'attribut non autorisé : {node.attr}'
        if isinstance(node, ast.Name) and (node.id in FORBIDDEN_NAMES or node.id.startswith('__')):
            return f'nom non autorisé : {node.id}'
        if isinstance(node, ast.alias) and (node.asname or node.name).startswith('__'):
            return f'nom non autorisé : {node.asname or node.name}'
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and '__' in node.value:
            return 'chaîne contenant « __ » non autorisée'
    return None


# Not -I: isolated mode would ignore PYTHONHASHSEED (set iteration order must be reproducible). -S -s -P keep site-packages,
# user site and the working directory out of sys.path; the environment is replaced entirely by child_env().
COMMAND = [sys.executable, '-S', '-s', '-B', '-P', '-X', 'utf8', '-c']


def child_env():
    env = {'PYTHONHASHSEED': '0', 'PYTHONUTF8': '1'}
    if os.name == 'nt':
        env['SYSTEMROOT'] = os.environ.get('SYSTEMROOT', 'C:\\Windows')
    return env


def _linux_limits():
    import resource
    os.setsid()
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS, CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_BYTES, MEMORY_BYTES))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    if os.getuid() == 0:
        os.setgroups([])
        os.setgid(65534)
        os.setuid(65534)


def execute(code):
    """Run one program. Returns a dict with the text sent back to the model and the evidence kept in the logs."""
    reason = check(code)
    if reason is not None:
        return {'status': 'REFUSED', 'text': f'Erreur : code refusé ({reason}).', 'stdout': '', 'error': reason}
    job = json.dumps({'code': code, 'allowed': list(ALLOWED_MODULES), 'forbidden': list(FORBIDDEN_NAMES),
                      'lazy': list(INTERNAL_LAZY)})
    with tempfile.TemporaryDirectory(prefix='core_tool_') as tmp:
        kwargs = dict(input=job.encode('ascii'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=tmp, env=child_env(),
                      timeout=TIMEOUT_SECONDS)
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        else:
            kwargs['preexec_fn'] = _linux_limits
        try:
            done = subprocess.run(COMMAND + [RUNNER], **kwargs)
        except subprocess.TimeoutExpired:
            return {'status': 'TIMEOUT', 'text': f'Erreur : délai dépassé ({TIMEOUT_SECONDS} s).', 'stdout': '',
                    'error': 'timeout'}
    out = done.stdout.decode('utf-8', 'replace').replace('\r\n', '\n').rstrip()
    err = done.stderr.decode('utf-8', 'replace').replace('\r\n', '\n')
    clipped = out if len(out) <= MAX_OUTPUT_CHARS else out[:MAX_OUTPUT_CHARS] + '\n[sortie tronquée]'
    if done.returncode != 0:
        marker = err.rsplit('CORE_TOOL_ERROR ', 1)
        error = marker[1].strip() if len(marker) == 2 else (err.strip().splitlines() or ['arrêt anormal'])[-1]
        text = (clipped + '\n' if clipped else '') + f'Erreur : {error}'
        return {'status': 'ERROR', 'text': text, 'stdout': out, 'error': error, 'returncode': done.returncode}
    if not out:
        return {'status': 'NO_OUTPUT', 'text': '(aucune sortie : affiche le résultat avec print)', 'stdout': '',
                'error': None}
    return {'status': 'OK', 'text': clipped, 'stdout': out, 'error': None}


def isolation_facts():
    """Evidence of the hardening actually applied in the child (checked before any campaign)."""
    probe = execute('import json\nprint(json.dumps(["Î", sorted(set("abc")), list({"x", "y", "z"})]))')
    again = execute('import json\nprint(json.dumps(["Î", sorted(set("abc")), list({"x", "y", "z"})]))')
    facts = {'platform': sys.platform, 'python': sys.executable, 'command': COMMAND, 'probe': probe['text'],
             'probe_status': probe['status'], 'utf8_round_trip': probe['stdout'].startswith('["Î"') or
             probe['stdout'].startswith('["\\u00ce"'), 'deterministic_set_order': probe['stdout'] == again['stdout']}
    if os.name != 'nt':
        code = COMMAND + ['import os, sys, resource, json; print(json.dumps({"uid": os.getuid(), "gid": os.getgid(), '
                          '"cpu": resource.getrlimit(resource.RLIMIT_CPU), "as": resource.getrlimit(resource.RLIMIT_AS), '
                          '"fsize": resource.getrlimit(resource.RLIMIT_FSIZE), "env": sorted(os.environ), '
                          '"path": sys.path}))']
        with tempfile.TemporaryDirectory(prefix='core_tool_') as tmp:
            done = subprocess.run(code, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=tmp, env=child_env(),
                                  timeout=TIMEOUT_SECONDS, preexec_fn=_linux_limits)
        facts['child'] = json.loads(done.stdout.decode('utf-8'))
    return facts
