"""Tool declaration, Qwen3.5 tool-call parsing and the bounded tool loop (Opus 5.5, 29/09/2026). Pure Python: no
torch, no model; the generator is injected so the loop is tested on CPU with a scripted model. Import-safe.

Loop (arm `outil`): render [system, user] with tools=TOOLS through the chat template, generate greedily; if the turn
contains tool calls, execute each one in the sandbox, append the assistant turn (content before the first call + the
parsed calls) and one `tool` message per call, re-render with the template and generate again. At most MAX_TOOL_ROUNDS
rounds of calls; the final answer is the text of the first turn without a call. A malformed call (markup present but
unparsable) is NOT executed: that turn is the final answer and is flagged. Accepted formats (pre-registered): the
documented XML format of the Qwen3.5 template, and the legacy JSON format {"name": ..., "arguments": {...}}."""
from __future__ import annotations

import json
import re

SYSTEM = ("Tu es Core, un assistant professionnel fiable. Réponds uniquement à partir des informations fournies, respecte "
          "strictement les instructions et n'invente aucune information.")
TOOL_NAME = 'executer_python'
TOOLS = [{'type': 'function', 'function': {
    'name': TOOL_NAME,
    'description': (
        "Exécute un court programme Python 3 et renvoie exactement ce qu'il affiche avec print(). À utiliser pour tout "
        "calcul exact : montants, taxes, remises, pourcentages et arrondis (decimal.Decimal construit à partir de chaînes ; "
        "arrondi moitié vers le haut : quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)), dates, jours de la semaine, jours "
        "ouvrés et durées (module datetime), transformations exactes de listes ou de texte (casse, masquage, filtrage, "
        "dédoublonnage, tri, jointure). L'outil ne voit pas la conversation : recopie dans le code les données utiles. "
        "Modules autorisés : math, decimal, fractions, datetime, calendar, re, json, itertools, collections, statistics, "
        "string, unicodedata ; ni fichiers ni réseau. Après le résultat, donne la réponse finale dans le format exact "
        "demandé, sans mentionner l'outil."),
    'parameters': {'type': 'object',
                   'properties': {'code': {'type': 'string',
                                           'description': 'Programme Python complet qui affiche le résultat avec print().'}},
                   'required': ['code']}}}]
MAX_TOOL_ROUNDS = 3
XML_CALL = re.compile(r'<tool_call>\s*<function=([^>\n]+)>(.*?)</function>\s*</tool_call>', re.S)
XML_PARAM = re.compile(r'<parameter=([^>\n]+)>\n?(.*?)\n?</parameter>', re.S)
JSON_CALL = re.compile(r'<tool_call>\s*(\{.*?\})\s*</tool_call>', re.S)
THINK = re.compile(r'<think>.*?</think>', re.S)
MARKUP = ('<tool_call>', '</tool_call>', '<function=', '<parameter=', '<tool_response>', '</tool_response>')


def user_content(row):
    return 'INSTRUCTION:\n' + row['instruction'].strip() + '\n\nCONTEXTE:\n' + row['contexte'].strip()


def base_messages(row):
    return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': user_content(row)}]


def clean(text):
    return THINK.sub('', text).strip()


def parse(text):
    """-> (content before the first call, [{'name', 'arguments'}], format in {'none', 'xml', 'json', 'malformed'})."""
    if '<tool_call>' not in text:
        return clean(text), [], 'none'
    content = clean(text[:text.index('<tool_call>')])
    calls = []
    for name, body in XML_CALL.findall(text):
        calls.append({'name': name.strip(), 'arguments': {k.strip(): v for k, v in XML_PARAM.findall(body)}})
    if calls:
        return content, calls, 'xml'
    for blob in JSON_CALL.findall(text):
        try:
            obj = json.loads(blob)
        except json.JSONDecodeError:
            continue
        args = obj.get('arguments') if isinstance(obj, dict) else None
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = None
        if isinstance(obj, dict) and isinstance(obj.get('name'), str) and isinstance(args, dict):
            calls.append({'name': obj['name'].strip(), 'arguments': args})
    if calls:
        return content, calls, 'json'
    return clean(text), [], 'malformed'


def run_tool(call, execute):
    if call['name'] != TOOL_NAME:
        return {'status': 'UNKNOWN_FUNCTION', 'text': f"Erreur : fonction inconnue « {call['name']} » ; seule {TOOL_NAME} "
                                                      "existe.", 'stdout': '', 'error': 'unknown_function'}
    code = call['arguments'].get('code')
    if not isinstance(code, str):
        return {'status': 'BAD_ARGUMENTS', 'text': 'Erreur : paramètre « code » manquant.', 'stdout': '',
                'error': 'missing_code'}
    return execute(code)


def tool_loop(row, generate, execute, max_rounds=MAX_TOOL_ROUNDS):
    """generate(messages, tools) -> dict(text=..., **evidence); execute(code) -> sandbox result.
    Returns the final answer (None if the model still calls a tool after max_rounds) and the full trace."""
    messages = base_messages(row)
    turns = []
    for round_index in range(max_rounds + 1):
        gen = generate(messages, TOOLS)
        content, calls, fmt = parse(gen['text'])
        turn = {'round': round_index, 'format': fmt, 'content': content, 'calls': calls, 'generation': gen, 'results': []}
        turns.append(turn)
        if not calls:
            return {'final': content, 'final_status': 'MALFORMED_CALL' if fmt == 'malformed' else 'ANSWERED',
                    'turns': turns, 'tool_rounds': round_index}
        if round_index == max_rounds:
            break
        messages = messages + [{'role': 'assistant', 'content': content,
                                'tool_calls': [{'type': 'function', 'function': c} for c in calls]}]
        for call in calls:
            result = run_tool(call, execute)
            turn['results'].append(result)
            messages = messages + [{'role': 'tool', 'content': result['text']}]
    return {'final': None, 'final_status': 'ROUND_LIMIT', 'turns': turns, 'tool_rounds': max_rounds}


def leaked_markup(text):
    return text is not None and any(m in text for m in MARKUP)
