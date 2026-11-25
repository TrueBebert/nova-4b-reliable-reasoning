"""TOOLCALC R2 integration fixes (Opus 5.5, 29/09/2026), on top of the unchanged R1 modules (toolcall, sandbox).
Pure Python, import-safe. Three changes agreed with the user after R1, nothing else:
  1. retry guard: a call whose code is identical (after strip) to code already submitted in the same case is not run;
     the loop stops (RETRY_STOPPED);
  2. escaped-quote repair: code refused for a SyntaxError that contains \\" or \\' is retried once with those escapes
     removed, and only if the repaired code passes the same AST check; the repair is recorded;
  3. fallback: when the tool path gives no usable answer (round limit, malformed call, retry stopped, prompt too long,
     empty answer, tool markup in the answer), the system returns the production answer (direct arm, same prompt).
Routing (whether the tool is offered at all) is in router.py; the tool declaration and the loop bound are R1's."""
from __future__ import annotations

import toolcall
import sandbox


def run_tool(call, execute):
    if call['name'] != toolcall.TOOL_NAME or not isinstance(call['arguments'].get('code'), str):
        return toolcall.run_tool(call, execute)
    code = call['arguments']['code']
    reason = sandbox.check(code)
    if reason is not None and reason.startswith('SyntaxError') and ('\\"' in code or "\\'" in code):
        repaired = code.replace('\\"', '"').replace("\\'", "'")
        if sandbox.check(repaired) is None:
            result = dict(execute(repaired))
            result['repaired_escaped_quotes'] = True
            return result
    return execute(code)


def tool_loop(row, generate, execute, max_rounds=toolcall.MAX_TOOL_ROUNDS):
    messages = toolcall.base_messages(row)
    turns, seen = [], set()
    for round_index in range(max_rounds + 1):
        gen = generate(messages, toolcall.TOOLS)
        content, calls, fmt = toolcall.parse(gen['text'])
        turn = {'round': round_index, 'format': fmt, 'content': content, 'calls': calls, 'generation': gen, 'results': []}
        turns.append(turn)
        if not calls:
            return {'final': content, 'final_status': 'MALFORMED_CALL' if fmt == 'malformed' else 'ANSWERED',
                    'turns': turns, 'tool_rounds': round_index}
        if round_index == max_rounds:
            break
        codes = [c['arguments'].get('code').strip() for c in calls if isinstance(c['arguments'].get('code'), str)]
        if any(code in seen for code in codes):
            return {'final': None, 'final_status': 'RETRY_STOPPED', 'turns': turns, 'tool_rounds': round_index}
        seen.update(codes)
        messages = messages + [{'role': 'assistant', 'content': content,
                                'tool_calls': [{'type': 'function', 'function': c} for c in calls]}]
        for call in calls:
            result = run_tool(call, execute)
            turn['results'].append(result)
            messages = messages + [{'role': 'tool', 'content': result['text']}]
    return {'final': None, 'final_status': 'ROUND_LIMIT', 'turns': turns, 'tool_rounds': max_rounds}


def system_answer(trace, direct_final):
    """-> (final answer of the R2 system for a routed request, whether the fallback was used)."""
    final = trace.get('final')
    if trace['final_status'] != 'ANSWERED' or final is None or not final.strip() or toolcall.leaked_markup(final):
        return direct_final, True
    return final, False
